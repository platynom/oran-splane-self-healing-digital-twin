from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oran_twin.engine import normalize_engine_row
from oran_twin.self_learning import OnlineSelfLearningModel


PHY_ODU_FEATURES = {
    "cqi",
    "harq_retx_pct",
    "rlc_buffer_kbytes",
    "mac_scheduler_delay_ms",
    "beam_quality_score",
    "timing_offset_us",
    "fronthaul_delay_ms",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark V1.2 PHY/O-DU-aware self-learning against generic KPI-only learning."
    )
    parser.add_argument("--input", default="data/training/generalized_virtual_ran_scenarios.csv")
    parser.add_argument("--output", default="outputs/benchmarks/phy_odu_generalization_benchmark.json")
    parser.add_argument("--model-output", default="outputs/models/phy_odu_virtual_ran_self_learning_model.json")
    parser.add_argument("--max-rows", type=int, default=60000)
    args = parser.parse_args()

    rows = load_rows(Path(args.input), args.max_rows)
    holdouts = build_holdouts(rows)
    benchmark = {
        "version": "v1.2",
        "input": args.input,
        "rows_evaluated": len(rows),
        "purpose": "Measure whether O-DU/High-PHY feature signals improve generalization beyond generic KPI-only learning.",
        "new_features": sorted(PHY_ODU_FEATURES),
        "dataset_profile": profile_rows(rows),
        "holdout_results": [],
    }

    for holdout in holdouts:
        train_rows = [row for row in rows if row.get(holdout["field"]) != holdout["value"]]
        test_rows = [row for row in rows if row.get(holdout["field"]) == holdout["value"]]
        benchmark["holdout_results"].append(
            {
                "holdout": holdout,
                "train_profile": profile_rows(train_rows),
                "test_profile": profile_rows(test_rows),
                "generic_kpi_only": train_and_evaluate(train_rows, test_rows, zero_phy_odu=True),
                "phy_odu_aware": train_and_evaluate(train_rows, test_rows, zero_phy_odu=False),
            }
        )

    final_model = OnlineSelfLearningModel()
    for row in rows:
        final_model.learn(row)
    model_output = Path(args.model_output)
    final_model.save(model_output)
    benchmark["trained_model_artifact"] = str(model_output)
    benchmark["aggregate"] = aggregate_results(benchmark["holdout_results"])

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    print(json.dumps(benchmark, indent=2))


def load_rows(path: Path, max_rows: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row = normalize_engine_row(raw)
            for key in (
                "area_persona",
                "event_context",
                "weather_context",
                "temporal_context",
                "mobility_index",
                "density_index",
                "interference_index",
                "edge_pressure_index",
            ):
                row[key] = raw.get(key, "")
            rows.append(row)
            if len(rows) >= max_rows:
                break
    return rows


def build_holdouts(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    area_counts = Counter(str(row.get("area_persona", "")) for row in rows)
    event_counts = Counter(str(row.get("event_context", "")) for row in rows)
    service_counts = Counter(str(row.get("service_class", "")) for row in rows)
    return [
        {"field": "area_persona", "value": area_counts.most_common(1)[0][0]},
        {"field": "event_context", "value": event_counts.most_common(1)[0][0]},
        {"field": "service_class", "value": service_counts.most_common(1)[0][0]},
    ]


def train_and_evaluate(
    train_rows: list[dict[str, object]],
    test_rows: list[dict[str, object]],
    *,
    zero_phy_odu: bool,
) -> dict[str, object]:
    model = OnlineSelfLearningModel()
    started = perf_counter()
    for row in train_rows:
        model.learn(mask_phy_odu(row) if zero_phy_odu else row)
    train_seconds = perf_counter() - started

    started = perf_counter()
    metrics = evaluate_model(model, [mask_phy_odu(row) if zero_phy_odu else row for row in test_rows])
    inference_seconds = perf_counter() - started
    metrics["train_seconds"] = round(train_seconds, 4)
    metrics["inference_seconds"] = round(inference_seconds, 4)
    metrics["feature_mode"] = "generic_kpi_only" if zero_phy_odu else "phy_odu_aware"
    return metrics


def mask_phy_odu(row: dict[str, object]) -> dict[str, object]:
    masked = dict(row)
    for feature in PHY_ODU_FEATURES:
        masked[feature] = 0.0
    return masked


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


def aggregate_results(results: list[dict[str, object]]) -> dict[str, object]:
    aggregate: dict[str, object] = {}
    for mode in ("generic_kpi_only", "phy_odu_aware"):
        metrics = [item[mode] for item in results]
        aggregate[mode] = {
            "mean_precision": mean(metrics, "precision"),
            "mean_recall": mean(metrics, "recall"),
            "mean_f1_score": mean(metrics, "f1_score"),
            "mean_false_positive_rate": mean(metrics, "false_positive_rate"),
            "mean_rca_accuracy_on_prediction_records": mean(metrics, "rca_accuracy_on_prediction_records"),
        }
    return aggregate


def profile_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "records": len(rows),
        "fault_records": sum(1 for row in rows if row["fault_active"]),
        "normal_records": sum(1 for row in rows if not row["fault_active"]),
        "service_class_counts": dict(Counter(str(row["service_class"]) for row in rows)),
        "fault_type_counts": dict(Counter(str(row["fault_type"]) for row in rows)),
        "area_counts": dict(Counter(str(row.get("area_persona", "")) for row in rows)),
    }


def mean(rows: list[dict[str, object]], key: str) -> float:
    return round(sum(float(row[key]) for row in rows) / max(1, len(rows)), 4)


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


if __name__ == "__main__":
    main()
