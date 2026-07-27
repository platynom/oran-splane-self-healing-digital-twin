from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "outputs" / "EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED"
SHOW = PACK / "01_show_first"


def main() -> None:
    SHOW.mkdir(parents=True, exist_ok=True)
    copy_presentation()
    write_index()
    write_flexric_summary()
    write_benchmark_metrics()
    write_controlled_faults()
    copy_decisions()
    write_reconciliation()
    write_column_guide()
    write_readme()


def copy_presentation() -> None:
    source = ROOT / "outputs" / "presentations" / "O-RAN_AI_Native_Self_Healing_Final_Expert_Review.pptx"
    if source.exists():
        shutil.copy2(source, SHOW / "01_FINAL_PRESENTATION.pptx")


def write_index() -> None:
    rows = [
        ["01_FINAL_PRESENTATION.pptx", "outputs/presentations/O-RAN_AI_Native_Self_Healing_Final_Expert_Review.pptx", "Open this first for the expert review story."],
        ["02_EXPERT_CSV_INDEX.csv", "this pack", "Index of every CSV in the show-first folder."],
        ["03_FLEXRIC_30MIN_REPORT_SUMMARY.csv", "outputs/reports/flexric_kpm_30min.json + syncfixed CSV counts", "Headline count summary after parser sync fix."],
        ["04_MODEL_BENCHMARK_METRICS.csv", "outputs/benchmarks/flexric_kpm_30min_ml_benchmark_balanced_syncfixed.json", "Model comparison on the corrected benchmark input."],
        ["05_CONTROLLED_FAULT_SUMMARY.csv", "outputs/evidence/controlled_fault_evaluation_syncfixed.json", "Controlled fault-injection headline detection/RCA/healing metrics."],
        ["06_CONTROLLED_FAULT_WINDOW_RESULTS.csv", "outputs/evidence/controlled_fault_evaluation_syncfixed.json", "Per-fault-window detection, RCA, and healing accuracy."],
        ["07_FULL_FLEXRIC_DECISION_ROWS.csv", "outputs/evidence/flexric_kpm_30min_decisions.csv", "All 71,900 final decision rows exported from JSONL."],
        ["08_PIPELINE_ROW_COUNT_RECONCILIATION.csv", "current generated evidence", "Explains why 71,900, 431,400, and 6,250 are different but synced."],
        ["09_CSV_COLUMN_GUIDE.csv", "this pack", "Column-by-column meaning for every expert CSV."],
    ]
    write_csv(SHOW / "02_EXPERT_CSV_INDEX.csv", ["csv_file", "source", "purpose"], rows)


def write_flexric_summary() -> None:
    report = read_json(ROOT / "outputs" / "reports" / "flexric_kpm_30min.json")
    summary = report.get("jsonl_decision_summary", {})
    sqlite = report.get("sqlite_summary", {})
    rows = [
        ["report_version", report.get("version", "")],
        ["decision_records", summary.get("records", "")],
        ["normalized_kpm_rows_syncfixed", count_data_rows(ROOT / "outputs" / "flexric_xapp_longrun_normalized_syncfixed.csv")],
        ["augmented_training_rows_syncfixed", count_data_rows(ROOT / "data" / "training" / "flexric_kpm_30min_augmented_training_syncfixed.csv")],
        ["anomaly_records", summary.get("anomaly_records", "")],
        ["approved_records", summary.get("approved_records", "")],
        ["sqlite_decision_records_for_run", sqlite.get("decision_records", "")],
        ["sqlite_feature_rows_cumulative", sqlite.get("feature_rows", "")],
        ["sqlite_data_quality_events", sqlite.get("data_quality_events", "")],
        ["honest_interpretation", "FlexRIC decisions are executable lab/e2-kpm evidence. Training rows include controlled synthetic fault augmentations; they are not operator production fault truth."],
    ]
    write_csv(SHOW / "03_FLEXRIC_30MIN_REPORT_SUMMARY.csv", ["metric", "value"], rows)


def write_benchmark_metrics() -> None:
    data = read_json(ROOT / "outputs" / "benchmarks" / "flexric_kpm_30min_ml_benchmark_balanced_syncfixed.json")
    rows = []
    for benchmark in data.get("benchmarks", []):
        if "features" in benchmark:
            continue
        confusion = benchmark.get("confusion_matrix", {})
        rows.append([
            benchmark.get("name", ""),
            benchmark.get("records", ""),
            confusion.get("tp", ""),
            confusion.get("fp", ""),
            confusion.get("fn", ""),
            confusion.get("tn", ""),
            benchmark.get("precision", ""),
            benchmark.get("recall", ""),
            benchmark.get("f1_score", ""),
            benchmark.get("false_positive_rate", ""),
            benchmark.get("false_negative_rate", ""),
            benchmark.get("rca_accuracy_on_fault_predictions", ""),
            benchmark.get("predicted_fault_rate", ""),
        ])
    fields = ["model", "records", "tp", "fp", "fn", "tn", "precision", "recall", "f1_score", "false_positive_rate", "false_negative_rate", "rca_accuracy_on_fault_predictions", "predicted_fault_rate"]
    write_csv(SHOW / "04_MODEL_BENCHMARK_METRICS.csv", fields, rows)


