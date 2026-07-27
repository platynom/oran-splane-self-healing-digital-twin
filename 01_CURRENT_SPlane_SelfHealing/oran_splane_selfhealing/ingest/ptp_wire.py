from __future__ import annotations

"""Minimal, dependency-free PTP-over-Ethernet (IEEE-1588 Annex F, Ethertype
0x88F7) wire codec plus a tiny libpcap reader/writer.

This is deliberately self-contained (no scapy) so the ingestion path has no heavy
runtime dependency and the parser is auditable. It supports exactly the message
types the S-plane self-healing pipeline needs: Sync, Follow_Up, Delay_Req,
Delay_Resp, Announce.
"""

import struct
from dataclasses import dataclass

ETHERTYPE_PTP = 0x88F7

# messageType (low nibble of byte 0)
MT_SYNC = 0x0
MT_DELAY_REQ = 0x1
MT_FOLLOW_UP = 0x8
MT_DELAY_RESP = 0x9
MT_ANNOUNCE = 0xB
MSG_NAME = {
    MT_SYNC: "Sync",
    MT_DELAY_REQ: "Delay_Req",
    MT_FOLLOW_UP: "Follow_Up",
    MT_DELAY_RESP: "Delay_Resp",
    MT_ANNOUNCE: "Announce",
}
NAME_MSG = {v: k for k, v in MSG_NAME.items()}

_PTP_HEADER_LEN = 34
_TS_LEN = 10  # 6 bytes seconds + 4 bytes nanoseconds


@dataclass
class PtpMessage:
    msg_type: int
    seq_id: int
    correction_ns: float
    origin_ts_ns: int | None  # payload timestamp if the message carries one
    current_utc_offset: int | None = None
    grandmaster_priority1: int | None = None
    grandmaster_clock_class: int | None = None
    grandmaster_clock_accuracy: int | None = None
    offset_scaled_log_variance: int | None = None
    grandmaster_priority2: int | None = None
    grandmaster_identity: bytes | None = None
    steps_removed: int | None = None
    time_source: int | None = None


def encode_timestamp(ts_ns: int) -> bytes:
    seconds = ts_ns // 1_000_000_000
    nanos = ts_ns % 1_000_000_000
    return seconds.to_bytes(6, "big") + struct.pack(">I", nanos)


def decode_timestamp(raw: bytes) -> int:
    seconds = int.from_bytes(raw[:6], "big")
    nanos = struct.unpack(">I", raw[6:10])[0]
    return seconds * 1_000_000_000 + nanos


def build_ptp_payload(msg_type: int, seq_id: int, origin_ts_ns: int | None = None,
                      correction_ns: float = 0.0, domain: int = 24) -> bytes:
    b0 = msg_type & 0x0F  # transportSpecific=0
    b1 = 0x02             # versionPTP=2
    has_ts = msg_type in (MT_SYNC, MT_FOLLOW_UP, MT_DELAY_REQ, MT_DELAY_RESP)
    body_len = _PTP_HEADER_LEN + (_TS_LEN if has_ts else 0)
    correction_subns = int(round(correction_ns * (1 << 16)))  # scaled ns
    header = bytearray(_PTP_HEADER_LEN)
    header[0] = b0
    header[1] = b1
    struct.pack_into(">H", header, 2, body_len)
    header[4] = domain
    struct.pack_into(">q", header, 8, correction_subns)
    struct.pack_into(">H", header, 30, seq_id & 0xFFFF)
    header[32] = 0x00
    header[33] = 0x00
    payload = bytes(header)
    if has_ts:
        payload += encode_timestamp(origin_ts_ns or 0)
    return payload


