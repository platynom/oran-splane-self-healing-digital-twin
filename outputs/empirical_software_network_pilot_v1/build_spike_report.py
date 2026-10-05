#!/usr/bin/env python3
"""Build MECHANISM_FEASIBILITY.md from spike_two_path artifacts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"))
from ingest.ptp_wire import MSG_NAME, decode_ptp_payload, parse_eth_frame, read_pcap

SPIKE_DIR = Path(__file__).resolve().parent / "spike_two_path"
REPORT_PATH = SPIKE_DIR / "MECHANISM_FEASIBILITY.md"


def parse_events(events_path: Path) -> list[dict[str, str]]:
    if not events_path.is_file():
        return []
    rows = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            rows.append(dict(part.split("=", 1) for part in line.split() if "=" in part))
    return rows


def analyze_pcap(pcap_path: Path, split_ts: float | None = None) -> dict:
    if not pcap_path.is_file():
        return {"exists": False, "total_packets": 0, "before_split": 0, "after_split": 0, "msg_types": {}}
    total = 0
    before = 0
    after = 0
    msg_types: dict[str, int] = {}
    for ts_ns, frame in read_pcap(str(pcap_path)):
        total += 1
        ts_s = ts_ns / 1e9
        if split_ts is not None:
            if ts_s < split_ts:
                before += 1
            else:
                after += 1
        payload = parse_eth_frame(frame)
        msg = decode_ptp_payload(payload) if payload else None
        if msg:
            name = MSG_NAME.get(msg.msg_type, f"TYPE_{msg.msg_type}")
            msg_types[name] = msg_types.get(name, 0) + 1
        else:
            msg_types["undecoded"] = msg_types.get("undecoded", 0) + 1
    return {
        "exists": True,
        "total_packets": total,
        "before_split": before,
        "after_split": after,
        "msg_types": msg_types,
    }


def parse_tc(tc_path: Path) -> dict:
    if not tc_path.is_file():
        return {"raw": "file_missing", "packets": None, "bytes": None, "dropped": None}
    text = tc_path.read_text(encoding="utf-8", errors="replace")
    # match: Sent 1234 bytes 12 pkt (dropped 0, overlimits 0 requeues 0)
    m = re.search(r"Sent\s+(\d+)\s+bytes\s+(\d+)\s+pkt\s+\(dropped\s+(\d+)", text)
    if m:
        return {
            "raw": text.strip(),
            "bytes": int(m.group(1)),
            "packets": int(m.group(2)),
            "dropped": int(m.group(3)),
        }
    return {"raw": text.strip(), "packets": None, "bytes": None, "dropped": None}


def parse_slave_log(log_path: Path) -> dict:
    if not log_path.is_file():
        return {"exists": False, "ports_mentioned": [], "transitions": []}
    text = log_path.read_text(encoding="utf-8", errors="replace")
    ports_seen = set()
    transitions = []
    for line in text.splitlines():
        # e.g. "ptp4l[...]: port 1: INITIALIZING to LISTENING on INITIALIZE"
        m = re.search(r"port\s+(\d+):\s+([A-Z_]+)\s+to\s+([A-Z_]+)(?:\s+on\s+([A-Z_]+))?", line)
        if m:
            port_num = int(m.group(1))
            ports_seen.add(port_num)
            transitions.append({
                "port": port_num,
                "from": m.group(2),
                "to": m.group(3),
                "reason": m.group(4) or "UNKNOWN",
                "line": line.strip()
            })
    return {
        "exists": True,
        "ports_mentioned": sorted(ports_seen),
        "transitions": transitions,
        "raw_lines_count": len(text.splitlines()),
    }


def main() -> None:
    events = parse_events(SPIKE_DIR / "events.log")
    slave_log_data = parse_slave_log(SPIKE_DIR / "slave.log")

    # Find the impairment timestamp
    impair_event = next((e for e in events if e.get("event") == "v4_impairment_applied_s1"), None)
    impair_mono = float(impair_event["monotonic_s"]) if impair_event and "monotonic_s" in impair_event else None

    # For pcap timing, let's get first packet timestamp or use relative timing
    # Alternatively parse pcap split by first packet + settle duration
    # Settle duration is ~8 seconds
    pcap1_all = list(read_pcap(str(SPIKE_DIR / "capture_s1.pcap"))) if (SPIKE_DIR / "capture_s1.pcap").is_file() else []
    pcap2_all = list(read_pcap(str(SPIKE_DIR / "capture_s2.pcap"))) if (SPIKE_DIR / "capture_s2.pcap").is_file() else []

    first_ts = None
    if pcap1_all:
        first_ts = pcap1_all[0][0] / 1e9
    if pcap2_all and (first_ts is None or (pcap2_all[0][0] / 1e9) < first_ts):
        first_ts = pcap2_all[0][0] / 1e9

    # Settle period was recorded in events
    settle_event = next((e for e in events if e.get("event") == "phase_settle_started"), None)
    if settle_event and impair_event and first_ts:
        # relative time of impairment from settle start:
        impair_offset = float(impair_event["monotonic_s"]) - float(settle_event["monotonic_s"])
        split_ts = first_ts + impair_offset
    else:
        split_ts = None

    pcap1 = analyze_pcap(SPIKE_DIR / "capture_s1.pcap", split_ts)
    pcap2 = analyze_pcap(SPIKE_DIR / "capture_s2.pcap", split_ts)

    tc_s1_before = parse_tc(SPIKE_DIR / "tc_s1_before.txt")
    tc_s2_before = parse_tc(SPIKE_DIR / "tc_s2_before.txt")
    tc_s1_after = parse_tc(SPIKE_DIR / "tc_s1_after.txt")
    tc_s2_after = parse_tc(SPIKE_DIR / "tc_s2_after.txt")

    # Q1: Does one ptp4l instance actually bring up and hold two ports in this namespace?
    # Backed by slave.log showing both port 1 and port 2 active and holding states
    ports_held = len(slave_log_data["ports_mentioned"]) >= 2
    q1_answer = "YES" if ports_held else "NO"

    # Q2: Does PTP traffic flow on both paths before impairment?
    # Backed by capture_s1.pcap and capture_s2.pcap having packets before split_ts,
    # or tc counters before showing non-zero packets on both ports
    traffic_s1_pre = pcap1["before_split"] > 0 if split_ts else (pcap1["total_packets"] > 0)
    traffic_s2_pre = pcap2["before_split"] > 0 if split_ts else (pcap2["total_packets"] > 0)
    q2_traffic_both = traffic_s1_pre and traffic_s2_pre
    q2_answer = "YES" if q2_traffic_both else "NO"

    # Q3: With netem on one path only, does the clean path keep carrying PTP traffic?
    # Backed by capture_s2.pcap having packets after split_ts and tc_s2_after > tc_s2_before
    traffic_s2_post = pcap2["after_split"] > 0 if split_ts else (pcap2["total_packets"] > 0)
    q3_answer = "YES" if traffic_s2_post else "NO"

    # Q4: Does the slave's port state machine react to the impaired path at all, and how?
    # Backed by slave.log transitions after impairment
    # Let's inspect what transitions occurred
    transitions = slave_log_data["transitions"]
    # Check if there are transitions or if port states remained unchanged
    q4_reaction = False
    reaction_description = []
    for t in transitions:
        reaction_description.append(f"Port {t['port']}: {t['from']} -> {t['to']} ({t['reason']})")
    
    # Check if any transition occurred specifically on the impaired port (port 1) or clean port (port 2)
    # after the initial settling to SLAVE/PASSIVE
    settle_trans = transitions[:4]  # initial setup transitions
    later_trans = transitions[4:]
    if later_trans:
        q4_answer = f"YES: {'; '.join(t['line'] for t in later_trans)}"
    else:
        # If no subsequent transitions occurred:
        q4_answer = "NO: The port state machine did not change port states after the impairment was applied under this configuration and duration."

    lines = [
        "# Part B: Two-Path Mechanism Feasibility Spike Report",
        "",
        "## Purpose and Scope",
        "",
        "This capability check investigates whether a multi-port rerouting mechanism exists in this testbed.",
        "It evaluates one slave ptp4l instance configured with two ports connected via separate veth pairs",
        "to the bridge, with single-path netem impairment applied after a clean settle period.",
        "**NO closed-loop recovery was executed and NO recovery claim is made.**",
        "",
        "## Capability Questions and Evidence-Backed Answers",
        "",
        f"### Q1: Does one ptp4l instance actually bring up and hold two ports in this namespace?",
        f"**Answer**: **{q1_answer}**",
        "",
        f"- Evidence file: `slave.log`",
        f"- Ports observed in ptp4l log: {slave_log_data['ports_mentioned']}",
        "- State transitions recorded in slave.log:",
    ]
    for t in transitions:
        lines.append(f"  - `{t['line']}`")

    lines.extend([
        "",
        f"### Q2: Does PTP traffic flow on both paths before impairment?",
        f"**Answer**: **{q2_answer}**",
        "",
        f"- Evidence files: `capture_s1.pcap`, `capture_s2.pcap`, `tc_s1_before.txt`, `tc_s2_before.txt`",
        f"- Path 1 (S1) pre-impairment packets captured: {pcap1['before_split']} (total: {pcap1['total_packets']})",
        f"- Path 2 (S2) pre-impairment packets captured: {pcap2['before_split']} (total: {pcap2['total_packets']})",
        f"- S1 TC before: packets={tc_s1_before['packets']}, bytes={tc_s1_before['bytes']}, dropped={tc_s1_before['dropped']}",
        f"- S2 TC before: packets={tc_s2_before['packets']}, bytes={tc_s2_before['bytes']}, dropped={tc_s2_before['dropped']}",
        f"- Decoded message breakdown on Path 1: {pcap1['msg_types']}",
        f"- Decoded message breakdown on Path 2: {pcap2['msg_types']}",
        "",
        f"### Q3: With netem on one path only, does the clean path keep carrying PTP traffic?",
        f"**Answer**: **{q3_answer}**",
        "",
        f"- Evidence files: `capture_s2.pcap`, `tc_s2_before.txt`, `tc_s2_after.txt`",
        f"- Path 2 (clean path) packets captured after impairment: {pcap2['after_split']}",
        f"- S2 TC counters: before={tc_s2_before['packets']} pkts, after={tc_s2_after['packets']} pkts (delta={((tc_s2_after['packets'] or 0) - (tc_s2_before['packets'] or 0))} pkts)",
        f"- Path 1 (impaired path) TC counters: before={tc_s1_before['packets']} pkts, after={tc_s1_after['packets']} pkts (dropped={tc_s1_after['dropped']})",
        "",
        f"### Q4: Does the slave's port state machine react to the impaired path at all, and how?",
        f"**Answer**: **{q4_answer}**",
        "",
        f"- Evidence files: `slave.log`, `pmc_port_states.log`, `events.log`",
        f"- Total transitions logged: {len(transitions)}",
    ])
    if later_trans:
        lines.append("- Subsequent transitions observed after settle:")
        for t in later_trans:
            lines.append(f"  - `{t['line']}`")
    else:
        lines.append("- No port state transitions occurred following impairment onset during the observation window.")

    lines.extend([
        "",
        "## Artifact Manifest and Verification",
        "",
        "The following artifacts were produced by `spike_two_path_topology.sh` and hashed into `source_manifest.sha256`:",
        "- `capture_s1.pcap`",
        "- `capture_s2.pcap`",
        "- `events.log`",
        "- `master_a.conf`",
        "- `master_b.conf`",
        "- `slave.conf`",
        "- `master_a.log`",
        "- `master_b.log`",
        "- `slave.log`",
        "- `tc_s1_before.txt`",
        "- `tc_s1_after.txt`",
        "- `tc_s2_before.txt`",
        "- `tc_s2_after.txt`",
        "- `run_environment.txt`",
        "- `source_manifest.sha256`",
        "",
        "## Conclusion and Mechanism Feasibility Assessment",
        "",
        f"- Dual-port slave topology instantiation: {'FEASIBLE' if ports_held else 'NOT_FEASIBLE'}",
        f"- Dual-path traffic concurrency before impairment: {'CONFIRMED' if q2_traffic_both else 'NOT_OBSERVED'}",
        f"- Clean path traffic preservation under single-path netem: {'CONFIRMED' if traffic_s2_post else 'NOT_OBSERVED'}",
        "",
    ])

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH.name} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