def write_controlled_faults() -> None:
    data = read_json(ROOT / "outputs" / "evidence" / "controlled_fault_evaluation_syncfixed.json")
    confusion = data.get("confusion_matrix", {})
    rows = [
        ["run_name", data.get("run_name", "")],
        ["records", data.get("records", "")],
        ["fault_windows", data.get("fault_windows", "")],
        ["true_positives", confusion.get("tp", "")],
        ["false_positives", confusion.get("fp", "")],
        ["true_negatives", confusion.get("tn", "")],
        ["false_negatives", confusion.get("fn", "")],
        ["precision", data.get("precision", "")],
        ["recall", data.get("recall", "")],
        ["f1_score", data.get("f1_score", "")],
        ["false_positive_rate", data.get("false_positive_rate", "")],
        ["false_negative_rate", data.get("false_negative_rate", "")],
        ["rca_accuracy_when_detected", data.get("rca_accuracy_when_detected", "")],
        ["healing_accuracy_when_detected", data.get("healing_accuracy_when_detected", "")],
        ["honest_interpretation", data.get("honest_interpretation", "")],
    ]
    write_csv(SHOW / "05_CONTROLLED_FAULT_SUMMARY.csv", ["metric", "value"], rows)
    fields = ["window_id", "fault_type", "start_s", "end_s", "duration_s", "detected_rows", "detection_coverage", "first_detection_s", "detection_latency_s", "rca_accuracy_when_detected", "healing_accuracy_when_detected"]
    write_csv(SHOW / "06_CONTROLLED_FAULT_WINDOW_RESULTS.csv", fields, [[item.get(field, "") for field in fields] for item in data.get("window_results", [])])


def copy_decisions() -> None:
    source = ROOT / "outputs" / "evidence" / "flexric_kpm_30min_decisions.csv"
    if source.exists():
        shutil.copy2(source, SHOW / "07_FULL_FLEXRIC_DECISION_ROWS.csv")


def write_reconciliation() -> None:
    rows = [
        ["FlexRIC decision export", "outputs/evidence/flexric_kpm_30min_decisions.csv", count_data_rows(ROOT / "outputs" / "evidence" / "flexric_kpm_30min_decisions.csv"), "One final row per decision emitted by the self-healing engine.", "This is the 71,900 number."],
        ["Corrected normalized KPM CSV", "outputs/flexric_xapp_longrun_normalized_syncfixed.csv", count_data_rows(ROOT / "outputs" / "flexric_xapp_longrun_normalized_syncfixed.csv"), "One parsed KPI row after ignoring internal FlexRIC indication-latency logs.", "Now matches the 71,900 decision rows."],
        ["Old normalized KPM CSV", "outputs/flexric_xapp_longrun_normalized.csv", count_data_rows(ROOT / "outputs" / "flexric_xapp_longrun_normalized.csv"), "Previous parser output before sync fix.", "Had 1,792 extra internal latency rows, so do not use this for expert proof."],
        ["Corrected augmented training CSV", "data/training/flexric_kpm_30min_augmented_training_syncfixed.csv", count_data_rows(ROOT / "data" / "training" / "flexric_kpm_30min_augmented_training_syncfixed.csv"), "Each base row is expanded into normal plus five controlled fault scenarios.", "71,900 x 6 = 431,400 rows."],
        ["Old augmented training CSV", "data/training/flexric_kpm_30min_augmented_training.csv", count_data_rows(ROOT / "data" / "training" / "flexric_kpm_30min_augmented_training.csv"), "Previous training file before sync fix.", "73,692 x 6 = 442,152 rows; superseded by syncfixed file."],
        ["Benchmark loaded rows", "outputs/benchmarks/flexric_kpm_30min_ml_benchmark_balanced_syncfixed.json", 25000, "Benchmark intentionally samples 25,000 rows for local CPU model comparison.", "This is a benchmark sample, not the full training file."],
        ["Benchmark test rows", "outputs/benchmarks/flexric_kpm_30min_ml_benchmark_balanced_syncfixed.json", 6250, "Held-out test split: radio_link_degradation plus normal holdout rows.", "This is why Excel shows 6,250 in the model benchmark."],
        ["Controlled fault evaluation rows", "outputs/evidence/controlled_fault_evaluation_syncfixed.json", 2400, "Short scheduled replay with known answer-key fault windows.", "Used to measure detection/RCA/healing correctness, not full model training."],
        ["SQLite feature rows", "outputs/oran_twin.sqlite", 87927, "Cumulative feature-row store across live metric ingestion.", "Do not compare directly to only the 30-minute decision CSV."],
    ]
    write_csv(SHOW / "08_PIPELINE_ROW_COUNT_RECONCILIATION.csv", ["stage", "file", "records", "meaning", "why_number_differs"], rows)


