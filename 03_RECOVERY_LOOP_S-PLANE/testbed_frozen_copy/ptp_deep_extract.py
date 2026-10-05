#!/usr/bin/env python3
"""
G.8275.1-aware deep PTP extractor.

Parses the FULL IEEE 1588-2019 surface that is genuinely present on the wire.

INTEGRITY CONTRACT (non-negotiable):
  * Every emitted column is parsed from actual bytes.
  * A field that is not present/derivable is emitted as EMPTY (NaN), never as a
    placeholder constant. Placeholder constants are what made the previous
    derived datasets unusable.
  * Fields that cannot be recovered from a PASSIVE capture (the slave's own t2/t3)
    are NOT emitted at all, rather than approximated silently.

Field offsets: IEEE 1588-2019 clause 13 (common header) and clause 13.5 (Announce).
Profile constants checked against ITU-T G.8275.1.
"""
from __future__ import annotations
import struct, csv, os, sys, collections

ETH_PTP = 0x88F7
MSG = {0:"Sync",1:"Delay_Req",2:"Pdelay_Req",3:"Pdelay_Resp",8:"Follow_Up",
       9:"Delay_Resp",0xA:"Pdelay_Resp_Follow_Up",0xB:"Announce",0xC:"Signaling",0xD:"Management"}

# ---- G.8275.1 profile expectations (ITU-T G.8275.1) ----
G87251 = dict(domain_default=24, domain_lo=24, domain_hi=43,
              log_sync=-4, log_announce=-3, log_delayreq=-4,
              priority1=128,
              mcast_forwardable="011b19000000", mcast_linklocal="0180c200000e")

def _ts48(b):
    """PTP Timestamp: 48-bit seconds + 32-bit nanoseconds -> integer ns."""
    if len(b) < 10: return None
    sec = int.from_bytes(b[0:6], "big"); ns = int.from_bytes(b[6:10], "big")
    return sec * 1_000_000_000 + ns

def parse_pcap(path):
    """Yield (capture_ts_ns, frame_bytes). Supports classic pcap (LINKTYPE_ETHERNET)."""
    with open(path, "rb") as f:
        gh = f.read(24)
        if len(gh) < 24: return
        magic = struct.unpack("<I", gh[:4])[0]
        if magic in (0xa1b2c3d4, 0xa1b23c4d): endian, nano = "<", magic == 0xa1b23c4d
        elif magic in (0xd4c3b2a1, 0x4d3cb2a1): endian, nano = ">", magic == 0x4d3cb2a1
        else: raise ValueError(f"not a classic pcap: {hex(magic)}")
        linktype = struct.unpack(endian + "I", gh[20:24])[0]
        if linktype != 1: raise ValueError(f"unsupported linktype {linktype}")
        while True:
            ph = f.read(16)
            if len(ph) < 16: break
            ts, frac, cap, orig = struct.unpack(endian + "IIII", ph)
            data = f.read(cap)
            if len(data) < cap: break
            yield ts * 1_000_000_000 + (frac if nano else frac * 1000), data

