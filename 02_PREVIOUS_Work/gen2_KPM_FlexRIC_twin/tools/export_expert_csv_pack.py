from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export current project evidence JSON files into expert-friendly CSV tables.")
    parser.add_argument("--output-dir", default="outputs/expert_csv")
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    index_rows: list[dict[str, str]] = []

    def add_index(file_name: str, source: str, purpose: str) -> None:
        index_rows.append({"csv_file": file_name, "source": source, "purpose": purpose})

    export_flexric_report(output_dir, add_index)
    export_controlled_faults(output_dir, add_index)
    export_balanced_benchmark(output_dir, add_index)
    export_support_benchmarks(output_dir, add_index)
    export_model_inventory(output_dir, add_index)
    export_json_scalar_catalog(output_dir, add_index)

    write_csv(output_dir / "00_EXPERT_CSV_INDEX.csv", index_rows, ["csv_file", "source", "purpose"])


def export_flexric_report(output_dir: Path, add_index: Any) -> None:
    source = ROOT / "outputs/reports/flexric_kpm_30min.json"
    data = read_json(source)
    summary = data.get("jsonl_decision_summary", {})
    sqlite = data.get("sqlite_summary", {})
    file_status = data.get("file_status", {})

    rows = [
        {"metric": "report_version", "value": data.get("version", "")},
        {"metric": "jsonl_decision_records", "value": summary.get("records", "")},
        {"metric": "jsonl_anomaly_records", "value": summary.get("anomaly_records", "")},
        {"metric": "jsonl_approved_records", "value": summary.get("approved_records", "")},
        {"metric": "sqlite_decision_records", "value": sqlite.get("decision_records", "")},
        {"metric": "sqlite_feature_rows", "value": sqlite.get("feature_rows", "")},
        {"metric": "sqlite_data_quality_events", "value": sqlite.get("data_quality_events", "")},
        {"metric": "honest_interpretation", "value": data.get("honest_interpretation", "")},
    ]
    write_csv(output_dir / "flexric_30min_report_summary.csv", rows, ["metric", "value"])
    add_index("flexric_30min_report_summary.csv", str(source.relative_to(ROOT)), "Top-level FlexRIC 30-minute evidence summary.")

    count_rows: list[dict[str, Any]] = []
    for group_name in [
        "root_cause_counts",
        "healing_action_counts",
        "automation_decision_counts",
        "ric_control_type_counts",
    ]:
        for label, count in dict(summary.get(group_name, {})).items():
            count_rows.append({"source": "jsonl_decision_summary", "group": group_name, "label": label, "count": count})
    for group_name in ["root_cause_counts", "healing_action_counts"]:
        for label, count in dict(sqlite.get(group_name, {})).items():
            count_rows.append({"source": "sqlite_summary", "group": group_name, "label": label, "count": count})
    write_csv(output_dir / "flexric_30min_report_counts.csv", count_rows, ["source", "group", "label", "count"])
    add_index("flexric_30min_report_counts.csv", str(source.relative_to(ROOT)), "Root-cause, healing, automation, and RIC output counts.")

    file_rows = []
    for key, status in dict(file_status).items():
        file_rows.append(
            {
                "artifact": key,
                "available": status.get("available", ""),
                "path": status.get("path", ""),
                "bytes": status.get("bytes", ""),
            }
        )
    write_csv(output_dir / "flexric_30min_file_status.csv", file_rows, ["artifact", "available", "path", "bytes"])
    add_index("flexric_30min_file_status.csv", str(source.relative_to(ROOT)), "File availability and sizes for final FlexRIC run artifacts.")