def decode_ptp_payload(payload: bytes) -> PtpMessage | None:
    if len(payload) < _PTP_HEADER_LEN:
        return None
    if (payload[1] & 0x0F) != 0x02:  # versionPTP must be 2
        return None
    msg_type = payload[0] & 0x0F
    if msg_type not in MSG_NAME:
        return None
    seq_id = struct.unpack_from(">H", payload, 30)[0]
    correction_subns = struct.unpack_from(">q", payload, 8)[0]
    correction_ns = correction_subns / (1 << 16)
    origin_ts_ns = None
    if msg_type in (MT_SYNC, MT_FOLLOW_UP, MT_DELAY_REQ, MT_DELAY_RESP) and len(payload) >= _PTP_HEADER_LEN + _TS_LEN:
        origin_ts_ns = decode_timestamp(payload[_PTP_HEADER_LEN:_PTP_HEADER_LEN + _TS_LEN])
    if msg_type == MT_ANNOUNCE and len(payload) >= 64:
        return PtpMessage(
            msg_type=msg_type,
            seq_id=seq_id,
            correction_ns=correction_ns,
            origin_ts_ns=decode_timestamp(payload[34:44]),
            current_utc_offset=struct.unpack_from(">h", payload, 44)[0],
            grandmaster_priority1=payload[47],
            grandmaster_clock_class=payload[48],
            grandmaster_clock_accuracy=payload[49],
            offset_scaled_log_variance=struct.unpack_from(">H", payload, 50)[0],
            grandmaster_priority2=payload[52],
            grandmaster_identity=payload[53:61],
            steps_removed=struct.unpack_from(">H", payload, 61)[0],
            time_source=payload[63],
        )
    return PtpMessage(msg_type, seq_id, correction_ns, origin_ts_ns)


def build_eth_frame(dst_mac: bytes, src_mac: bytes, payload: bytes) -> bytes:
    return dst_mac + src_mac + struct.pack(">H", ETHERTYPE_PTP) + payload


def parse_eth_frame(frame: bytes) -> bytes | None:
    if len(frame) < 14:
        return None
    ethertype = struct.unpack_from(">H", frame, 12)[0]
    if ethertype != ETHERTYPE_PTP:
        return None
    return frame[14:]


# ---- tiny libpcap (classic) reader/writer, NANOSECOND precision ----
# Nanosecond resolution is mandatory here: S-plane offsets are tens of ns, so a
# microsecond-resolution pcap would quantize the signal away. We use the pcap
# nanosecond magic (0xA1B23C4D); the reader below auto-detects it.
_PCAP_MAGIC = 0xA1B2C3D4       # classic microsecond magic (reader still accepts)
_PCAP_MAGIC_NS = 0xA1B23C4D    # nanosecond magic (what we WRITE)
_LINKTYPE_ETHERNET = 1


class PcapWriter:
    def __init__(self, path: str):
        self._f = open(path, "wb")
        self._f.write(struct.pack("<IHHiIII", _PCAP_MAGIC_NS, 2, 4, 0, 0, 65535, _LINKTYPE_ETHERNET))

    def write(self, ts_ns: int, frame: bytes) -> None:
        """ts_ns is INTEGER nanoseconds since epoch (floats lose ns precision at
        epoch scale, so we never route timestamps through a float second)."""
        ts_ns = int(ts_ns)
        sec, nsec = divmod(ts_ns, 1_000_000_000)
        self._f.write(struct.pack("<IIII", sec, nsec, len(frame), len(frame)))
        self._f.write(frame)

    def close(self) -> None:
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def read_pcap(path: str):
    """Yield (capture_ts_nanoseconds:int, frame_bytes) for each record.

    Integer ns is returned (not float seconds) to preserve sub-microsecond
    precision, which the S-plane offset math depends on.
    """
    with open(path, "rb") as f:
        global_header = f.read(24)
        if len(global_header) < 24:
            return
        magic = struct.unpack_from("<I", global_header, 0)[0]
        endian = "<" if magic in (_PCAP_MAGIC, _PCAP_MAGIC_NS) else ">"
        if magic not in (_PCAP_MAGIC, 0xD4C3B2A1, _PCAP_MAGIC_NS, 0x4D3CB2A1):
            raise ValueError("not a classic pcap file")
        nano = magic in (_PCAP_MAGIC_NS, 0x4D3CB2A1)
        while True:
            rec = f.read(16)
            if len(rec) < 16:
                break
            ts_sec, ts_frac, incl_len, _orig = struct.unpack(endian + "IIII", rec)
            data = f.read(incl_len)
            if len(data) < incl_len:
                break
            ts_ns = ts_sec * 1_000_000_000 + (ts_frac if nano else ts_frac * 1000)
            yield ts_ns, data