def parse_frame(ts_ns, pkt):
    """Return a fully-parsed record, or None if not PTP-over-Ethernet."""
    if len(pkt) < 14: return None
    dst = pkt[0:6].hex(); src = pkt[6:12].hex()
    et = struct.unpack(">H", pkt[12:14])[0]; off = 14; vlan_id = None; vlan_pcp = None
    if et == 0x8100:                                    # 802.1Q VLAN
        tci = struct.unpack(">H", pkt[14:16])[0]
        vlan_pcp = (tci >> 13) & 0x7; vlan_id = tci & 0x0FFF
        et = struct.unpack(">H", pkt[16:18])[0]; off = 18
    if et != ETH_PTP: return None
    p = pkt[off:]
    if len(p) < 34: return None

    # ---- L0: common header (IEEE 1588-2019 cl.13.3) ----
    major_sdo = (p[0] >> 4) & 0x0F
    mtype     = p[0] & 0x0F
    minor_ver = (p[1] >> 4) & 0x0F
    version   = p[1] & 0x0F
    mlen      = struct.unpack(">H", p[2:4])[0]
    domain    = p[4]
    minor_sdo = p[5]
    flags     = struct.unpack(">H", p[6:8])[0]
    corr_raw  = struct.unpack(">q", p[8:16])[0]         # scaled ns, 2^-16
    clk_id    = p[20:28].hex()
    port_num  = struct.unpack(">H", p[28:30])[0]
    seq       = struct.unpack(">H", p[30:32])[0]
    ctrl      = p[32]
    log_int   = struct.unpack(">b", p[33:34])[0]

    f0, f1 = (flags >> 8) & 0xFF, flags & 0xFF          # octet0, octet1
    r = dict(
        capture_ts_ns=ts_ns, eth_dst=dst, eth_src=src, vlan_id=vlan_id, vlan_pcp=vlan_pcp,
        message_type=MSG.get(mtype, f"type{mtype}"), message_type_raw=mtype,
        version_ptp=version, minor_version_ptp=minor_ver, message_length=mlen,
        domain_number=domain, major_sdo_id=major_sdo, minor_sdo_id=minor_sdo,
        flag_field_hex=f"0x{flags:04x}",
        flag_alternateMaster=int(bool(f0 & 0x01)), flag_twoStep=int(bool(f0 & 0x02)),
        flag_unicast=int(bool(f0 & 0x04)),
        flag_profileSpecific1=int(bool(f0 & 0x20)), flag_profileSpecific2=int(bool(f0 & 0x40)),
        flag_leap61=int(bool(f1 & 0x01)), flag_leap59=int(bool(f1 & 0x02)),
        flag_currentUtcOffsetValid=int(bool(f1 & 0x04)), flag_ptpTimescale=int(bool(f1 & 0x08)),
        flag_timeTraceable=int(bool(f1 & 0x10)), flag_frequencyTraceable=int(bool(f1 & 0x20)),
        flag_syncUncertain=int(bool(f1 & 0x40)),
        correction_ns=corr_raw / 65536.0,
        source_clock_identity=clk_id, source_port_number=port_num,
        sequence_id=seq, control_field=ctrl, log_message_interval=log_int,
        # --- profile legality (G.8275.1), computed, not assumed ---
        g87251_domain_ok=int(G87251["domain_lo"] <= domain <= G87251["domain_hi"]),
        g87251_mcast_ok=int(dst in (G87251["mcast_forwardable"], G87251["mcast_linklocal"])),
    )

    body = p[34:]
    # ---- L1/L2: Announce body (cl.13.5) ----
    if mtype == 0x0B and len(body) >= 30:
        r.update(
            origin_ts_ns=_ts48(body[0:10]),
            current_utc_offset=struct.unpack(">h", body[10:12])[0],
            gm_priority1=body[13],
            gm_clock_class=body[14], gm_clock_accuracy=body[15],
            gm_offset_scaled_log_variance=struct.unpack(">H", body[16:18])[0],
            gm_priority2=body[18],
            gm_clock_identity=body[19:27].hex(),
            steps_removed=struct.unpack(">H", body[27:29])[0],
            time_source=body[29],
        )
        r["g87251_priority1_ok"] = int(body[13] == G87251["priority1"])
        r["clock_class_legal"] = int(body[14] >= 6)          # 0-5 reserved, IEEE 1588 Table 5
        r["bmca_fields_all_zero"] = int(body[13] == 0 and body[14] == 0 and body[18] == 0)
        r["gm_identity_equals_source"] = int(body[19:27].hex() == clk_id)
        r["g87251_log_announce_ok"] = int(log_int == G87251["log_announce"])
        # TLVs (PATH_TRACE = 0x0008)
        tlvs, i, has_pt, pt_len = [], 30, 0, None
        while i + 4 <= len(body):
            t = struct.unpack(">H", body[i:i+2])[0]; ln = struct.unpack(">H", body[i+2:i+4])[0]
            tlvs.append(f"0x{t:04x}")
            if t == 0x0008:
                has_pt = 1; pt_len = ln // 8
            i += 4 + ln
            if ln == 0: break
        r["tlv_types"] = ";".join(tlvs) if tlvs else ""
        r["has_path_trace"] = has_pt
        r["path_trace_hops"] = pt_len
    elif mtype in (0x00, 0x08, 0x09) and len(body) >= 10:
        # Sync(originTimestamp) / Follow_Up(preciseOriginTimestamp) / Delay_Resp(receiveTimestamp)
        r["origin_ts_ns"] = _ts48(body[0:10])
        if mtype == 0x09 and len(body) >= 20:
            r["requesting_clock_identity"] = body[10:18].hex()
            r["requesting_port_number"] = struct.unpack(">H", body[18:20])[0]
        if mtype == 0x00:
            r["g87251_log_sync_ok"] = int(log_int == G87251["log_sync"])
    elif mtype == 0x01 and len(body) >= 10:
        r["origin_ts_ns"] = _ts48(body[0:10])
        # 0x7F (127) = "unspecified", the correct value for multicast Delay_Req per
        # IEEE 1588 cl.13.3.2.14. Treat it as compliant, not a violation.
        r["g87251_log_delayreq_ok"] = int(log_int in (G87251["log_delayreq"], 127))
    return r

COLUMNS = ["capture_ts_ns","eth_src","eth_dst","vlan_id","vlan_pcp","message_type","message_type_raw",
"version_ptp","minor_version_ptp","message_length","domain_number","major_sdo_id","minor_sdo_id",
"flag_field_hex","flag_alternateMaster","flag_twoStep","flag_unicast","flag_profileSpecific1",
"flag_profileSpecific2","flag_leap61","flag_leap59","flag_currentUtcOffsetValid","flag_ptpTimescale",
"flag_timeTraceable","flag_frequencyTraceable","flag_syncUncertain","correction_ns",
"source_clock_identity","source_port_number","sequence_id","control_field","log_message_interval",
"origin_ts_ns","current_utc_offset","gm_priority1","gm_clock_class","gm_clock_accuracy",
"gm_offset_scaled_log_variance","gm_priority2","gm_clock_identity","steps_removed","time_source",
"tlv_types","has_path_trace","path_trace_hops","requesting_clock_identity","requesting_port_number",
"clock_class_legal","bmca_fields_all_zero","gm_identity_equals_source",
"g87251_domain_ok","g87251_mcast_ok","g87251_priority1_ok","g87251_log_sync_ok",
"g87251_log_announce_ok","g87251_log_delayreq_ok"]

def extract(pcap_path, out_csv):
    n_frames = n_ptp = 0
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for ts, pkt in parse_pcap(pcap_path):
            n_frames += 1
            rec = parse_frame(ts, pkt)
            if rec is None: continue
            n_ptp += 1
            w.writerow(rec)          # absent keys -> EMPTY, never a constant
    return n_frames, n_ptp

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    a, b = extract(src, dst)
    print(f"{os.path.basename(src)}: frames={a} ptp={b} -> {dst}")