def export_controlled_faults(output_dir: Path, add_index: Any) -> None:
    source = ROOT / "outputs/evidence/controlled_fault_evaluation.json"
    data = read_json(source)
    confusion = data.get("confusion_matrix", {})
    rows = [
        {"metric": "run_name", "value": data.get("run_name", "")},
        {"metric": "records", "value": data.get("records", "")},
        {"metric": "fault_windows", "value": data.get("fault_windows", "")},
        {"metric": "true_positives", "value": confusion.get("tp", "")},
        {"metric": "false_positives", "value": confusion.get("fp", "")},
        {"metric": "true_negatives", "value": confusion.get("tn", "")},
        {"metric": "false_negatives", "value": confusion.get("fn", "")},
        {"metric": "precision", "value": data.get("precision", "")},
        {"metric": "recall", "value": data.get("recall", "")},
        {"metric": "f1_score", "value": data.get("f1_score", "")},
        {"metric": "false_positive_rate", "value": data.get("false_positive_rate", "")},
        {"metric": "false_negative_rate", "value": data.get("false_negative_rate", "")},
        {"metric": "rca_accuracy_when_detected", "value": data.get("rca_accuracy_when_detected", "")},
        {"metric": "healing_accuracy_when_detected", "value": data.get("healing_accuracy_when_detected", "")},
        {"metric": "honest_interpretation", "value": data.get("honest_interpretation", "")},
    ]
    write_csv(output_dir / "controlled_fault_summary.csv", rows, ["metric", "value"])
    add_index("controlled_fault_summary.csv", str(source.relative_to(ROOT)), "Controlled timestamped fault-injection headline metrics.")

    window_fields = [
        "window_id",
        "fault_type",
        "start_s",
        "end_s",
        "duration_s",
        "detected_rows",
        "detection_coverage",
        "first_detection_s",
        "detection_latency_s",
        "rca_accuracy_when_detected",
        "healing_accuracy_when_detected",
    ]
    write_csv(output_dir / "controlled_fault_window_results.csv", data.get("window_results", []), window_fields)
    add_index("controlled_fault_window_results.csv", str(source.relative_to(ROOT)), "Per-fault-window detection, RCA, and healing results.")

    for key, file_name, purpose in [
        ("expected_fault_counts", "controlled_fault_expected_fault_counts.csv", "Expected answer-key fault distribution."),
        ("predicted_root_cause_counts", "controlled_fault_predicted_root_cause_counts.csv", "Predicted RCA distribution during controlled fault injection."),
    ]:
        rows = [{"label": label, "count": count} for label, count in dict(data.get(key, {})).items()]
        write_csv(output_dir / file_name, rows, ["label", "count"])
        add_index(file_name, str(source.relative_to(ROOT)), purpose)


def export_balanced_benchmark(output_dir: Path, add_index: Any) -> None:
    source = ROOT / "outputs/benchmarks/flexric_kpm_30min_ml_benchmark_balanced.json"
    data = read_json(source)
    profile = data.get("dataset_profile", {})

    split_rows = []
    for split in ["train", "test"]:
        item = profile.get(split, {})
        split_rows.append(
            {
                "split": split,
                "records": item.get("records", ""),
                "fault_records": item.get("fault_records", ""),
                "normal_records": item.get("normal_records", ""),
                "service_counts": json.dumps(item.get("service_counts", {}), sort_keys=True),
                "fault_counts": json.dumps(item.get("fault_counts", {}), sort_keys=True),
            }
        )
    write_csv(
        output_dir / "flexric_30min_balanced_benchmark_split.csv",
        split_rows,
        ["split", "records", "fault_records", "normal_records", "service_counts", "fault_counts"],
    )
    add_index("flexric_30min_balanced_benchmark_split.csv", str(source.relative_to(ROOT)), "Train/test profile for the balanced benchmark.")

    metric_rows = []
    feature_rows = []
    for benchmark in data.get("benchmarks", []):
        if "features" in benchmark:
            feature_rows.extend(
                {"model": benchmark.get("name", "feature_set"), "feature": feature}
                for feature in benchmark.get("features", [])
            )
            continue
        confusion = benchmark.get("confusion_matrix", {})
        metric_rows.append(
            {
                "model": benchmark.get("name", ""),
                "records": benchmark.get("records", ""),
                "tp": confusion.get("tp", ""),
                "fp": confusion.get("fp", ""),
                "fn": confusion.get("fn", ""),
                "tn": confusion.get("tn", ""),
                "precision": benchmark.get("precision", ""),
                "recall": benchmark.get("recall", ""),
                "f1_score": benchmark.get("f1_score", ""),
                "false_positive_rate": benchmark.get("false_positive_rate", ""),
                "false_negative_rate": benchmark.get("false_negative_rate", ""),
                "rca_accuracy_on_fault_predictions": benchmark.get("rca_accuracy_on_fault_predictions", ""),
                "predicted_fault_rate": benchmark.get("predicted_fault_rate", ""),
            }
        )
    metric_fields = [
        "model",
        "records",
        "tp",
        "fp",
        "fn",
        "tn",
        "precision",
        "recall",
        "f1_score",
        "false_positive_rate",
        "false_negative_rate",
        "rca_accuracy_on_fault_predictions",
        "predicted_fault_rate",
    ]
    write_csv(output_dir / "flexric_30min_balanced_benchmark_model_metrics.csv", metric_rows, metric_fields)
    add_index("flexric_30min_balanced_benchmark_model_metrics.csv", str(source.relative_to(ROOT)), "Model comparison table used by the final presentation.")
    write_csv(output_dir / "flexric_30min_balanced_benchmark_features.csv", feature_rows, ["model", "feature"])
    add_index("flexric_30min_balanced_benchmark_features.csv", str(source.relative_to(ROOT)), "Feature list used by the benchmark models.")


