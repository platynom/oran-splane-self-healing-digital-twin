#!/usr/bin/env python3
"""Audit PTP Announce stepsRemoved values in the frozen recovery archive.

This deliberately uses only the Python standard library so the result is
reproducible without tshark/scapy.  It reads, but never extracts or modifies,
the archive.  Ethernet PTP frames use EtherType 0x88f7; in an IEEE 1588-2008
Announce message the two-byte stepsRemoved field starts at byte 61 of the PTP
message.
"""

from __future__ import annotations

import collections
import gzip
import io
import json
import struct
import sys
import tarfile
from pathlib import Path


def pcap_packets(raw: bytes):
    stream = io.BytesIO(raw)
    header = stream.read(24)
    if len(header) != 24:
        return
    magic = header[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        endian = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        endian = ">"
    else:
        raise ValueError(f"unsupported pcap magic {magic.hex()}")
    while True:
        packet_header = stream.read(16)
        if not packet_header:
            return
        if len(packet_header) != 16:
            raise ValueError("truncated pcap packet header")
        _sec, _frac, captured, _wire = struct.unpack(endian + "IIII", packet_header)
        packet = stream.read(captured)
        if len(packet) != captured:
            raise ValueError("truncated pcap packet")
        yield packet


def announce(packet: bytes):
    if len(packet) < 14:
        return None
    ethertype = struct.unpack(">H", packet[12:14])[0]
    offset = 14
    if ethertype == 0x8100 and len(packet) >= 18:
        ethertype = struct.unpack(">H", packet[16:18])[0]
        offset = 18
    if ethertype != 0x88F7 or len(packet) < offset + 63:
        return None
    ptp = packet[offset:]
    if ptp[0] & 0x0F != 11:
        return None
    return {
        "source_mac": packet[6:12].hex(),
        "source_clock_identity": ptp[20:28].hex(),
        "grandmaster_identity": ptp[53:61].hex(),
        "steps_removed": struct.unpack(">H", ptp[61:63])[0],
    }


def main() -> int:
    archive = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "03_RECOVERY_LOOP_S-PLANE/results/recovery_eval_runs_r13-r17.tgz"
    )
    counts = collections.Counter()
    by_capture: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_sender: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    observer = collections.Counter()
    observer_rows = 0

    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            if not member.isfile():
                continue
            extracted = bundle.extractfile(member)
            if extracted is None:
                continue
            raw = extracted.read()
            if member.name.endswith("/observer.jsonl"):
                for line in raw.decode().splitlines():
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    observer[str(row.get("stepsRemoved"))] += 1
                    observer_rows += 1
            elif member.name.endswith(("/up.pcap.gz", "/dn.pcap.gz")):
                capture = member.name.rsplit("/", 1)[-1]
                for packet in pcap_packets(gzip.decompress(raw)):
                    parsed = announce(packet)
                    if parsed is None:
                        continue
                    key = (
                        parsed["source_clock_identity"],
                        parsed["grandmaster_identity"],
                        parsed["steps_removed"],
                    )
                    counts[key] += 1
                    by_capture[capture][parsed["steps_removed"]] += 1
                    by_sender[parsed["source_clock_identity"]][parsed["steps_removed"]] += 1

    report = {
        "archive": str(archive),
        "observer_rows": observer_rows,
        "observer_steps_removed": dict(sorted(observer.items())),
        "announce_packets": sum(counts.values()),
        "announce_by_capture": {k: dict(sorted(v.items())) for k, v in sorted(by_capture.items())},
        "announce_by_sender": {k: dict(sorted(v.items())) for k, v in sorted(by_sender.items())},
        "announce_tuples": [
            {
                "source_clock_identity": source,
                "grandmaster_identity": grandmaster,
                "steps_removed": steps,
                "packets": number,
            }
            for (source, grandmaster, steps), number in sorted(counts.items())
        ],
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
