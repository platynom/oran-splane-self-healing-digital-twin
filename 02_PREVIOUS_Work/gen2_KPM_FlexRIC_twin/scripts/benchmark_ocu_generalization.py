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


ORU_LOW_PHY_FEATURES = {
    "rsrp_dbm",
    "rsrq_db",
    "rssi_dbm",
    "noise_floor_dbm",
    "evm_pct",
    "interference_power_dbm",
    "beam_misalignment_deg",
    "antenna_vswr",
    "rf_temperature_c",
}

OCU_FEATURES = {
    "rrc_setup_fail_pct",
    "rrc_reestab_rate_pct",
    "pdcp_discard_rate_pct",
    "pdcp_reordering_delay_ms",
    "sdap_qos_flow_drop_pct",
    "qfi_violation_pct",
    "session_drop_rate_pct",
    "mobility_pingpong_pct",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark V1.4 O-CU-aware self-learning.")
    parser.add_argument("--input", default="data/training/generalized_virtual_ran_scenarios.csv")
    parser.add_argument("--output", default="outputs/benchmarks/ocu_generalization_benchmark.json")
    parser.add_argument("--model-output", default="outputs/models/ocu_virtual_ran_self_learning_model.json")
    parser.add_argument("--max-rows", type=int, default=60000)
    args = parser.parse_args()

    rows = load_rows(Path(args.input), args.max_rows)
    holdouts = build_holdouts(rows)
    benchmark = {
        "version": "v1.4",
        "input": args.input,
        "rows_evaluated": len(rows),
        "purpose": "Measure whether O-CU RRC/PDCP/SDAP features improve mobility and QoS/session RCA.",
        "ocu_features": sorted(OCU_FEATURES),
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
                "active_v1_2_view": train_and_evaluate(train_rows, test_rows, mode="active_v1_2_view"),
                "ocu_aware": train_and_evaluate(train_rows, test_rows, mode="ocu_aware"),
                "full_shadow_view": train_and_evaluate(train_rows, test_rows, mode="full_shadow_view"),
            }
        )

    final_model = OnlineSelfLearningModel()
    for row in rows:
        final_model.learn(mask_row(row, "ocu_aware"))
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
            for key in ("area_persona", "event_context", "weather_context", "temporal_context"):
                row[key] = raw.get(key, "")
            rows.append(row)
            if len(rows) >= max_rows:
                break
    return rows


def build_holdouts(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        {"field": "area_persona", "value": Counter(str(row.get("area_persona", "")) for row in rows).most_common(1)[0][0]},
        {"field": "service_class", "value": "V2X"},
        {"field": "event_context", "value": "sports_event"},
    ]


def train_and_evaluate(train_rows: list[dict[str, object]], test_rows: list[dict[str, object]], *, mode: str) -> dict[str, object]:
    model = OnlineSelfLearningModel()
    started = perf_counter()
    for row in train_rows:
        model.learn(mask_row(row, mode))
    train_seconds = perf_counter() - started

    started = perf_counter()
    metrics = evaluate_model(model, [mask_row(row, mode) for row in test_rows])
    inference_seconds = perf_counter() - started
    metrics["train_seconds"] = round(train_seconds, 4)
    metrics["inference_seconds"] = round(inference_seconds, 4)
    metrics["feature_mode"] = mode
    return metrics


def mask_row(row: dict[str, object], mode: str) -> dict[str, object]:
    masked = dict(row)
    if mode == "active_v1_2_view":
        for feature in ORU_LOW_PHY_FEATURES | OCU_FEATURES:
            masked[feature] = 0.0
    elif mode == "ocu_aware":
        for feature in ORU_LOW_PHY_FEATURES:
            masked[feature] = 0.0
    return masked


def evaluate_model(model: OnlineSelfLearningModel, rows: list[dict[str, object]]) -> dict[str, object]:
    tp = fp = fn = tn = 0
    rca_predictions = 0
    rca_correct = 0
    mobility_faults = mobility_correct = 0
    qos_faults = qos_correct = 0
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

        actual_cause = str(row["fault_type"]).split("+", 1)[0]
        if actual_fault and assessment.rca_prediction not in {"unknown", "normal"}:
            rca_predictions += 1
            rca_counter[assessment.rca_prediction] += 1
            if actual_cause == assessment.rca_prediction:
                rca_correct += 1
        if actual_cause == "handover_instability":
            mobility_faults += 1
            if assessment.rca_prediction == "handover_instability":
                mobility_correct += 1
        if actual_cause == "qos_session_degradation":
            qos_faults += 1
            if assessment.rca_prediction == "qos_session_degradation":
                qos_correct += 1

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
        "handover_instability_recall": ratio(mobility_correct, mobility_faults),
        "qos_session_degradation_recall": ratio(qos_correct, qos_faults),
        "rca_predictions": dict(rca_counter),
    }


def aggregate_results(results: list[dict[str, object]]) -> dict[str, object]:
    aggregate: dict[str, object] = {}
    for mode in ("active_v1_2_view", "ocu_aware", "full_shadow_view"):
        metrics = [item[mode] for item in results]
        aggregate[mode] = {
            "mean_precision": mean(metrics, "precision"),
            "mean_recall": mean(metrics, "recall"),
            "mean_f1_score": mean(metrics, "f1_score"),
            "mean_false_positive_rate": mean(metrics, "false_positive_rate"),
            "mean_rca_accuracy_on_prediction_records": mean(metrics, "rca_accuracy_on_prediction_records"),
            "mean_handover_instability_recall": mean(metrics, "handover_instability_recall"),
            "mean_qos_session_degradation_recall": mean(metrics, "qos_session_degradation_recall"),
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
