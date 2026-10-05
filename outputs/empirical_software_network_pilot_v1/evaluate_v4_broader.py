"""One-pass, hash-bound run-level evaluation of the frozen V4 broader validation protocol.

Faithful adaptation of evaluate_v3_nonoverlap.py: same frozen detector, same thresholds,
pointed at v4_runs with the five V4 conditions. No threshold or inclusion change.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from streaming_discriminator_v1 import packet_from_frame
from streaming_discriminator_v3_nonoverlap import NonoverlapV3State, observe_nonoverlap_v3
from ingest.ptp_wire import read_pcap
from validate_pilot import parse_manifest_text

HERE = Path(__file__).resolve().parent
RUNS = HERE / "v4_runs"
PROTOCOL = HERE / "V4_BROADER_VALIDATION_PROTOCOL.json"
PLAN = {
    "baseline_control": [f"20260913_v4_b{i}" for i in range(1, 6)],
    "netem_delay_jitter_loss": [f"20260913_v4_n{i}" for i in range(1, 6)],
    "benign_delay_jitter_no_loss": [f"20260913_v4_d{i}" for i in range(1, 6)],
    "benign_authorized_source_change_no_action": [f"20260913_v4_c{i}" for i in range(1, 6)],
    "authorized_source_termination_observation": [f"20260913_v4_s{i}" for i in range(1, 6)],
}
REQUIRED_MANIFEST_ENTRIES = {"capture.pcap", "events.log", "run_environment.txt", "master_a.conf",
                             "master_b.conf", "slave.conf", "master_a.log", "master_b.log",
                             "slave.log", "tcpdump.log"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_inputs() -> dict:
    frozen = json.loads(PROTOCOL.read_text())["frozen_rule"]
    app = HERE.parents[1] / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
    actual = {
        "v1_engine_sha256": sha256(HERE / "streaming_discriminator_v1.py"),
        "v3_nonoverlap_engine_sha256": sha256(HERE / "streaming_discriminator_v3_nonoverlap.py"),
        "isolated_runner_sha256": sha256(app / "harness" / "run_empirical_software_pilot.sh"),
        "validator_sha256": sha256(HERE / "validate_pilot.py"),
    }
    mismatch = {k: {"expected": frozen[k], "actual": v} for k, v in actual.items()
                if frozen[k].lower() != v.lower()}
    if mismatch:
        raise RuntimeError(f"frozen input hash mismatch: {json.dumps(mismatch, sort_keys=True)}")
    return {"frozen_hashes_match": True, **actual,
            "frozen_thresholds": {k: frozen[k] for k in
                                  ("standard_deviation_threshold_s", "block_size",
                                   "high_block_count", "high_block_window_s")}}


def wilson(k: int, n: int, z: float = 1.95996398454) -> dict:
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {"k": k, "n": n, "proportion": p, "wilson95": [max(0, center - radius), min(1, center + radius)]}


def cached_verification_valid(validation: dict) -> bool:
    cached = validation.get("manifest_hashes_match")
    return (validation.get("status") == "STRUCTURALLY_COMPLETE" and isinstance(cached, dict)
            and bool(cached) and all(v is True for v in cached.values()))


def manifest_mismatches(manifest: dict, actual_hashes: dict) -> dict:
    mismatches = {name: "missing" if actual_hashes.get(name) is None else "hash_mismatch"
                  for name, expected in manifest.items() if actual_hashes.get(name) != expected}
    if not REQUIRED_MANIFEST_ENTRIES <= set(manifest):
        mismatches["required_manifest_entries"] = "missing"
    return mismatches


def verify_run_artifacts(run_dir: Path, validation: dict) -> dict:
    if not cached_verification_valid(validation):
        raise RuntimeError(f"cached manifest verification missing or false: {run_dir.name}")
    manifest_path = run_dir / "source_manifest.sha256"
    if not manifest_path.is_file():
        raise RuntimeError(f"source manifest missing: {run_dir.name}")
    manifest = parse_manifest_text(manifest_path.read_text(encoding="utf-8", errors="strict"))
    if not manifest:
        raise RuntimeError(f"source manifest malformed or empty: {run_dir.name}")
    actual_hashes = {name: (sha256(run_dir / name) if (run_dir / name).is_file() else None)
                     for name in manifest}
    mismatches = manifest_mismatches(manifest, actual_hashes)
    if mismatches:
        raise RuntimeError(f"actual source-manifest verification failed for {run_dir.name}: "
                           f"{json.dumps(mismatches, sort_keys=True)}")
    return {"cached_validation_status": validation["status"],
            "manifest_entries_rehashed": len(manifest),
            "actual_manifest_hashes_match": True,
            "source_manifest_sha256": sha256(manifest_path)}


def evaluate_run(name: str) -> dict:
    run_dir = RUNS / name
    validation = json.loads((run_dir / "validation.json").read_text())
    verification = verify_run_artifacts(run_dir, validation)
    capture = run_dir / "capture.pcap"
    capture_hash = sha256(capture)
    state = NonoverlapV3State()
    counts: Counter = Counter()
    validity_reasons: Counter = Counter()
    events: Counter = Counter()
    first: dict = {}
    first_event: dict = {}
    start = None
    for _ordinal, (timestamp_ns, frame) in enumerate(read_pcap(str(capture)), start=1):
        timestamp = timestamp_ns / 1e9
        if start is None:
            start = timestamp
        output = observe_nonoverlap_v3(state, packet_from_frame(capture_hash, timestamp, frame))
        counts[output["classification"]] += 1
        validity_reasons[f"{output['validity']}:{output['reason']}"] += 1
        if output["classification"] not in first:
            first[output["classification"]] = round(timestamp - start, 9)
        for event in output["events"]:
            events[event["type"]] += 1
            if event["type"] not in first_event:
                first_event[event["type"]] = round(timestamp - start, 9)
    return {
        "capture_sha256": capture_hash,
        "packet_records": sum(counts.values()),
        "classification_counts": dict(counts),
        "validity_reason_counts": dict(validity_reasons),
        "independent_event_counts": dict(events),
        "first_independent_event_s": first_event,
        "first_classification_s": first,
        "any_nonoverlap_persistence": counts["NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED"] > 0,
        "scenario_recorded_in_validation": validation.get("scenario"),
        "artifact_verification": verification,
    }


def main() -> None:
    verified = verify_frozen_inputs()
    runs = {condition: {name: evaluate_run(name) for name in names}
            for condition, names in PLAN.items()}
    summary = {condition: wilson(sum(r["any_nonoverlap_persistence"] for r in rows.values()), len(rows))
               for condition, rows in runs.items()}
    aggregate_ok = all(r["artifact_verification"]["actual_manifest_hashes_match"]
                       for c in runs.values() for r in c.values())
    total_rehashed = sum(r["artifact_verification"]["manifest_entries_rehashed"]
                         for c in runs.values() for r in c.values())
    output = {
        "schema_version": "v4-broader-run-evaluation-v1",
        "protocol": "V4_BROADER_VALIDATION_PROTOCOL.json",
        "frozen_input_verification": verified,
        "scope": ("predeclared n=5 per condition across five conditions; isolated free-running "
                  "software feasibility; run level only. V1-V3 captures excluded."),
        "runs": runs,
        "run_level_summary": summary,
        "aggregate_integrity": {"all_actual_manifest_hashes_match": aggregate_ok,
                                "total_manifest_entries_rehashed": total_rehashed,
                                "runs_evaluated": sum(len(v) for v in runs.values())},
        "excluded_runs": [],
        "limits": [
            "one prospective batch; wide n=5 uncertainty per condition",
            "condition labels are evaluation metadata, never detector features",
            "shared-host free_running software-clock observations; namespaces are not independent clocks",
            "packet-arrival dispersion is not a referenced receiver clock-error measurement",
            "no attack, health, receiver-selection, outage, physical timing, or recovery inference",
            "V4 determines only whether the packet-arrival observation repeats under its frozen conditions",
        ],
    }
    (HERE / "V4_BROADER_EVALUATION.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"summary": summary, "aggregate_integrity": output["aggregate_integrity"]}, indent=2))


if __name__ == "__main__":
    main()
