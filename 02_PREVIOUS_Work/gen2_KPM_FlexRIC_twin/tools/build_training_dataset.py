from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oran_twin.engine import normalize_engine_row
from tools.normalize_telemetry import parse_kv_log


ENGINE_FIELDS = [
    "t",
    "cell_id",
    "service_class",
    "fault_active",
    "fault_type",
    "aml_attack_active",
    "aml_attack_type",
    "latency_ms",
    "jitter_ms",
    "throughput_mbps",
    "packet_loss_pct",
    "prb_util_pct",
    "handover_fail_pct",
    "edge_delay_ms",
    "backhaul_delay_ms",
    "sinr_db",
    "bler_pct",
]

OUTPUT_FIELDS = ENGINE_FIELDS + [
    "source_id",
    "source_type",
    "source_file",
    "label_quality",
    "ingestion_note",
]

CONTROL_PLANE_PATTERNS = {
    "e2_setup_request": "E2 SETUP-REQUEST",
    "e2_setup_response": "E2 SETUP RESPONSE",
    "kpm_ran_function": "ORAN-E2SM-KPM",
    "near_rt_ric_started": "nearRT-RIC IP Address",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a replay-training CSV from real, emulated, or public O-RAN telemetry.")
    parser.add_argument("--input", action="append", required=True, help="Input telemetry CSV/log path. Repeat for multiple files.")
    parser.add_argument("--output", default="data/training/authentic_training_dataset.csv")
    parser.add_argument("--source-type", default="auto", choices=["auto", "normalized_csv", "kv_log", "flexric_log"])
    parser.add_argument("--source-id", default="local_ingestion")
    parser.add_argument("--default-service", default="eMBB")
    parser.add_argument("--summary-output", default="")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    control_events: list[dict[str, Any]] = []
    for input_value in args.input:
        path = Path(input_value)
        detected = detect_source_type(path, args.source_type)
        if detected == "flexric_log":
            control_events.extend(parse_control_plane_log(path, args.source_id))
            continue
        rows.extend(load_kpi_rows(path, detected, args.source_id, args.default_service))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_path, rows)

    summary = build_summary(rows, control_events, args.input, output_path)
    summary_path = Path(args.summary_output) if args.summary_output else output_path.with_suffix(".summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def detect_source_type(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "normalized_csv"
    text = read_text(path)
    if any(pattern in text for pattern in CONTROL_PLANE_PATTERNS.values()):
        return "flexric_log"
    return "kv_log"


def load_kpi_rows(path: Path, source_type: str, source_id: str, default_service: str) -> list[dict[str, Any]]:
    if source_type == "normalized_csv":
        raw_rows = read_csv_rows(path)
    elif source_type == "kv_log":
        raw_rows = parse_kv_log(read_text(path), cell_id="CELL_A")
    else:
        raise ValueError(f"{source_type} is not a KPI-bearing source type")

    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rows):
        inferred_fault_type = str(raw.get("fault_type", raw.get("fault", infer_fault_type(raw))))
        inferred_fault_active = infer_fault_active(raw) or inferred_fault_type not in {"normal", "none", ""}
        enriched = {
            **raw,
            "t": raw.get("t", index),
            "service_class": raw.get("service_class", raw.get("service", default_service)),
            "fault_active": raw.get("fault_active", inferred_fault_active),
            "fault_type": inferred_fault_type,
            "aml_attack_active": raw.get("aml_attack_active", False),
            "aml_attack_type": raw.get("aml_attack_type", "none"),
        }
        normalized = normalize_engine_row(enriched)
        rows.append(
            {
                **{field: normalized[field] for field in ENGINE_FIELDS},
                "source_id": source_id,
                "source_type": source_type,
                "source_file": str(path),
                "label_quality": label_quality(raw),
                "ingestion_note": "kpi_row_replay_ready",
            }
        )
    return rows


def parse_control_plane_log(path: Path, source_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        for event_type, pattern in CONTROL_PLANE_PATTERNS.items():
            if pattern in line:
                events.append(
                    {
                        "source_id": source_id,
                        "source_type": "flexric_log",
                        "source_file": str(path),
                        "line": line_no,
                        "event_type": event_type,
                        "event_text": compact(line),
                    }
                )
    return events


def infer_fault_active(row: dict[str, Any]) -> bool:
    if "fault" in row:
        return str(row.get("fault")).strip().lower() not in {"", "normal", "none", "false", "0"}
    if "fault_type" in row:
        return str(row.get("fault_type")).strip().lower() not in {"", "normal", "none"}
    return False


def infer_fault_type(row: dict[str, Any]) -> str:
    prb = to_float(row, "prb_util_pct", "prb")
    sinr = to_float(row, "sinr_db", "sinr")
    bler = to_float(row, "bler_pct", "bler")
    loss = to_float(row, "packet_loss_pct", "loss")
    handover = to_float(row, "handover_fail_pct", "handover")
    backhaul = to_float(row, "backhaul_delay_ms", "backhaul")
    if prb is not None and prb >= 88:
        return "cell_congestion"
    if sinr is not None and sinr <= 12:
        return "radio_interference"
    if bler is not None and bler >= 4:
        return "radio_link_degradation"
    if handover is not None and handover >= 3:
        return "handover_instability"
    if backhaul is not None and backhaul >= 10:
        return "backhaul_degradation"
    if loss is not None and loss >= 3:
        return "packet_loss_degradation"
    return "normal"


def label_quality(row: dict[str, Any]) -> str:
    if "fault_active" in row or "fault_type" in row or "fault" in row:
        return "explicit_label"
    inferred = infer_fault_type(row)
    if inferred != "normal":
        return "weak_rule_label"
    return "unlabeled_assumed_normal"


def build_summary(
    rows: list[dict[str, Any]],
    control_events: list[dict[str, Any]],
    inputs: list[str],
    output_path: Path,
) -> dict[str, Any]:
    fault_counts = Counter(str(row["fault_type"]) for row in rows)
    source_counts = Counter(str(row["source_type"]) for row in rows)
    label_counts = Counter(str(row["label_quality"]) for row in rows)
    event_counts = Counter(str(event["event_type"]) for event in control_events)
    return {
        "output": str(output_path),
        "inputs": inputs,
        "training_rows": len(rows),
        "source_type_counts": dict(source_counts),
        "label_quality_counts": dict(label_counts),
        "fault_type_counts": dict(fault_counts),
        "control_plane_events": len(control_events),
        "control_plane_event_counts": dict(event_counts),
        "can_train_self_learning_model": len(rows) > 0,
        "note": "Control-plane events prove RIC/E2/KPM integration, but only KPI rows are used for replay training.",
    }


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def to_float(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if value in {None, ""}:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()[:240]


if __name__ == "__main__":
    main()
