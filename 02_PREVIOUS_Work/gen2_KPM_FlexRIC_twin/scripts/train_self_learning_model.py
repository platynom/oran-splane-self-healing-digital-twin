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
    parser = argparse.ArgumentParser(description="Train/replay the online self-learning O-RAN KPI model.")
    parser.add_argument("--input", required=True, help="CSV file with O-RAN KPI rows.")
    parser.add_argument("--output", default="outputs/models/self_learning_model.json")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    model = OnlineSelfLearningModel()
    fault_counts: Counter[str] = Counter()
    records = 0

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row = normalize_engine_row(raw)
            model.learn(row)
            records += 1
            if row["fault_active"]:
                fault_counts[str(row["fault_type"]).split("+", 1)[0]] += 1

    model.save(output_path)
    summary = {
        "records_replayed": records,
        "fault_labels_seen": dict(fault_counts),
        "model_artifact": str(output_path),
        "model_type": "online_self_learning_v1",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
