from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FIELDS = [
    "row_id",
    "cell_id",
    "service_class",
    "anomaly_detected",
    "risk_score",
    "root_cause",
    "healing_action",
    "automation_decision",
    "approved",
    "ric_control_type",
    "ric_policy",
    "ric_intent",
    "reason_count",
    "reasons",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export compact JSONL decision records to a clean CSV.")
    parser.add_argument("--input", default="outputs/flexric_xapp_longrun_decisions.jsonl")
    parser.add_argument("--output", default="outputs/evidence/flexric_kpm_30min_decisions.csv")
    args = parser.parse_args()

    rows = list(read_rows(Path(args.input)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for idx, row in enumerate(rows):
            writer.writerow(flatten(idx, row))
    print(f"Exported {len(rows)} decision rows to {output}")


def read_rows(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def flatten(idx: int, row: dict[str, Any]) -> dict[str, Any]:
    ric = row.get("ric_control") or {}
    payload = ric.get("payload") or {}
    reasons = row.get("reasons") or []
    return {
        "row_id": idx,
        "cell_id": row.get("cell_id", ""),
        "service_class": row.get("service_class", ""),
        "anomaly_detected": bool(row.get("anomaly_detected", False)),
        "risk_score": row.get("risk_score", ""),
        "root_cause": row.get("root_cause", ""),
        "healing_action": row.get("healing_action", ""),
        "automation_decision": row.get("automation_decision", ""),
        "approved": bool(row.get("approved", False)),
        "ric_control_type": ric.get("type", "none"),
        "ric_policy": payload.get("policy", ""),
        "ric_intent": payload.get("intent", ""),
        "reason_count": len(reasons),
        "reasons": " | ".join(str(item) for item in reasons),
    }


if __name__ == "__main__":
    main()
