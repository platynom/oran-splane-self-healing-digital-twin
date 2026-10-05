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
    parser = argparse.ArgumentParser(description="Benchmark SMO/Non-RT RIC governance and model lifecycle outputs.")
    parser.add_argument("--input", default="data/training/generalized_virtual_ran_scenarios.csv")
    parser.add_argument("--output", default="outputs/benchmarks/smo_governance_benchmark.json")
    parser.add_argument("--max-rows", type=int, default=12000)
    args = parser.parse_args()

    rows = load_rows(Path(args.input), args.max_rows)
    engine = OranDecisionEngine(self_learning_model_path="outputs/models/phy_odu_virtual_ran_self_learning_model.json")
    decisions = [engine.assess(row) for row in rows]
    result = summarize(decisions, args.input)

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
    guarded = sum(1 for item in decisions if item["smo_governance_state"] != "governance_normal")
    model_review = sum(1 for item in decisions if item["smo_approval_gate"] == "mlops_model_review")
    critical_review = sum(1 for item in decisions if item["smo_approval_gate"] == "human_change_advisory_board")
    security_review = sum(1 for item in decisions if item["smo_approval_gate"] == "soc_noc_joint_approval")
    retraining_queue = sum(
        1
        for item in decisions
        if item["smo_retraining_dataset_action"]
        not in {"append_to_audit_dataset", "exclude_until_security_review"}
    )
    candidate_selected = sum(1 for item in decisions if item["smo_candidate_model"] != "none")
    rollback_available = sum(1 for item in decisions if item["smo_rollback_target"] != "none")
    return {
        "version": "v1.6",
        "input": input_path,
        "rows_evaluated": total,
        "purpose": "Validate SMO/Non-RT RIC governance, policy approval gates, model lifecycle, and retraining queue decisions.",
        "governed_decision_rate": ratio(guarded, total),
        "mlops_model_review_rate": ratio(model_review, total),
        "critical_change_review_rate": ratio(critical_review, total),
        "security_review_rate": ratio(security_review, total),
        "retraining_queue_rate": ratio(retraining_queue, total),
        "candidate_model_selection_rate": ratio(candidate_selected, total),
        "rollback_available_rate": ratio(rollback_available, total),
        "governance_state_counts": dict(Counter(str(item["smo_governance_state"]) for item in decisions)),
        "approval_gate_counts": dict(Counter(str(item["smo_approval_gate"]) for item in decisions)),
        "model_lifecycle_action_counts": dict(Counter(str(item["smo_model_lifecycle_action"]) for item in decisions)),
        "non_rt_policy_intent_counts": dict(Counter(str(item["smo_non_rt_policy_intent"]) for item in decisions)),
        "candidate_model_counts": dict(Counter(str(item["smo_candidate_model"]) for item in decisions)),
        "retraining_dataset_action_counts": dict(Counter(str(item["smo_retraining_dataset_action"]) for item in decisions)),
        "audit_class_counts": dict(Counter(str(item["smo_audit_class"]) for item in decisions)),
    }


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


if __name__ == "__main__":
    main()
