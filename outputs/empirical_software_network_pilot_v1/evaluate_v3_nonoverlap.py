"""One-pass, hash-bound run-level evaluation of the frozen V3 prospective protocol."""
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
RUNS = HERE / "v3_runs"
PLAN = {
    "baseline_control": [f"20260913_v3_b{i}" for i in range(1, 6)],
    "netem_delay_jitter_loss": [f"20260913_v3_n{i}" for i in range(1, 6)],
    "authorized_source_change_no_action_control": [f"20260913_v3_c{i}" for i in range(1, 6)],
    "authorized_source_termination_observation": [f"20260913_v3_s{i}" for i in range(1, 6)],
}
REQUIRED_MANIFEST_ENTRIES = {"capture.pcap", "events.log", "run_environment.txt", "master_a.conf", "master_b.conf", "slave.conf", "master_a.log", "master_b.log", "slave.log", "tcpdump.log"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_inputs() -> dict[str, str]:
    frozen = json.loads((HERE / "V3_NONOVERLAPPING_PROSPECTIVE_PROTOCOL.json").read_text())["frozen_inputs"]
    actual = {
        "streaming_discriminator_v1.py_sha256": sha256(HERE / "streaming_discriminator_v1.py"),
        "streaming_discriminator_v3_nonoverlap.py_sha256": sha256(HERE / "streaming_discriminator_v3_nonoverlap.py"),
    }
    mismatch = {key: {"expected": frozen[key], "actual": value} for key, value in actual.items() if frozen[key].lower() != value.lower()}
    if mismatch:
        raise RuntimeError(f"frozen input hash mismatch: {json.dumps(mismatch, sort_keys=True)}")
    return actual


def wilson(k: int, n: int, z: float = 1.95996398454) -> dict:
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {"k": k, "n": n, "proportion": p, "wilson95": [max(0, center - radius), min(1, center + radius)]}


def cached_verification_valid(validation: dict) -> bool:
    cached = validation.get("manifest_hashes_match")
    return validation.get("status") == "STRUCTURALLY_COMPLETE" and isinstance(cached, dict) and bool(cached) and all(value is True for value in cached.values())


def manifest_mismatches(manifest: dict[str, str], actual_hashes: dict[str, str | None]) -> dict[str, str]:
    mismatches = {name: "missing" if actual_hashes.get(name) is None else "hash_mismatch" for name, expected in manifest.items() if actual_hashes.get(name) != expected}
    if not REQUIRED_MANIFEST_ENTRIES <= set(manifest):
        mismatches["required_manifest_entries"] = "missing"
    return mismatches


def verify_run_artifacts(run_dir: Path, validation: dict) -> dict:
    """Reject stale, malformed, or merely asserted run-integrity evidence before replay."""
    if not cached_verification_valid(validation):
        raise RuntimeError(f"cached manifest verification missing or false: {run_dir.name}")
    manifest_path = run_dir / "source_manifest.sha256"
    if not manifest_path.is_file():
        raise RuntimeError(f"source manifest missing: {run_dir.name}")
    manifest = parse_manifest_text(manifest_path.read_text(encoding="utf-8", errors="strict"))
    if not manifest:
        raise RuntimeError(f"source manifest malformed or empty: {run_dir.name}")
    actual_hashes: dict[str, str | None] = {}
    for name in manifest:
        path = run_dir / name
        actual_hashes[name] = sha256(path) if path.is_file() else None
    mismatches = manifest_mismatches(manifest, actual_hashes)
    if mismatches:
        raise RuntimeError(f"actual source-manifest verification failed for {run_dir.name}: {json.dumps(mismatches, sort_keys=True)}")
    return {"cached_validation_status": validation["status"], "manifest_entries_rehashed": len(manifest), "actual_manifest_hashes_match": True, "source_manifest_sha256": sha256(manifest_path)}


def evaluate_run(name: str) -> dict:
    run_dir = RUNS / name
    validation = json.loads((run_dir / "validation.json").read_text())
    verification = verify_run_artifacts(run_dir, validation)
    capture = run_dir / "capture.pcap"
    capture_hash = sha256(capture)
    state = NonoverlapV3State()
    counts: Counter[str] = Counter()
    validity_reasons: Counter[str] = Counter()
    events: Counter[str] = Counter()
    first: dict[str, float] = {}
    first_event: dict[str, float] = {}
    start = None
    for ordinal, (timestamp_ns, frame) in enumerate(read_pcap(str(capture)), start=1):
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
        "artifact_verification": verification,
    }


def main() -> None:
    verified = verify_frozen_inputs()
    runs = {condition: {name: evaluate_run(name) for name in names} for condition, names in PLAN.items()}
    summary = {condition: wilson(sum(row["any_nonoverlap_persistence"] for row in rows.values()), len(rows)) for condition, rows in runs.items()}
    netem_gate = summary["netem_delay_jitter_loss"]["k"] >= 4
    controls = summary["baseline_control"]["k"] + summary["authorized_source_change_no_action_control"]["k"]
    aggregate_artifact_validity = all(row["artifact_verification"]["actual_manifest_hashes_match"] for condition in runs.values() for row in condition.values())
    output = {
        "schema_version": "v3-nonoverlap-run-evaluation-v1",
        "protocol": "V3_NONOVERLAPPING_PROSPECTIVE_PROTOCOL.json",
        "frozen_input_verification": verified,
        "scope": "predeclared n=5 per condition, isolated free-running software feasibility; run level only",
        "runs": runs,
        "run_level_summary": summary,
        "prospective_feasibility_gates": {"netem_at_least_4_of_5": netem_gate, "baseline_plus_no_action_controls_zero_of_10": controls == 0, "all_structural_and_manifest_valid": aggregate_artifact_validity, "result": "PASS" if netem_gate and controls == 0 and aggregate_artifact_validity else "FAIL"},
        "excluded_runs": [],
        "limits": ["one prospective pilot; wide n=5 uncertainty", "labels are evaluation metadata, never features", "shared-host free_running software-clock observations", "no attack, health, receiver-selection, outage, physical timing, or recovery inference"],
    }
    (HERE / "V3_NONOVERLAPPING_EVALUATION.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
