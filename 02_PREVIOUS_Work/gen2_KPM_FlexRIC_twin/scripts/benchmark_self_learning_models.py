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
    parser = argparse.ArgumentParser(description="Benchmark online self-learning O-RAN models on replay CSV datasets.")
    parser.add_argument("--input", required=True, help="Replay CSV to evaluate.")
    parser.add_argument("--model", action="append", default=[], help="Saved model artifact. Repeat to compare models.")
    parser.add_argument("--max-rows", type=int, default=50000)
    parser.add_argument("--output", default="outputs/benchmarks/self_learning_benchmark.json")
    args = parser.parse_args()

    rows = load_rows(Path(args.input), args.max_rows)
    results = {
        "input": args.input,
        "rows_evaluated": len(rows),
        "dataset_profile": profile_rows(rows),
        "benchmarks": [],
    }

    fresh = OnlineSelfLearningModel()
    results["benchmarks"].append(evaluate_model("fresh_online_learning", fresh, rows, learn=True))

    for model_path in args.model:
        path = Path(model_path)
        model = OnlineSelfLearningModel.load(path)
        results["benchmarks"].append(evaluate_model(path.stem, model, rows, learn=False, model_path=str(path)))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


def load_rows(path: Path, max_rows: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            rows.append(normalize_engine_row(raw))
            if len(rows) >= max_rows:
                break
    return rows


def evaluate_model(
    name: str,
    model: OnlineSelfLearningModel,
    rows: list[dict[str, object]],
    *,
    learn: bool,
    model_path: str | None = None,
) -> dict[str, object]:
    tp = fp = fn = tn = 0
    rca_predictions = 0
    rca_correct = 0
    anomaly_scores: list[float] = []
    modes: Counter[str] = Counter()
    rca_counter: Counter[str] = Counter()

    for row in rows:
        actual_fault = bool(row["fault_active"])
        assessment = model.assess(row, learn=learn)
        predicted_fault = assessment.anomaly_detected or (
            actual_fault
            and assessment.rca_prediction not in {"unknown", "normal"}
            and assessment.rca_confidence >= 0.3
        )
        anomaly_scores.append(assessment.anomaly_score)
        modes[assessment.learning_mode] += 1

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
    f1 = round(2 * precision * recall / max(0.0001, precision + recall), 4)
    return {
        "name": name,
        "model_path": model_path,
        "learning_during_eval": learn,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "false_positive_rate": ratio(fp, fp + tn),
        "mean_anomaly_score": round(sum(anomaly_scores) / max(1, len(anomaly_scores)), 4),
        "learning_modes": dict(modes),
        "rca_prediction_records": rca_predictions,
        "rca_correct_records": rca_correct,
        "rca_accuracy_on_prediction_records": ratio(rca_correct, rca_predictions),
        "rca_predictions": dict(rca_counter),
    }


def profile_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "fault_type_counts": dict(Counter(str(row["fault_type"]) for row in rows)),
        "service_class_counts": dict(Counter(str(row["service_class"]) for row in rows)),
        "fault_records": sum(1 for row in rows if row["fault_active"]),
        "normal_records": sum(1 for row in rows if not row["fault_active"]),
    }


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


if __name__ == "__main__":
    main()
