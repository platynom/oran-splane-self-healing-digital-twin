from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oran_twin.engine import OranDecisionEngine, normalize_engine_row


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Near-RT RIC/xApp arbitration and control safety.")
    parser.add_argument("--input", default="data/training/generalized_virtual_ran_scenarios.csv")
    parser.add_argument("--output", default="outputs/benchmarks/xapp_arbitration_benchmark.json")
    parser.add_argument("--max-rows", type=int, default=12000)
    parser.add_argument("--stress-cell", default="RIC_STRESS_CELL", help="Cell ID used for repeated-control stress rows.")
    parser.add_argument("--stress-rows", type=int, default=300)
    args = parser.parse_args()

    rows = load_rows(Path(args.input), args.max_rows)
    engine = OranDecisionEngine(self_learning_model_path="outputs/models/phy_odu_virtual_ran_self_learning_model.json")
    decisions = [engine.assess(row) for row in rows]
    stress_rows = build_repeated_control_stress_rows(args.stress_cell, args.stress_rows)
    stress_engine = OranDecisionEngine(self_learning_model_path="outputs/models/phy_odu_virtual_ran_self_learning_model.json")
    stress_decisions = [stress_engine.assess(row) for row in stress_rows]
    result = summarize(decisions, args.input)
    result["repeated_control_stress"] = summarize(stress_decisions, f"generated:{args.stress_cell}") 

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def load_rows(path: Path, max_rows: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            rows.append(normalize_engine_row(raw))
            if len(rows) >= max_rows:
                break
    return rows


def summarize(decisions: list[dict[str, object]], input_path: str) -> dict[str, object]:
    total = len(decisions)
    conflict_count = sum(1 for item in decisions if item["xapp_conflict_detected"])
    cooldown_count = sum(1 for item in decisions if item["xapp_cooldown_state"] == "cooldown_active")
    latency_risk_count = sum(
        1 for item in decisions if "control_loop_latency_risk" in list(item["xapp_conflict_reasons"])
    )
    approved_payloads = sum(1 for item in decisions if bool(item["ric_control"].get("approved")) and item["ric_control"].get("type") != "none")
    executable_guarded = sum(1 for item in decisions if bool(item["automation_guarded_would_execute"]))
    baseline_execute = sum(1 for item in decisions if bool(item["automation_baseline_would_execute"]))
    prevented = sum(1 for item in decisions if bool(item["unsafe_action_prevented"]))
    latencies = [float(item["xapp_control_loop_latency_ms"]) for item in decisions]
    return {
        "version": "v1.5",
        "input": input_path,
        "rows_evaluated": total,
        "purpose": "Validate xApp arbitration with conflict, cooldown, latency, and guarded-control evidence.",
        "conflict_rate": ratio(conflict_count, total),
        "cooldown_event_rate": ratio(cooldown_count, total),
        "control_latency_risk_rate": ratio(latency_risk_count, total),
        "ric_payload_approval_rate": ratio(approved_payloads, total),
        "guarded_execute_rate": ratio(executable_guarded, total),
        "baseline_execute_rate": ratio(baseline_execute, total),
        "unsafe_prevention_rate_vs_baseline": ratio(prevented, baseline_execute),
        "mean_control_loop_latency_ms": round(sum(latencies) / max(1, len(latencies)), 2),
        "p95_control_loop_latency_ms": percentile(latencies, 0.95),
        "selected_xapp_counts": dict(Counter(str(item["xapp_selected"]) for item in decisions)),
        "selected_action_counts": dict(Counter(str(item["healing_action"]) for item in decisions)),
        "automation_decision_counts": dict(Counter(str(item["automation_safety_decision"]) for item in decisions)),
        "conflict_type_counts": dict(Counter(str(item["xapp_conflict_type"]) for item in decisions)),
        "cooldown_state_counts": dict(Counter(str(item["xapp_cooldown_state"]) for item in decisions)),
        "ric_control_type_counts": dict(Counter(str(item["ric_control"].get("type", "none")) for item in decisions)),
    }


def build_repeated_control_stress_rows(cell_id: str, rows: int) -> list[dict[str, object]]:
    stress: list[dict[str, object]] = []
    services = ["eMBB", "URLLC", "V2X"]
    for index in range(rows):
        service = services[index % len(services)]
        stress.append(
            {
                "t": index,
                "cell_id": cell_id,
                "service_class": service,
                "fault_active": True,
                "fault_type": "cell_congestion" if index % 5 != 4 else "handover_instability",
                "aml_attack_active": False,
                "aml_attack_type": "none",
                "latency_ms": 72 + (index % 7),
                "jitter_ms": 8 + (index % 3),
                "throughput_mbps": 45,
                "packet_loss_pct": 2.4,
                "prb_util_pct": 94,
                "handover_fail_pct": 6.5 if index % 5 == 4 else 2.0,
                "edge_delay_ms": 2.4,
                "backhaul_delay_ms": 5.0,
                "sinr_db": 13.0,
                "bler_pct": 2.0,
                "cqi": 9.0,
                "harq_retx_pct": 4.0,
                "rlc_buffer_kbytes": 1320.0,
                "mac_scheduler_delay_ms": 13.0,
                "beam_quality_score": 0.7,
                "timing_offset_us": 5.0,
                "fronthaul_delay_ms": 2.2,
            }
        )
    return stress


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return round(ordered[index], 2)


if __name__ == "__main__":
    main()
