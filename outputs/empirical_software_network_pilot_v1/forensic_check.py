#!/usr/bin/env python3
"""Forensic Verification Script for Set 2 Captures.

Verifies that all 12 set2 captures are distinct, strictly ordered in time,
and use independent MAC addresses.
"""

import hashlib
import json
import struct
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT_DIR / "outputs" / "empirical_software_network_pilot_v1" / "runs"

INTERLEAVED_ORDER = [
    "20260911_set2_baseline_r1",
    "20260911_set2_netem_r1",
    "20260911_set2_control_r1",
    "20260911_set2_intervention_r1",
    "20260911_set2_baseline_r2",
    "20260911_set2_netem_r2",
    "20260911_set2_control_r2",
    "20260911_set2_intervention_r2",
    "20260911_set2_baseline_r3",
    "20260911_set2_netem_r3",
    "20260911_set2_control_r3",
    "20260911_set2_intervention_r3",
]


def parse_pcap_info(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 24:
        return 0, 0.0, 0.0, []
    magic = struct.unpack("<I", data[:4])[0]
    if magic == 0xA1B2C3D4:
        endian, ts_factor = "<", 1e6
    elif magic == 0xD4C3B2A1:
        endian, ts_factor = ">", 1e6
    elif magic == 0xA1B23C4D:
        endian, ts_factor = "<", 1e9
    elif magic == 0x4D3CB2A1:
        endian, ts_factor = ">", 1e9
    else:
        raise ValueError(f"Unknown pcap magic: {hex(magic)}")

    offset = 24
    count = 0
    first_ts = None
    last_ts = None
    macs = set()

    while offset + 16 <= len(data):
        hdr = data[offset : offset + 16]
        ts_sec, ts_sub, incl_len, orig_len = struct.unpack(f"{endian}IIII", hdr)
        ts = ts_sec + (ts_sub / ts_factor)
        offset += 16
        pkt_data = data[offset : offset + incl_len]
        offset += incl_len

        if len(pkt_data) >= 14:
            src_mac = ":".join(f"{b:02x}" for b in pkt_data[6:12])
            ethertype = struct.unpack(">H", pkt_data[12:14])[0]
            if ethertype == 0x88F7:
                count += 1
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
                macs.add(src_mac)

    return count, first_ts or 0.0, last_ts or 0.0, sorted(list(macs))


def main():
    rows = []
    sha_set = set()
    epoch_list = []
    mac_to_runs = {}

    print("=== TASK A: FORENSIC VERIFICATION OF SET 2 CAPTURES ===")
    print(
        f"{'directory':32s} | {'sha256':16s} | {'size_bytes':10s} | {'first_epoch_s':15s} | {'last_epoch_s':15s} | {'frames':6s} | {'distinct_macs'}"
    )
    print("-" * 120)

    for dir_name in INTERLEAVED_ORDER:
        dpath = RUNS_DIR / dir_name
        pcap_path = dpath / "capture.pcap"
        data = pcap_path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        size_bytes = len(data)
        count, first_ts, last_ts, macs = parse_pcap_info(pcap_path)

        sha_set.add(sha256)
        epoch_list.append(first_ts)
        for m in macs:
            mac_to_runs.setdefault(m, []).append(dir_name)

        print(
            f"{dir_name:32s} | {sha256[:16]} | {size_bytes:10d} | {first_ts:15.6f} | {last_ts:15.6f} | {count:6d} | {','.join(macs)}"
        )

    # Check A1: All 12 sha256 values are distinct
    pass_a1 = len(sha_set) == 12
    # Check A2: All 12 first_frame_epoch_s values are distinct and strictly increasing
    pass_a2 = len(epoch_list) == 12 and all(
        epoch_list[i] < epoch_list[i + 1] for i in range(len(epoch_list) - 1)
    )
    # Check A3: No two runs share a source MAC
    shared_macs = {m: r for m, r in mac_to_runs.items() if len(r) > 1}
    pass_a3 = len(shared_macs) == 0

    print("-" * 120)
    print(f"A1 (all 12 sha256 distinct): {'PASS' if pass_a1 else 'FAIL'}")
    print(
        f"A2 (all 12 first_frame_epoch_s distinct & strictly increasing): {'PASS' if pass_a2 else 'FAIL'}"
    )
    print(f"A3 (no shared source MACs across runs): {'PASS' if pass_a3 else 'FAIL'}")


if __name__ == "__main__":
    main()
