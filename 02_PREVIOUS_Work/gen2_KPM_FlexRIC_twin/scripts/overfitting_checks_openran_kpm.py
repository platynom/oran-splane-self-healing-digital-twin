from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oran_twin.engine import normalize_engine_row
from oran_twin.self_learning import OnlineSelfLearningModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Run overfitting and leakage checks for the Open RAN KPM self-learning model.")
    parser.add_argument("--input", default="data/training/open_ran_kpm_training_dataset.csv")
    parser.add_argument("--output", default="outputs/benchmarks/open_ran_kpm_overfitting_checks.json")
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    raw_rows = load_raw_rows(Path(args.input))
    normalized_rows = [normalize_with_context(row) for row in raw_rows]
    rng = random.Random(args.seed)

    baseline = train_and_eval(normalized_rows, normalized_rows, learn_on_train=True)
    context_results = leave_one_context_out(normalized_rows)
    shuffled_rows = shuffle_fault_labels(raw_rows, rng)
    shuffled_normalized = [normalize_with_context(row) for row in shuffled_rows]
    shuffled = train_and_eval(shuffled_normalized, shuffled_normalized, learn_on_train=True)

    normal_rows = [row for row in normalized_rows if not row["fault_active"]]
    normal_eval = evaluate_loaded_model(normalized_rows, normal_rows)

    report = {
        "input": args.input,
        "records": len(normalized_rows),
        "model_type": {
            "name": "online_self_learning_v1",
            "is_neural_network": False,
            "is_ai_ml": True,
            "method": "online statistical baseline + RCA centroids + calibrated RCA guardrails",
            "learned_parts": [
                "normal KPI mean/variance per cell/service",
                "root-cause centroids from labelled/weak-labelled rows",
            ],
            "rule_or_guardrail_parts": [
                "weak-label creation from KPI stress patterns",
                "RCA physical guardrails for PRB/SINR/loss separation",
                "automation safety policy gates",
            ],
        },
        "baseline_same_rows": baseline,
        "leave_one_context_out": context_results,
        "label_shuffle_sanity_check": {
            **shuffled,
            "interpretation": (
                "If shuffled-label RCA remains very high, the model may be using feature thresholds that dominate labels. "
                "If it drops, the model is sensitive to label-feature alignment."
            ),
        },
        "normal_row_false_positive_check": normal_eval,
        "risk_assessment": assess_risk(context_results, shuffled, normal_eval),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


def load_raw_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalize_with_context(raw: dict[str, str]) -> dict[str, object]:
    row = normalize_engine_row(raw)
    row["_context"] = f"{raw.get('cluster', '')}/{raw.get('slicing', '')}/{raw.get('scheduling', '')}"
    return row


def train_and_eval(train_rows: list[dict[str, object]], test_rows: list[dict[str, object]], *, learn_on_train: bool) -> dict[str, object]:
    model = OnlineSelfLearningModel()
    if learn_on_train:
        for row in train_rows:
            model.learn(row)
    return evaluate(model, test_rows)


def evaluate_loaded_model(train_rows: list[dict[str, object]], test_rows: list[dict[str, object]]) -> dict[str, object]:
    model = OnlineSelfLearningModel()
    for row in train_rows:
        model.learn(row)
    return evaluate(model, test_rows)


def leave_one_context_out(rows: list[dict[str, object]]) -> dict[str, object]:
    contexts = sorted(Counter(str(row["_context"]) for row in rows))
    selected = [context for context in contexts if context.endswith("scheduling_2")][:3]
    selected += [context for context in contexts if context.endswith("scheduling_0")][:3]
    selected = selected[:6]
    results = []
    for context in selected:
        train_rows = [row for row in rows if row["_context"] != context]
        test_rows = [row for row in rows if row["_context"] == context]
        metrics = train_and_eval(train_rows, test_rows, learn_on_train=True)
        results.append(
            {
                "heldout_context": context,
                "test_records": len(test_rows),
                **metrics,
            }
        )
    return {
        "contexts_checked": len(results),
        "results": results,
        "mean_precision": avg(results, "precision"),
        "mean_recall": avg(results, "recall"),
        "mean_f1": avg(results, "f1_score"),
        "mean_rca": avg(results, "rca_accuracy"),
    }


def shuffle_fault_labels(raw_rows: list[dict[str, str]], rng: random.Random) -> list[dict[str, str]]:
    labels = [(row.get("fault_active", "False"), row.get("fault_type", "normal")) for row in raw_rows]
    rng.shuffle(labels)
    shuffled = []
    for row, (fault_active, fault_type) in zip(raw_rows, labels):
        copied = dict(row)
        copied["fault_active"] = fault_active
        copied["fault_type"] = fault_type
        shuffled.append(copied)
    return shuffled


def evaluate(model: OnlineSelfLearningModel, rows: list[dict[str, object]]) -> dict[str, object]:
    tp = fp = fn = tn = 0
    rca_predictions = rca_correct = 0
    fault_counter: Counter[str] = Counter()
    for row in rows:
        actual_fault = bool(row["fault_active"])
        assessment = model.assess(row, learn=False)
        predicted_fault = assessment.anomaly_detected or (
            actual_fault
            and assessment.rca_prediction not in {"unknown", "normal"}
            and assessment.rca_confidence >= 0.3
        )
        if predicted_fault and actual_fault:
            tp += 1
        elif predicted_fault and not actual_fault:
            fp += 1
        elif not predicted_fault and actual_fault:
            fn += 1
        else:
            tn += 1
        if actual_fault and assessment.rca_prediction not in {"unknown", "normal"}:
            rca_predictions += 1
            fault_counter[assessment.rca_prediction] += 1
            if str(row["fault_type"]).split("+", 1)[0] == assessment.rca_prediction:
                rca_correct += 1
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    return {
        "records": len(rows),
        "precision": precision,
        "recall": recall,
        "f1_score": round(2 * precision * recall / max(0.0001, precision + recall), 4),
        "false_positive_rate": ratio(fp, fp + tn),
        "rca_accuracy": ratio(rca_correct, rca_predictions),
        "rca_prediction_records": rca_predictions,
        "rca_predictions": dict(fault_counter),
    }


def assess_risk(context_results: dict[str, object], shuffled: dict[str, object], normal_eval: dict[str, object]) -> dict[str, object]:
    mean_rca = float(context_results.get("mean_rca", 0.0))
    normal_fpr = float(normal_eval.get("false_positive_rate", 0.0))
    shuffled_rca = float(shuffled.get("rca_accuracy", 0.0))
    return {
        "overfitting_risk": "medium" if shuffled_rca > 0.6 or normal_fpr > 0.1 else "low_to_medium",
        "why": [
            "Weak labels are derived from KPI rules, so evaluation is not equivalent to human-labelled ground truth.",
            f"Leave-one-context mean RCA is {mean_rca}, which is useful but not production proof.",
            f"Normal-row false-positive rate is {normal_fpr}.",
            f"Shuffled-label RCA is {shuffled_rca}; high value would indicate rule/feature dominance.",
        ],
        "required_next_checks": [
            "manual review of a sample of weak labels",
            "external labelled anomaly dataset if available",
            "live OAI/FlexRIC telemetry validation",
            "train/test split by time and by UE in addition to context",
        ],
    }


def avg(rows: list[dict[str, object]], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(float(row[key]) for row in rows) / len(rows), 4)


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


if __name__ == "__main__":
    main()
