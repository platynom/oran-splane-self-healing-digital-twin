from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oran_twin.engine import OranDecisionEngine, normalize_engine_row


SCHEDULE_FIELDS = [
    "run_name",
    "start_s",
    "end_s",
    "fault_type",
    "severity",
    "target_cell",
    "injection_method",
    "expected_healing_action",
]

LABELLED_FIELDS = [
    "t",
    "cell_id",
    "service_class",
    "fault_active",
    "fault_type",
    "fault_label_source",
    "fault_window_id",
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
    "cqi",
    "rsrp_dbm",
    "rsrq_db",
]

DECISION_FIELDS = [
    "t",
    "cell_id",
    "service_class",
    "expected_fault_active",
    "expected_fault_type",
    "predicted_anomaly",
    "predicted_root_cause",
    "predicted_healing_action",
    "automation_decision",
    "risk_score",
    "rca_correct",
    "healing_correct",
    "fault_window_id",
]


@dataclass(frozen=True)
class FaultWindow:
    window_id: str
    run_name: str
    start_s: int
    end_s: int
    fault_type: str
    severity: float
    target_cell: str
    injection_method: str
    expected_healing_action: str

    @property
    def active_duration_s(self) -> int:
        return max(0, self.end_s - self.start_s)

    def contains(self, t: int, cell_id: str) -> bool:
        return self.start_s <= t < self.end_s and (self.target_cell in {"", "*"} or self.target_cell == cell_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run controlled timestamped fault-injection evaluation.")
    parser.add_argument("--input", default="outputs/flexric_xapp_longrun_normalized.csv", help="Normalized KPI CSV.")
    parser.add_argument("--run-name", default="controlled_fault_eval_30min")
    parser.add_argument("--service", default="eMBB")
    parser.add_argument("--max-rows", type=int, default=2400)
    parser.add_argument("--schedule", default="", help="Optional existing schedule CSV. If missing, a default schedule is generated.")
    parser.add_argument("--schedule-output", default="outputs/evidence/controlled_fault_schedule.csv")
    parser.add_argument("--labelled-output", default="outputs/evidence/controlled_fault_injected_telemetry.csv")
    parser.add_argument("--decisions-output", default="outputs/evidence/controlled_fault_decisions.csv")
    parser.add_argument("--report-output", default="outputs/evidence/controlled_fault_evaluation.json")
    args = parser.parse_args()

    input_path = Path(args.input)
    rows = read_normalized_rows(input_path, args.service, args.max_rows)
    if not rows:
        raise SystemExit(f"No rows found in {input_path}")

    schedule_path = Path(args.schedule) if args.schedule else Path(args.schedule_output)
    if args.schedule and schedule_path.exists():
        windows = read_schedule(schedule_path)
    else:
        windows = default_schedule(args.run_name, rows)
        write_schedule(Path(args.schedule_output), windows)

    labelled_rows = build_labelled_rows(rows, windows)
    decisions = run_engine(labelled_rows)
    report = evaluate(decisions, windows, args.run_name)

    write_csv(Path(args.labelled_output), LABELLED_FIELDS, labelled_rows)
    write_csv(Path(args.decisions_output), DECISION_FIELDS, decisions)
    write_report(Path(args.report_output), report)
    print(json.dumps(report, indent=2))


def read_normalized_rows(path: Path, service: str, max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for t, row in enumerate(reader):
            cell_id = row.get("cell_id") or "CELL_A"
            rows.append(
                {
                    "t": t,
                    "cell_id": cell_id,
                    "service_class": row.get("service_class") or service,
                    "fault_active": False,
                    "fault_type": "normal",
                    "fault_label_source": "controlled_schedule",
                    "fault_window_id": "normal",
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
                    "cqi": value(row, "cqi", 9.0),
                    "rsrp_dbm": value(row, "rsrp_dbm", -85.0),
                    "rsrq_db": value(row, "rsrq_db", -9.0),
                }
            )
            if len(rows) >= max_rows:
                break
    return rows


def default_schedule(run_name: str, rows: list[dict[str, Any]]) -> list[FaultWindow]:
    cell_id = str(rows[0].get("cell_id", "CELL_A"))
    return [
        FaultWindow("fault_001", run_name, 300, 600, "backhaul_degradation", 0.8, cell_id, "synthetic_delay_80ms", "reroute_transport_path"),
        FaultWindow("fault_002", run_name, 780, 1080, "packet_loss_degradation", 0.75, cell_id, "synthetic_packet_loss_5pct", "switch_to_reliable_path"),
        FaultWindow("fault_003", run_name, 1260, 1560, "cell_congestion", 0.85, cell_id, "synthetic_prb_util_95pct", "load_balance_neighbor_cell"),
        FaultWindow("fault_004", run_name, 1740, 2040, "radio_link_degradation", 0.8, cell_id, "synthetic_sinr_bler_degradation", "adjust_radio_parameters"),
        FaultWindow("fault_005", run_name, 2160, 2340, "handover_instability", 0.75, cell_id, "synthetic_handover_fail_5pct", "optimize_handover_parameters"),
    ]


def read_schedule(path: Path) -> list[FaultWindow]:
    windows: list[FaultWindow] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for idx, row in enumerate(csv.DictReader(handle), start=1):
            windows.append(
                FaultWindow(
                    window_id=f"fault_{idx:03d}",
                    run_name=row.get("run_name", "controlled_fault_eval"),
                    start_s=int(float(row["start_s"])),
                    end_s=int(float(row["end_s"])),
                    fault_type=row["fault_type"],
                    severity=float(row.get("severity", 0.75) or 0.75),
                    target_cell=row.get("target_cell", "*"),
                    injection_method=row.get("injection_method", "controlled_synthetic_fault"),
                    expected_healing_action=row.get("expected_healing_action", expected_action(row["fault_type"])),
                )
            )
    return windows


def write_schedule(path: Path, windows: list[FaultWindow]) -> None:
    rows = [
        {
            "run_name": window.run_name,
            "start_s": window.start_s,
            "end_s": window.end_s,
            "fault_type": window.fault_type,
            "severity": window.severity,
            "target_cell": window.target_cell,
            "injection_method": window.injection_method,
            "expected_healing_action": window.expected_healing_action,
        }
        for window in windows
    ]
    write_csv(path, SCHEDULE_FIELDS, rows)


def build_labelled_rows(rows: list[dict[str, Any]], windows: list[FaultWindow]) -> list[dict[str, Any]]:
    labelled: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        t = int(out["t"])
        cell_id = str(out["cell_id"])
        active = next((window for window in windows if window.contains(t, cell_id)), None)
        if active:
            out.update(apply_fault(out, active))
        labelled.append(out)
    return labelled


def apply_fault(row: dict[str, Any], window: FaultWindow) -> dict[str, Any]:
    out = dict(row)
    out["fault_active"] = True
    out["fault_type"] = window.fault_type
    out["fault_window_id"] = window.window_id
    sev = max(0.0, min(1.0, window.severity))

    if window.fault_type == "backhaul_degradation":
        out["backhaul_delay_ms"] = max(float(out["backhaul_delay_ms"]), 20.0 + 80.0 * sev)
        out["latency_ms"] = max(float(out["latency_ms"]), 45.0 + 60.0 * sev)
        out["jitter_ms"] = max(float(out["jitter_ms"]), 8.0 + 10.0 * sev)
    elif window.fault_type == "packet_loss_degradation":
        out["packet_loss_pct"] = max(float(out["packet_loss_pct"]), 1.0 + 6.0 * sev)
        out["jitter_ms"] = max(float(out["jitter_ms"]), 8.0 + 8.0 * sev)
        out["prb_util_pct"] = min(float(out["prb_util_pct"]), 65.0)
        out["throughput_mbps"] = max(0.1, float(out["throughput_mbps"]) * (1.0 - 0.45 * sev))
    elif window.fault_type == "cell_congestion":
        out["prb_util_pct"] = max(float(out["prb_util_pct"]), 88.0 + 10.0 * sev)
        out["latency_ms"] = max(float(out["latency_ms"]), 45.0 + 40.0 * sev)
        out["throughput_mbps"] = max(0.1, float(out["throughput_mbps"]) * (1.0 - 0.5 * sev))
    elif window.fault_type == "radio_link_degradation":
        out["prb_util_pct"] = min(float(out["prb_util_pct"]), 65.0)
        out["sinr_db"] = min(float(out["sinr_db"]), 10.0 - 5.0 * sev)
        out["bler_pct"] = max(float(out["bler_pct"]), 5.0 + 7.0 * sev)
        out["rsrp_dbm"] = min(float(out["rsrp_dbm"]), -102.0 - 8.0 * sev)
        out["rsrq_db"] = min(float(out["rsrq_db"]), -14.0 - 4.0 * sev)
        out["throughput_mbps"] = max(0.1, float(out["throughput_mbps"]) * (1.0 - 0.5 * sev))
    elif window.fault_type == "handover_instability":
        out["handover_fail_pct"] = max(float(out["handover_fail_pct"]), 3.0 + 4.0 * sev)
        out["latency_ms"] = max(float(out["latency_ms"]), 35.0 + 35.0 * sev)
        out["jitter_ms"] = max(float(out["jitter_ms"]), 7.0 + 8.0 * sev)
    return out


def run_engine(labelled_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    engine = OranDecisionEngine()
    decisions: list[dict[str, Any]] = []
    for row in labelled_rows:
        normalized = normalize_engine_row(row)
        decision = engine.assess(normalized)
        expected_fault = str(row["fault_type"])
        predicted_root = str(decision["root_cause"])
        predicted_action = str(decision["healing_action"])
        decisions.append(
            {
                "t": row["t"],
                "cell_id": row["cell_id"],
                "service_class": row["service_class"],
                "expected_fault_active": bool(row["fault_active"]),
                "expected_fault_type": expected_fault,
                "predicted_anomaly": bool(decision["anomaly_detected"]),
                "predicted_root_cause": predicted_root,
                "predicted_healing_action": predicted_action,
                "automation_decision": decision["automation_safety_decision"],
                "risk_score": decision["twin_risk_score"],
                "rca_correct": root_cause_matches(expected_fault, predicted_root),
                "healing_correct": predicted_action == expected_action(expected_fault),
                "fault_window_id": row["fault_window_id"],
            }
        )
    return decisions


def evaluate(decisions: list[dict[str, Any]], windows: list[FaultWindow], run_name: str) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    rca_total = rca_correct = 0
    healing_total = healing_correct = 0
    for row in decisions:
        actual = bool(row["expected_fault_active"])
        predicted = bool(row["predicted_anomaly"])
        if actual and predicted:
            tp += 1
        elif actual and not predicted:
            fn += 1
        elif not actual and predicted:
            fp += 1
        else:
            tn += 1
        if actual and predicted:
            rca_total += 1
            rca_correct += int(bool(row["rca_correct"]))
            healing_total += 1
            healing_correct += int(bool(row["healing_correct"]))

    window_results = []
    for window in windows:
        rows = [row for row in decisions if row["fault_window_id"] == window.window_id]
        first_detection = next((int(row["t"]) for row in rows if bool(row["predicted_anomaly"])), None)
        rca_hits = sum(1 for row in rows if bool(row["predicted_anomaly"]) and bool(row["rca_correct"]))
        healing_hits = sum(1 for row in rows if bool(row["predicted_anomaly"]) and bool(row["healing_correct"]))
        detected_rows = sum(1 for row in rows if bool(row["predicted_anomaly"]))
        window_results.append(
            {
                "window_id": window.window_id,
                "fault_type": window.fault_type,
                "start_s": window.start_s,
                "end_s": window.end_s,
                "duration_s": window.active_duration_s,
                "detected_rows": detected_rows,
                "detection_coverage": ratio(detected_rows, len(rows)),
                "first_detection_s": first_detection,
                "detection_latency_s": None if first_detection is None else max(0, first_detection - window.start_s),
                "rca_accuracy_when_detected": ratio(rca_hits, detected_rows),
                "healing_accuracy_when_detected": ratio(healing_hits, detected_rows),
            }
        )

    return {
        "run_name": run_name,
        "records": len(decisions),
        "fault_windows": len(windows),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "f1_score": f1(tp, fp, fn),
        "false_positive_rate": ratio(fp, fp + tn),
        "false_negative_rate": ratio(fn, fn + tp),
        "rca_accuracy_when_detected": ratio(rca_correct, rca_total),
        "healing_accuracy_when_detected": ratio(healing_correct, healing_total),
        "expected_fault_counts": dict(Counter(str(row["expected_fault_type"]) for row in decisions)),
        "predicted_root_cause_counts": dict(Counter(str(row["predicted_root_cause"]) for row in decisions if bool(row["predicted_anomaly"]))),
        "window_results": window_results,
        "honest_interpretation": (
            "This is a controlled lab-style validation over replayed normalized KPM rows with timestamped synthetic fault injection. "
            "It provides an answer key for detection/RCA/healing measurement, but is still not operator production fault truth."
        ),
    }


def expected_action(fault_type: str) -> str:
    return {
        "backhaul_degradation": "reroute_transport_path",
        "packet_loss_degradation": "reroute_transport_path",
        "cell_congestion": "load_balance_neighbor_cell",
        "radio_link_degradation": "dynamic_spectrum_reassignment",
        "handover_instability": "rrc_mobility_policy_tuning",
        "normal": "no_action",
    }.get(fault_type, "human_review_guarded_mode")


def root_cause_matches(expected_fault: str, predicted_root: str) -> bool:
    aliases = {
        "radio_link_degradation": {"radio_link_degradation", "spectrum_interference", "radio_quality_degradation"},
        "packet_loss_degradation": {"packet_loss_degradation", "backhaul_degradation", "core_transport_degradation"},
        "cell_congestion": {"cell_congestion", "capacity_degradation"},
        "backhaul_degradation": {"backhaul_degradation", "core_transport_degradation"},
        "handover_instability": {"handover_instability", "mobility_instability"},
    }
    return predicted_root in aliases.get(expected_fault, {expected_fault})


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# Controlled Fault-Injection Evaluation",
        "",
        f"Run name: {report['run_name']}",
        "",
        "## Summary",
        "",
        f"- Records: {report['records']}",
        f"- Fault windows: {report['fault_windows']}",
        f"- Precision: {report['precision']}",
        f"- Recall: {report['recall']}",
        f"- F1-score: {report['f1_score']}",
        f"- False-positive rate: {report['false_positive_rate']}",
        f"- RCA accuracy when detected: {report['rca_accuracy_when_detected']}",
        f"- Healing accuracy when detected: {report['healing_accuracy_when_detected']}",
        "",
        "## Window Results",
        "",
        "| Fault | Start | End | Detection coverage | Detection latency | RCA accuracy | Healing accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["window_results"]:
        md.append(
            "| {fault_type} | {start_s} | {end_s} | {detection_coverage} | {latency} | {rca} | {healing} |".format(
                fault_type=row["fault_type"],
                start_s=row["start_s"],
                end_s=row["end_s"],
                detection_coverage=row["detection_coverage"],
                latency="not_detected" if row["detection_latency_s"] is None else row["detection_latency_s"],
                rca=row["rca_accuracy_when_detected"],
                healing=row["healing_accuracy_when_detected"],
            )
        )
    md.extend(["", "## Honest Interpretation", "", report["honest_interpretation"], ""])
    path.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")


def value(row: dict[str, str], key: str, default: float) -> float:
    try:
        raw = row.get(key)
        return float(raw) if raw not in {None, ""} else default
    except ValueError:
        return default


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


def f1(tp: int, fp: int, fn: int) -> float:
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return round((2 * precision * recall) / max(0.0001, precision + recall), 4)


if __name__ == "__main__":
    main()
