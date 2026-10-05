"""Trace frozen V2 timing-pattern flags to causal packet windows; read-only of captures."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from evaluate_v2_repeated import PLAN, RUNS
from streaming_discriminator_v1 import StreamState, observe, packet_from_frame
from ingest.ptp_wire import read_pcap

HERE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_run(name: str) -> dict:
    capture = RUNS / name / "capture.pcap"
    capture_id = digest(capture)
    state = StreamState()
    start = None
    flags: list[dict] = []
    reasons: Counter[str] = Counter()
    for ordinal, (timestamp_ns, frame) in enumerate(read_pcap(str(capture)), start=1):
        timestamp = timestamp_ns / 1e9
        if start is None:
            start = timestamp
        packet = packet_from_frame(capture_id, timestamp, frame)
        result = observe(state, packet)
        reasons[f"{result['validity']}:{result['reason']}"] += 1
        if result["classification"] != "CONFIGURED_IMPAIRMENT_SUSPECT":
            continue
        context = packet["context"]
        # This deque is the already-causal trailing input used on this exact packet.
        pairs = list(state.paired_gaps[context])
        flags.append({
            "packet_ordinal": ordinal,
            "capture_elapsed_s": round(timestamp - start, 9),
            "context": {"transportSpecific": context[1], "version": context[2], "domain": context[3], "sourcePortIdentity_hex": context[4]},
            "sync_sequence_id": packet["sequence_id"],
            "current_sync_followup_gap_s": result["gap_s"],
            "trailing_window_count": result["window_count"],
            "trailing_std_s": result["trailing_std_s"],
            "trailing_pairs": [{"followup_capture_elapsed_s": round(t - start, 9), "gap_s": gap} for t, gap in pairs],
        })
    return {"capture_sha256": capture_id, "flag_count": len(flags), "flags": flags, "validity_reason_counts": dict(sorted(reasons.items()))}


def main() -> None:
    result = {
        "schema_version": "v2-control-flag-diagnosis-v1",
        "purpose": "read-only explanation of frozen V2 feature windows; it neither changes nor validates the rule",
        "conditions": {condition: {name: inspect_run(name) for name in names} for condition, names in PLAN.items()},
        "interpretation_limit": "Capture-arrival Sync/Follow_Up dispersion can reflect software scheduling and capture timing. This evidence establishes the values the frozen rule consumed, not a causal explanation for them.",
    }
    (HERE / "V2_CONTROL_FLAG_DIAGNOSIS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
