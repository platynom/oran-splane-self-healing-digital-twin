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


CORE_CAUSES = {
    "core_control_plane_degradation",
    "upf_user_plane_congestion",
    "transport_path_degradation",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark 5G Core and N3/N6 transport impact handling.")
    parser.add_argument("--input", default="data/training/generalized_virtual_ran_scenarios.csv")
    parser.add_argument("--output", default="outputs/benchmarks/core_transport_benchmark.json")
    parser.add_argument("--max-rows", type=int, default=12000)
    args = parser.parse_args()

    rows = load_rows(Path(args.input), args.max_rows)
    engine = OranDecisionEngine(self_learning_model_path="outputs/models/phy_odu_virtual_ran_self_learning_model.json")
    decisions = [engine.assess(row) for row in rows]
    result = summarize(rows, decisions, args.input)

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


def summarize(rows: list[dict[str, object]], decisions: list[dict[str, object]], input_path: str) -> dict[str, object]:
    total = len(decisions)
    core_label_count = sum(1 for row in rows if str(row.get("fault_type")) in CORE_CAUSES)
    core_detected = sum(1 for item in decisions if item["core_transport_state"] != "core_transport_stable")
    core_incidents = sum(1 for item in decisions if item["core_transport_state"] == "core_transport_incident")
    core_rca = sum(1 for item in decisions if str(item["root_cause"]) in CORE_CAUSES)
    core_actions = sum(
        1
        for item in decisions
        if str(item["healing_action"]) in {"amf_pdu_session_recovery_review", "upf_scale_or_traffic_reroute", "reroute_transport_path"}
        and str(item["core_transport_state"]) != "core_transport_stable"
    )
    exact_core_rca = sum(
        1
        for row, item in zip(rows, decisions)
        if str(row.get("fault_type")) in CORE_CAUSES and str(item["root_cause"]) == str(row.get("fault_type"))
    )
    core_label_detected = sum(
        1
        for row, item in zip(rows, decisions)
        if str(row.get("fault_type")) in CORE_CAUSES and bool(item["anomaly_detected"])
    )
    guarded_core = sum(
        1
        for item in decisions
        if str(item["core_transport_state"]) != "core_transport_stable" and not bool(item["action_approved_by_twin"])
    )
    return {
        "version": "v1.7",
        "input": input_path,
        "rows_evaluated": total,
        "purpose": "Validate 5G Core control-plane, UPF user-plane, and N3/N6 transport impact handling.",
        "core_label_rate": ratio(core_label_count, total),
        "core_transport_watch_or_incident_rate": ratio(core_detected, total),
        "core_transport_incident_rate": ratio(core_incidents, total),
        "core_root_cause_rate": ratio(core_rca, total),
        "core_action_rate": ratio(core_actions, total),
        "core_guarded_rate": ratio(guarded_core, max(1, core_detected)),
        "core_label_detection_recall": ratio(core_label_detected, core_label_count),
        "core_label_exact_rca_rate": ratio(exact_core_rca, core_label_count),
        "core_transport_state_counts": dict(Counter(str(item["core_transport_state"]) for item in decisions)),
        "affected_plane_counts": dict(Counter(str(item["core_transport_affected_plane"]) for item in decisions)),
        "core_likely_cause_counts": dict(Counter(str(item["core_transport_likely_cause"]) for item in decisions)),
        "root_cause_counts_for_core_labels": dict(
            Counter(str(item["root_cause"]) for row, item in zip(rows, decisions) if str(row.get("fault_type")) in CORE_CAUSES)
        ),
        "core_recommended_action_counts": dict(Counter(str(item["core_transport_recommended_action"]) for item in decisions)),
        "healing_action_counts": dict(Counter(str(item["healing_action"]) for item in decisions)),
        "policy_domain_counts": dict(Counter(str(item["policy_orchestration_domain"]) for item in decisions)),
        "ric_control_type_counts": dict(Counter(str(item["ric_control"].get("type", "none")) for item in decisions)),
        "slice_domain_counts": dict(Counter(str(item["slice_affected_domain"]) for item in decisions)),
    }


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


if __name__ == "__main__":
    main()
