from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oran_twin.engine import OranDecisionEngine, normalize_engine_row
from oran_twin.self_learning import FEATURES, OnlineSelfLearningModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare local ML models with strict train/test reporting.")
    parser.add_argument("--input", default="data/training/open_ran_kpm_training_dataset.csv")
    parser.add_argument("--output", default="outputs/benchmarks/ml_model_comparison_v2.json")
    parser.add_argument("--max-rows", type=int, default=25000)
    parser.add_argument("--holdout-column", default="cluster", help="Use a metadata column such as cluster, slicing, scheduling, area_persona.")
    parser.add_argument("--holdout-value", default="", help="Optional exact value. If empty, the least-common non-empty value is held out.")
    parser.add_argument(
        "--include-normal-holdout",
        action="store_true",
        help="When holding out a fault scenario, also place normal rows in test so FPR/TN metrics are meaningful.",
    )
    args = parser.parse_args()

    rows, raw_rows = load_rows(Path(args.input), args.max_rows)
    train_idx, test_idx, split = group_holdout_split(
        raw_rows,
        args.holdout_column,
        args.holdout_value,
        include_normal_holdout=args.include_normal_holdout,
    )
    if not train_idx or not test_idx:
        train_idx, test_idx, split = deterministic_split(len(rows))

    train_rows = [rows[i] for i in train_idx]
    test_rows = [rows[i] for i in test_idx]
    result = {
        "version": "ml_benchmark_v2",
        "input": args.input,
        "rows_loaded": len(rows),
        "split": split,
        "dataset_profile": {
            "train": profile(train_rows),
            "test": profile(test_rows),
        },
        "benchmarks": [],
        "limitations": [
            "Labels are explicit only when provided by source; otherwise weak labels may inflate scores.",
            "Open RAN KPM rows are strong for replay benchmarking but are not equivalent to operator production fault truth.",
            "Models are local CPU models; deep sequence models need longer continuous streams before they are meaningful.",
        ],
    }

    result["benchmarks"].append(benchmark_online_self_learning(train_rows, test_rows))
    result["benchmarks"].append(benchmark_decision_engine(test_rows))
    result["benchmarks"].extend(benchmark_sklearn_models(train_rows, test_rows))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def load_rows(path: Path, max_rows: int) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    rows: list[dict[str, object]] = []
    raw_rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            raw_rows.append(raw)
            rows.append(normalize_engine_row(raw))
            if len(rows) >= max_rows:
                break
    return rows, raw_rows


