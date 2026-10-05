from __future__ import annotations

import json
from pathlib import Path


BENCHMARKS = [
    Path("outputs/benchmarks/open_ran_kpm_heldout_benchmark.json"),
    Path("outputs/benchmarks/open_ran_kpm_heldout_cluster2_slicing4_sched0.json"),
    Path("outputs/benchmarks/open_ran_kpm_heldout_cluster1_slicing2_sched2.json"),
]


def main() -> None:
    rows = []
    for path in BENCHMARKS:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        holdout = data["holdout"]
        metrics = data["test_metrics"]
        rows.append(
            {
                "file": str(path),
                "holdout": f"{holdout['cluster']}/{holdout['slicing']}/{holdout['scheduling']}",
                "test_records": data["test_profile"]["records"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "false_positive_rate": metrics["false_positive_rate"],
                "rca_accuracy": metrics["rca_accuracy_on_prediction_records"],
            }
        )

    summary = {
        "benchmarks": rows,
        "mean_precision": avg(rows, "precision"),
        "mean_recall": avg(rows, "recall"),
        "mean_f1": avg(rows, "f1_score"),
        "mean_rca_accuracy": avg(rows, "rca_accuracy"),
        "interpretation": (
            "Fault detection generalizes strongly across held-out Open RAN contexts. "
            "RCA is usually strong but drops on at least one held-out context, so the next tuning target is RCA calibration, not anomaly detection."
        ),
    }
    output = Path("outputs/benchmarks/open_ran_kpm_heldout_summary.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def avg(rows: list[dict[str, object]], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(float(row[key]) for row in rows) / len(rows), 4)


if __name__ == "__main__":
    main()
