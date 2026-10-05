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

from oran_twin.engine import normalize_engine_row
from oran_twin.self_learning import OnlineSelfLearningModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Held-out Open RAN KPM benchmark by cluster/slicing/scheduler context.")
    parser.add_argument("--input", default="data/training/open_ran_kpm_training_dataset.csv")
    parser.add_argument("--holdout-cluster", default="cluster_3")
    parser.add_argument("--holdout-slicing", default="slicing_5")
    parser.add_argument("--holdout-scheduling", default="scheduling_2")
    parser.add_argument("--output", default="outputs/benchmarks/open_ran_kpm_heldout_benchmark.json")
    args = parser.parse_args()

    train_rows, test_rows = split_rows(
        Path(args.input),
        holdout_cluster=args.holdout_cluster,
        holdout_slicing=args.holdout_slicing,
        holdout_scheduling=args.holdout_scheduling,
    )
    model = OnlineSelfLearningModel()
    for row in train_rows:
        model.learn(row)

    benchmark = {
        "input": args.input,
        "holdout": {
            "cluster": args.holdout_cluster,
            "slicing": args.holdout_slicing,
            "scheduling": args.holdout_scheduling,
        },
        "train_profile": profile_rows(train_rows),
        "test_profile": profile_rows(test_rows),
        "test_metrics": evaluate_model(model, test_rows),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    print(json.dumps(benchmark, indent=2))


def split_rows(
    path: Path,
    *,
    holdout_cluster: str,
    holdout_slicing: str,
    holdout_scheduling: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    train_rows: list[dict[str, object]] = []
    test_rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row = normalize_engine_row(raw)
            row["_cluster"] = raw.get("cluster", "")
            row["_slicing"] = raw.get("slicing", "")
            row["_scheduling"] = raw.get("scheduling", "")
            if (
                row["_cluster"] == holdout_cluster
                and row["_slicing"] == holdout_slicing
                and row["_scheduling"] == holdout_scheduling
            ):
                test_rows.append(row)
            else:
                train_rows.append(row)
    return train_rows, test_rows


def evaluate_model(model: OnlineSelfLearningModel, rows: list[dict[str, object]]) -> dict[str, object]:
    tp = fp = fn = tn = 0
    rca_predictions = 0
    rca_correct = 0
    rca_counter: Counter[str] = Counter()
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
            rca_counter[assessment.rca_prediction] += 1
            if str(row["fault_type"]).split("+", 1)[0] == assessment.rca_prediction:
                rca_correct += 1

    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "f1_score": round(2 * precision * recall / max(0.0001, precision + recall), 4),
        "false_positive_rate": ratio(fp, fp + tn),
        "rca_prediction_records": rca_predictions,
        "rca_correct_records": rca_correct,
        "rca_accuracy_on_prediction_records": ratio(rca_correct, rca_predictions),
        "rca_predictions": dict(rca_counter),
    }


def profile_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "records": len(rows),
        "fault_records": sum(1 for row in rows if row["fault_active"]),
        "normal_records": sum(1 for row in rows if not row["fault_active"]),
        "service_class_counts": dict(Counter(str(row["service_class"]) for row in rows)),
        "fault_type_counts": dict(Counter(str(row["fault_type"]) for row in rows)),
    }


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


if __name__ == "__main__":
    main()
