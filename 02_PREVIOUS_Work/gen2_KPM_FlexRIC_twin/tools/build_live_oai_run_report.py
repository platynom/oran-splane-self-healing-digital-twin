from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a report for a live OAI/FlexRIC telemetry run.")
    parser.add_argument("--db", default="outputs/oran_twin.sqlite")
    parser.add_argument("--decisions", default="outputs/live_oai_decisions.jsonl")
    parser.add_argument("--metrics", default="data/telemetry/raw/live_oai_metrics.log")
    parser.add_argument("--run-name", default="live_oai_stream")
    parser.add_argument("--output", default="outputs/reports/live_oai_run_report.json")
    args = parser.parse_args()

    report = build_report(
        db=Path(args.db),
        decisions=Path(args.decisions),
        metrics=Path(args.metrics),
        run_name=args.run_name,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    output.with_suffix(".md").write_text(to_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


def build_report(*, db: Path, decisions: Path, metrics: Path, run_name: str) -> dict[str, Any]:
    decision_rows = read_jsonl(decisions)
    sqlite_summary = read_sqlite_summary(db, run_name)
    return {
        "version": "v1.9",
        "purpose": "Summarize live OAI/FlexRIC telemetry ingestion into the self-healing decision engine.",
        "inputs": {
            "database": str(db),
            "decisions_jsonl": str(decisions),
            "metrics_log": str(metrics),
        },
        "file_status": {
            "database": file_status(db),
            "decisions_jsonl": file_status(decisions),
            "metrics_log": file_status(metrics),
        },
        "jsonl_decision_summary": summarize_decisions(decision_rows),
        "sqlite_summary": sqlite_summary,
        "honest_interpretation": (
            "This report proves that live/lab telemetry rows reached the local engine and were stored. "
            "It does not prove operator-grade production performance unless the source is a sustained real OAI/FlexRIC run with validated fault truth."
        ),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def summarize_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "records": len(rows),
        "anomaly_records": sum(1 for row in rows if bool(row.get("anomaly_detected"))),
        "approved_records": sum(1 for row in rows if bool(row.get("approved"))),
        "root_cause_counts": dict(Counter(str(row.get("root_cause", "unknown")) for row in rows)),
        "healing_action_counts": dict(Counter(str(row.get("healing_action", "unknown")) for row in rows)),
        "automation_decision_counts": dict(Counter(str(row.get("automation_decision", "unknown")) for row in rows)),
        "ric_control_type_counts": dict(Counter(str((row.get("ric_control") or {}).get("type", "none")) for row in rows)),
    }


def read_sqlite_summary(db: Path, run_name: str) -> dict[str, Any]:
    if not db.exists():
        return {"available": False, "database": str(db)}
    with sqlite3.connect(db) as conn:
        decision_count = int(conn.execute("SELECT COUNT(*) FROM decisions WHERE run_name = ?", (run_name,)).fetchone()[0])
        feature_count = int(conn.execute("SELECT COUNT(*) FROM feature_rows WHERE source = ?", ("live_oai_metrics",)).fetchone()[0])
        quality_count = int(conn.execute("SELECT COUNT(*) FROM data_quality_events").fetchone()[0])
        root_causes = dict(
            conn.execute(
                "SELECT root_cause, COUNT(*) FROM decisions WHERE run_name = ? GROUP BY root_cause",
                (run_name,),
            ).fetchall()
        )
        actions = dict(
            conn.execute(
                "SELECT healing_action, COUNT(*) FROM decisions WHERE run_name = ? GROUP BY healing_action",
                (run_name,),
            ).fetchall()
        )
    return {
        "available": True,
        "database": str(db),
        "decision_records": decision_count,
        "feature_rows": feature_count,
        "data_quality_events": quality_count,
        "root_cause_counts": root_causes,
        "healing_action_counts": actions,
    }


def file_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "path": str(path), "bytes": 0}
    return {"available": True, "path": str(path), "bytes": path.stat().st_size}


def to_markdown(report: dict[str, Any]) -> str:
    summary = report["jsonl_decision_summary"]
    sqlite_summary = report["sqlite_summary"]
    return "\n".join(
        [
            "# Live OAI/FlexRIC Run Report",
            "",
            f"Version: {report['version']}",
            "",
            "## Decision Summary",
            "",
            f"- JSONL records: {summary['records']}",
            f"- Anomaly records: {summary['anomaly_records']}",
            f"- Approved records: {summary['approved_records']}",
            f"- SQLite decision records: {sqlite_summary.get('decision_records', 0)}",
            f"- SQLite feature rows: {sqlite_summary.get('feature_rows', 0)}",
            f"- Data quality events: {sqlite_summary.get('data_quality_events', 0)}",
            "",
            "## Root Causes",
            "",
            json.dumps(summary["root_cause_counts"], indent=2),
            "",
            "## Healing Actions",
            "",
            json.dumps(summary["healing_action_counts"], indent=2),
            "",
            "## Honest Interpretation",
            "",
            report["honest_interpretation"],
            "",
        ]
    )


if __name__ == "__main__":
    main()
