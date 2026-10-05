#!/usr/bin/env python3
"""Structural validation for an executed free-running protocol pilot."""
from __future__ import annotations

import argparse, hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"))
from ingest.ptp_wire import MSG_NAME, decode_ptp_payload, parse_eth_frame, read_pcap  # noqa: E402

REQUIRED = ("capture.pcap", "events.log", "run_environment.txt", "master_a.conf", "master_b.conf", "slave.conf", "master_a.log", "master_b.log", "slave.log", "tcpdump.log", "source_manifest.sha256")
SCENARIOS = {"baseline_control", "netem_delay_jitter_loss", "benign_delay_jitter_no_loss", "authorized_source_change_no_action_control", "authorized_source_change_intervention"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()

def parse_kv(line: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in line.split() if "=" in part)

def parse_manifest_text(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in text.splitlines():
        digest, sep, raw_path = line.partition("  ")
        if sep and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest.lower()):
            entries[Path(raw_path.strip()).name] = digest.lower()
    return entries

def status_from_evidence(events: list[dict[str, str]], log_bytes: dict[str, int], packets: int, errors: list[str]) -> str:
    if errors or packets <= 0 or any(size <= 0 for size in log_bytes.values()): return "INCOMPLETE"
    phases = [row for row in events if row.get("event") == "phase_finished" and row.get("status") == "PASS"]
    ready = [row for row in events if row.get("phase") == "setup" and row.get("event", "").endswith("_ready") and row.get("status") == "PASS"]
    return "STRUCTURALLY_COMPLETE" if len(phases) == 1 and len(ready) == 4 else "INCOMPLETE"

def validate(run_dir: Path) -> dict:
    missing = [x for x in REQUIRED if not (run_dir / x).is_file()]
    report: dict[str, object] = {"schema_version": "pilot-validation-v2", "run_directory": str(run_dir), "missing_required_artifacts": missing, "outcome_label_policy": "NOT_ASSIGNED"}
    if missing: report["status"] = "INCOMPLETE"; return report
    event_rows = [parse_kv(x) for x in (run_dir / "events.log").read_text(encoding="utf-8", errors="replace").splitlines()]
    errors: list[str] = []
    if not event_rows or any(not {"run_id", "phase", "event", "utc", "monotonic_s", "status"} <= set(x) for x in event_rows): errors.append("malformed_event_record")
    if any(x.get("status") == "FAIL" for x in event_rows): errors.append("recorded_command_or_readiness_failure")
    phase = next((x.get("phase") for x in event_rows if x.get("event") == "phase_started"), None)
    if phase not in SCENARIOS: errors.append("missing_or_unknown_scenario")
    if phase and not any(x.get("phase") == phase and x.get("event") == "phase_finished" and x.get("status") == "PASS" for x in event_rows): errors.append("missing_successful_phase_finish")
    if phase == "netem_delay_jitter_loss" and not any(x.get("event") == "netem_command_confirmed" and x.get("status") == "PASS" for x in event_rows): errors.append("netem_not_command_confirmed")
    if phase == "benign_delay_jitter_no_loss" and not any(x.get("event") == "benign_netem_command_confirmed" and x.get("status") == "PASS" for x in event_rows): errors.append("benign_netem_not_command_confirmed")
    if phase == "authorized_source_change_intervention" and not any(x.get("event") == "preferred_master_stop_confirmed" and x.get("status") == "PASS" for x in event_rows): errors.append("source_change_not_command_confirmed")
    packet_types: Counter[str] = Counter(); undecoded = 0
    for _ts, frame in read_pcap(str(run_dir / "capture.pcap")):
        payload = parse_eth_frame(frame); msg = decode_ptp_payload(payload) if payload else None
        if msg is None: undecoded += 1
        else: packet_types[MSG_NAME[msg.msg_type]] += 1
    packets = sum(packet_types.values()) + undecoded
    logs = {x: (run_dir / x).stat().st_size for x in ("master_a.log", "master_b.log", "slave.log", "tcpdump.log")}
    if any(b"ERROR" in (run_dir / x).read_bytes().upper() for x in logs): errors.append("error_text_in_process_log")
    hashes = {x: sha256(run_dir / x) for x in REQUIRED if x != "source_manifest.sha256"}
    manifest = parse_manifest_text((run_dir / "source_manifest.sha256").read_text(encoding="utf-8", errors="replace"))
    matches = {x: manifest.get(x) == digest for x, digest in hashes.items()}
    if not all(matches.values()): errors.append("manifest_hash_mismatch")
    report.update({"events": event_rows, "scenario": phase, "pcap": {"records": packets, "decoded_message_counts": dict(packet_types), "undecoded_records": undecoded}, "log_bytes": logs, "manifest_hashes_match": matches, "errors": errors, "status": status_from_evidence(event_rows, logs, packets, errors), "interpretation_limit": "This validates artifact integrity and documented process/qdisc commands only. free_running 1 means no closed-loop clock recovery or independent-clock claim."})
    return report

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("run_directory", type=Path); args = parser.parse_args()
    report = validate(args.run_directory); (args.run_directory / "validation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True)); raise SystemExit(0 if report["status"] == "STRUCTURALLY_COMPLETE" else 1)
if __name__ == "__main__": main()