def group_holdout_split(
    raw_rows: list[dict[str, str]],
    column: str,
    value: str,
    *,
    include_normal_holdout: bool = False,
) -> tuple[list[int], list[int], dict[str, object]]:
    values = [row.get(column, "") for row in raw_rows if row.get(column, "")]
    if not values:
        return [], [], {"type": "unavailable_group_holdout", "column": column}
    chosen = value or Counter(values).most_common()[-1][0]
    test_idx = [idx for idx, row in enumerate(raw_rows) if row.get(column, "") == chosen]
    normal_holdout_idx: list[int] = []
    if include_normal_holdout:
        normal_candidates = [
            idx
            for idx, row in enumerate(raw_rows)
            if is_normal_raw_row(row) and row.get(column, "") != chosen
        ]
        normal_holdout_count = min(len(test_idx), max(1, len(normal_candidates) // 2)) if normal_candidates else 0
        normal_holdout_idx = normal_candidates[:normal_holdout_count]
        test_idx = sorted(set(test_idx + normal_holdout_idx))
    train_idx = [idx for idx in range(len(raw_rows)) if idx not in set(test_idx)]
    if not train_idx or not test_idx:
        return [], [], {"type": "invalid_group_holdout", "column": column, "value": chosen}
    return train_idx, test_idx, {
        "type": "group_holdout",
        "column": column,
        "value": chosen,
        "normal_holdout_records": len(normal_holdout_idx),
    }


def is_normal_raw_row(row: dict[str, str]) -> bool:
    fault_active = str(row.get("fault_active", "")).strip().lower()
    fault_type = str(row.get("fault_type", "")).strip().lower()
    return fault_active in {"", "0", "false", "no"} or fault_type == "normal"


def deterministic_split(total: int) -> tuple[list[int], list[int], dict[str, object]]:
    test_idx = [idx for idx in range(total) if idx % 5 == 0]
    test = set(test_idx)
    train_idx = [idx for idx in range(total) if idx not in test]
    return train_idx, test_idx, {"type": "deterministic_80_20_modulo"}


def benchmark_online_self_learning(train_rows: list[dict[str, object]], test_rows: list[dict[str, object]]) -> dict[str, object]:
    model = OnlineSelfLearningModel()
    for row in train_rows:
        model.learn(row)
    predictions = []
    rca_predictions = []
    for row in test_rows:
        assessment = model.assess(row, learn=False)
        predictions.append(bool(assessment.anomaly_detected))
        rca_predictions.append(assessment.rca_prediction)
    return summarize_binary_and_rca("online_self_learning_v1", test_rows, predictions, rca_predictions)


def benchmark_decision_engine(test_rows: list[dict[str, object]]) -> dict[str, object]:
    engine = OranDecisionEngine(self_learning_model_path="outputs/models/phy_odu_virtual_ran_self_learning_model.json")
    predictions = []
    rca_predictions = []
    for row in test_rows[: min(6000, len(test_rows))]:
        decision = engine.assess(row)
        predictions.append(bool(decision["anomaly_detected"]))
        rca_predictions.append(str(decision["root_cause"]))
    return summarize_binary_and_rca("full_guarded_decision_engine_sample", test_rows[: len(predictions)], predictions, rca_predictions)


def benchmark_sklearn_models(train_rows: list[dict[str, object]], test_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    try:
        from sklearn.ensemble import GradientBoostingClassifier, IsolationForest, RandomForestClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except Exception as exc:  # pragma: no cover
        return [{"name": "sklearn_models_unavailable", "error": str(exc)}]

    x_train = matrix(train_rows)
    x_test = matrix(test_rows)
    y_train = [int(bool(row["fault_active"])) for row in train_rows]
    y_test = [int(bool(row["fault_active"])) for row in test_rows]
    rca_train = [str(row["fault_type"]).split("+", 1)[0] for row in train_rows]

    normal_train = [features for features, label in zip(x_train, y_train) if label == 0]
    isolation = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), IsolationForest(n_estimators=180, contamination=0.12, random_state=2026))
    isolation.fit(normal_train or x_train)
    iso_pred = [pred == -1 for pred in isolation.predict(x_test)]

    rf = make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(n_estimators=220, min_samples_leaf=4, class_weight="balanced", random_state=2026, n_jobs=1))
    rf.fit(x_train, y_train)
    rf_pred = [bool(item) for item in rf.predict(x_test)]

    gb = make_pipeline(SimpleImputer(strategy="median"), GradientBoostingClassifier(n_estimators=140, learning_rate=0.06, max_depth=3, random_state=2026))
    gb.fit(x_train, y_train)
    gb_pred = [bool(item) for item in gb.predict(x_test)]

    rca_rf = make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(n_estimators=240, min_samples_leaf=3, class_weight="balanced", random_state=2027, n_jobs=1))
    fault_train_x = [features for features, row in zip(x_train, train_rows) if bool(row["fault_active"])]
    fault_train_y = [label for label, row in zip(rca_train, train_rows) if bool(row["fault_active"])]
    if fault_train_x and len(set(fault_train_y)) > 1:
        rca_rf.fit(fault_train_x, fault_train_y)
        rca_pred = [str(item) for item in rca_rf.predict(x_test)]
    else:
        rca_pred = ["unknown"] * len(test_rows)

    return [
        summarize_binary_and_rca("isolation_forest_unsupervised", test_rows, iso_pred, ["unknown"] * len(test_rows)),
        summarize_binary_and_rca("random_forest_supervised", test_rows, rf_pred, rca_pred),
        summarize_binary_and_rca("gradient_boosting_supervised", test_rows, gb_pred, ["unknown"] * len(test_rows)),
        {"name": "sklearn_feature_set", "features": FEATURES},
    ]


def matrix(rows: list[dict[str, object]]) -> list[list[float]]:
    return [[float(row.get(feature, 0.0) or 0.0) for feature in FEATURES] for row in rows]


def summarize_binary_and_rca(
    name: str,
    rows: list[dict[str, object]],
    predictions: list[bool],
    rca_predictions: list[str],
) -> dict[str, object]:
    tp = fp = fn = tn = 0
    rca_total = 0
    rca_correct = 0
    actual_faults = [bool(row["fault_active"]) for row in rows]
    for row, predicted, rca in zip(rows, predictions, rca_predictions):
        actual = bool(row["fault_active"])
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        else:
            tn += 1
        if actual and rca not in {"unknown", "normal"}:
            rca_total += 1
            if rca == str(row["fault_type"]).split("+", 1)[0]:
                rca_correct += 1

    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    return {
        "name": name,
        "records": len(rows),
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": precision,
        "recall": recall,
        "f1_score": round(2 * precision * recall / max(0.0001, precision + recall), 4),
        "false_positive_rate": ratio(fp, fp + tn),
        "false_negative_rate": ratio(fn, fn + tp),
        "rca_accuracy_on_fault_predictions": ratio(rca_correct, rca_total),
        "predicted_fault_rate": ratio(sum(1 for item in predictions if item), len(predictions)),
    }


def profile(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "records": len(rows),
        "fault_records": sum(1 for row in rows if bool(row["fault_active"])),
        "normal_records": sum(1 for row in rows if not bool(row["fault_active"])),
        "service_counts": dict(Counter(str(row["service_class"]) for row in rows)),
        "fault_counts": dict(Counter(str(row["fault_type"]) for row in rows)),
    }


def ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


if __name__ == "__main__":
    main()
