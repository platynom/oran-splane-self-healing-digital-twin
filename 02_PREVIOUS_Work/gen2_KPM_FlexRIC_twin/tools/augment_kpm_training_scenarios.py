from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


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
    "scenario",
    "label_quality",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create training rows from captured FlexRIC KPM plus controlled fault scenarios.")
    parser.add_argument("--input", required=True, help="Normalized FlexRIC KPM CSV.")
    parser.add_argument("--output", default="data/training/flexric_kpm_augmented_training.csv")
    parser.add_argument("--source-scenario", default="flexric_kpm_normal")
    parser.add_argument("--default-service", default="eMBB")
    parser.add_argument("--summary-output", default="")
    args = parser.parse_args()

    base_rows = read_csv(Path(args.input))
    output_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(base_rows):
        normal = to_engine_row(row, idx, args.default_service)
        normal["scenario"] = args.source_scenario
        normal["label_quality"] = "live_lab_assumed_normal"
        output_rows.append(normal)

        output_rows.append(apply_fault(normal, "cell_congestion", idx))
        output_rows.append(apply_fault(normal, "backhaul_degradation", idx))
        output_rows.append(apply_fault(normal, "radio_link_degradation", idx))
        output_rows.append(apply_fault(normal, "packet_loss_degradation", idx))
        output_rows.append(apply_fault(normal, "handover_instability", idx))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output, output_rows)
    summary = {
        "input": args.input,
        "output": str(output),
        "base_live_lab_rows": len(base_rows),
        "training_rows": len(output_rows),
        "scenarios_per_base_row": 6,
        "fault_types": sorted({str(row["fault_type"]) for row in output_rows}),
        "honest_note": (
            "Normal rows come from FlexRIC lab KPM capture. Fault rows are controlled synthetic augmentations "
            "used for local model stress-testing; they are not production fault truth."
        ),
    }
    summary_path = Path(args.summary_output) if args.summary_output else output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ENGINE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def to_engine_row(row: dict[str, str], idx: int, service: str) -> dict[str, Any]:
    return {
        "t": idx,
        "cell_id": row.get("cell_id") or "CELL_A",
        "service_class": service,
        "fault_active": False,
        "fault_type": "normal",
        "aml_attack_active": False,
        "aml_attack_type": "none",
        "latency_ms": value(row, "latency", 20.0),
        "jitter_ms": value(row, "jitter", 4.0),
        "throughput_mbps": value(row, "throughput", 100.0),
        "packet_loss_pct": value(row, "loss", 0.2),
        "prb_util_pct": value(row, "prb", 60.0),
        "handover_fail_pct": value(row, "handover", 0.8),
        "edge_delay_ms": value(row, "edgeDelay", 2.5),
        "backhaul_delay_ms": value(row, "backhaul", 4.0),
        "sinr_db": value(row, "sinr", 20.0),
        "bler_pct": value(row, "bler", 1.2),
        "scenario": "normal",
        "label_quality": "live_lab_assumed_normal",
    }


def apply_fault(row: dict[str, Any], fault_type: str, idx: int) -> dict[str, Any]:
    out = dict(row)
    out["t"] = f"{idx}_{fault_type}"
    out["fault_active"] = True
    out["fault_type"] = fault_type
    out["scenario"] = fault_type
    out["label_quality"] = "controlled_synthetic_fault"

    if fault_type == "cell_congestion":
        out["prb_util_pct"] = 94.0
        out["throughput_mbps"] = max(0.1, float(out["throughput_mbps"]) * 0.45)
        out["latency_ms"] = max(float(out["latency_ms"]), 55.0)
    elif fault_type == "backhaul_degradation":
        out["backhaul_delay_ms"] = 18.0
        out["latency_ms"] = max(float(out["latency_ms"]), 70.0)
        out["jitter_ms"] = max(float(out["jitter_ms"]), 12.0)
    elif fault_type == "radio_link_degradation":
        out["sinr_db"] = 7.0
        out["bler_pct"] = 8.0
        out["throughput_mbps"] = max(0.1, float(out["throughput_mbps"]) * 0.55)
    elif fault_type == "packet_loss_degradation":
        out["packet_loss_pct"] = 5.5
        out["jitter_ms"] = max(float(out["jitter_ms"]), 10.0)
    elif fault_type == "handover_instability":
        out["handover_fail_pct"] = 5.0
        out["latency_ms"] = max(float(out["latency_ms"]), 45.0)
    return out


def value(row: dict[str, str], key: str, default: float) -> float:
    try:
        raw = row.get(key)
        return float(raw) if raw not in {None, ""} else default
    except ValueError:
        return default


if __name__ == "__main__":
    main()