def export_support_benchmarks(output_dir: Path, add_index: Any) -> None:
    sources = sorted((ROOT / "outputs/benchmarks").glob("*.json"))
    rows = []
    for source in sources:
        data = read_json(source)
        profile = data.get("dataset_profile", {})
        rows.append(
            {
                "benchmark_file": str(source.relative_to(ROOT)),
                "version": data.get("version", ""),
                "input": data.get("input", ""),
                "purpose": data.get("purpose", ""),
                "rows_evaluated": data.get("rows_evaluated", data.get("rows_loaded", "")),
                "records": profile.get("records", ""),
                "fault_records": profile.get("fault_records", ""),
                "normal_records": profile.get("normal_records", ""),
                "service_class_counts": json.dumps(profile.get("service_class_counts", profile.get("service_counts", {})), sort_keys=True),
                "fault_type_counts": json.dumps(profile.get("fault_type_counts", profile.get("fault_counts", {})), sort_keys=True),
            }
        )
    fields = [
        "benchmark_file",
        "version",
        "input",
        "purpose",
        "rows_evaluated",
        "records",
        "fault_records",
        "normal_records",
        "service_class_counts",
        "fault_type_counts",
    ]
    write_csv(output_dir / "supporting_benchmark_inventory.csv", rows, fields)
    add_index("supporting_benchmark_inventory.csv", "outputs/benchmarks/*.json", "Inventory of current benchmark JSONs converted to a single expert CSV.")


def export_model_inventory(output_dir: Path, add_index: Any) -> None:
    sources = sorted((ROOT / "outputs/models").glob("*.json"))
    rows = []
    for source in sources:
        data = read_json(source)
        feature_stats = data.get("feature_stats", {})
        root_counts = data.get("root_cause_counts", {})
        rows.append(
            {
                "model_file": str(source.relative_to(ROOT)),
                "type": data.get("type", ""),
                "feature_count": len(data.get("features", [])),
                "feature_stats_groups": len(feature_stats) if isinstance(feature_stats, dict) else "",
                "warmup": data.get("warmup", ""),
                "anomaly_z": data.get("anomaly_z", ""),
                "root_cause_counts": json.dumps(root_counts, sort_keys=True),
            }
        )
    write_csv(
        output_dir / "model_inventory.csv",
        rows,
        ["model_file", "type", "feature_count", "feature_stats_groups", "warmup", "anomaly_z", "root_cause_counts"],
    )
    add_index("model_inventory.csv", "outputs/models/*.json", "Model metadata summary for expert review without opening raw model JSON.")


def export_json_scalar_catalog(output_dir: Path, add_index: Any) -> None:
    rows = []
    for folder in ["outputs/reports", "outputs/evidence", "outputs/benchmarks", "outputs/models"]:
        for source in sorted((ROOT / folder).glob("*.json")):
            data = read_json(source)
            for path, value in flatten_scalars(data):
                rows.append({"source_file": str(source.relative_to(ROOT)), "json_path": path, "value": value})
    write_csv(output_dir / "all_current_json_scalar_catalog.csv", rows, ["source_file", "json_path", "value"])
    add_index("all_current_json_scalar_catalog.csv", "current visible output JSON files", "Flat scalar catalog for traceability from JSON evidence to CSV.")


def flatten_scalars(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten_scalars(item, new_prefix)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            new_prefix = f"{prefix}[{index}]"
            yield from flatten_scalars(item, new_prefix)
    else:
        yield prefix, value


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