def write_column_guide() -> None:
    guide = {
        "02_EXPERT_CSV_INDEX.csv": {
            "csv_file": "Name of the CSV/PPTX artifact in the show-first folder.",
            "source": "Original project file or evidence source used to create it.",
            "purpose": "Why this artifact exists and when to open it.",
        },
        "03_FLEXRIC_30MIN_REPORT_SUMMARY.csv": {
            "metric": "Named headline evidence value.",
            "value": "Value for that metric.",
        },
        "04_MODEL_BENCHMARK_METRICS.csv": {
            "model": "Model or engine being compared.",
            "records": "Rows evaluated by that model in the test split.",
            "tp": "Fault rows correctly predicted as faults.",
            "fp": "Normal rows incorrectly predicted as faults.",
            "fn": "Fault rows missed as normal.",
            "tn": "Normal rows correctly left normal.",
            "precision": "TP / (TP + FP), how clean the positive alerts are.",
            "recall": "TP / (TP + FN), how many faults were caught.",
            "f1_score": "Harmonic mean of precision and recall.",
            "false_positive_rate": "FP / (FP + TN), normal rows falsely alerted.",
            "false_negative_rate": "FN / (FN + TP), fault rows missed.",
            "rca_accuracy_on_fault_predictions": "Among detected faults, how often the root cause label was correct.",
            "predicted_fault_rate": "Fraction of evaluated rows predicted as faulty.",
        },
        "05_CONTROLLED_FAULT_SUMMARY.csv": {
            "metric": "Controlled replay metric name.",
            "value": "Metric value.",
        },
        "06_CONTROLLED_FAULT_WINDOW_RESULTS.csv": {
            "window_id": "Fault-window identifier.",
            "fault_type": "Expected injected fault class.",
            "start_s": "Fault start time in replay seconds.",
            "end_s": "Fault end time in replay seconds.",
            "duration_s": "Fault duration in seconds.",
            "detected_rows": "Rows detected as anomalous inside the window.",
            "detection_coverage": "Detected rows divided by total fault-window rows.",
            "first_detection_s": "First replay second where the fault was detected.",
            "detection_latency_s": "Delay from fault start to first detection.",
            "rca_accuracy_when_detected": "Correct root-cause fraction inside that fault window.",
            "healing_accuracy_when_detected": "Correct healing-action fraction inside that fault window.",
        },
        "07_FULL_FLEXRIC_DECISION_ROWS.csv": {
            "row_id": "Sequential exported decision row number.",
            "cell_id": "Cell identifier used by the local pipeline.",
            "service_class": "Slice/service class attached to this run.",
            "anomaly_detected": "Whether the engine detected abnormal behavior.",
            "risk_score": "Engine risk score for the row.",
            "root_cause": "Predicted root cause.",
            "healing_action": "Recommended or selected healing action.",
            "automation_decision": "Safety decision such as monitor_only or allow_with_monitoring.",
            "approved": "Whether the guarded automation decision was approved.",
            "ric_control_type": "RIC output type, for example none or A1 policy.",
            "ric_policy": "Policy payload identifier/name when applicable.",
            "ric_intent": "High-level RIC intent when applicable.",
            "reason_count": "Number of reasons attached to the decision.",
            "reasons": "Semicolon-style evidence reasons behind the decision.",
        },
        "08_PIPELINE_ROW_COUNT_RECONCILIATION.csv": {
            "stage": "Pipeline stage where a count appears.",
            "file": "File containing that count.",
            "records": "Row/record count.",
            "meaning": "What one record means at that stage.",
            "why_number_differs": "Why this count can differ from the other files.",
        },
    }
    rows = []
    for file_name, columns in guide.items():
        for column, meaning in columns.items():
            rows.append([file_name, column, meaning])
    write_csv(SHOW / "09_CSV_COLUMN_GUIDE.csv", ["csv_file", "column", "meaning"], rows)


def write_readme() -> None:
    text = """Open 01_show_first/01_FINAL_PRESENTATION.pptx first.

Use 08_PIPELINE_ROW_COUNT_RECONCILIATION.csv to explain the row-count differences:
71,900 = corrected FlexRIC decision/KPM rows.
431,400 = corrected augmented training rows, because 71,900 base rows x 6 scenarios.
6,250 = benchmark test split only, not the full dataset.

The old 442,152-row training CSV is superseded because it included 1,792 internal FlexRIC indication-latency rows before parser cleanup.
"""
    (PACK / "00_OPEN_FIRST_README.txt").write_text(text, encoding="utf-8")


def count_data_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, fieldnames: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


if __name__ == "__main__":
    main()
