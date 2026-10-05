from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oran_twin.engine import OranDecisionEngine, normalize_engine_row
from oran_twin.persistence import DecisionStore
from tools.normalize_telemetry import parse_kv_line


def main() -> None:
    parser = argparse.ArgumentParser(description="Tail live OAI/FlexRIC metric lines into the decision engine and SQLite.")
    parser.add_argument("--input", default="data/telemetry/raw/live_oai_metrics.log")
    parser.add_argument("--output", default="outputs/live_oai_decisions.jsonl")
    parser.add_argument("--db", default="outputs/oran_twin.sqlite")
    parser.add_argument("--service", default="eMBB")
    parser.add_argument("--run-name", default="live_oai_stream")
    parser.add_argument("--poll", type=float, default=1.0)
    parser.add_argument("--from-start", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.touch(exist_ok=True)

    engine = OranDecisionEngine()
    store = DecisionStore(Path(args.db))
    offset = 0 if args.from_start else input_path.stat().st_size
    processed = 0
    print(f"Streaming {input_path} -> engine -> {output_path} and {args.db}")

    while True:
        offset, new_count = process_new_lines(
            input_path=input_path,
            output_path=output_path,
            offset=offset,
            engine=engine,
            store=store,
            service=args.service,
            run_name=args.run_name,
        )
        processed += new_count
        if new_count:
            print(f"processed {new_count} live row(s), total={processed}")
        if args.once:
            break
        time.sleep(args.poll)


def process_new_lines(
    *,
    input_path: Path,
    output_path: Path,
    offset: int,
    engine: OranDecisionEngine,
    store: DecisionStore,
    service: str,
    run_name: str,
) -> tuple[int, int]:
    with input_path.open("r", encoding="utf-8", errors="replace") as source:
        source.seek(offset)
        lines = source.readlines()
        offset = source.tell()

    count = 0
    with output_path.open("a", encoding="utf-8") as target:
        for line in lines:
            row = parse_live_metric_line(line, service)
            if row is None:
                if line.strip():
                    store.record_data_quality_event(
                        source="live_oai_metrics",
                        severity="warning",
                        event_type="unparsed_metric_line",
                        message="Line did not contain parseable KPI values.",
                        payload={"line": line.strip()[:300]},
                    )
                continue
            normalized = normalize_engine_row(row)
            decision = engine.assess(normalized)
            store.record_feature_row(source="live_oai_metrics", row=normalized, label={"fault_active": normalized["fault_active"], "fault_type": normalized["fault_type"]})
            store.record_decision(run_name=run_name, mode="live_oai_stream", decision=decision)
            target.write(json.dumps(compact_decision(decision), separators=(",", ":")) + "\n")
            count += 1
    return offset, count


def parse_live_metric_line(line: str, service: str) -> dict[str, Any] | None:
    parsed = parse_kv_line(line, cell_id="CELL_A")
    if not parsed:
        return None
    return {
        **parsed,
        "service_class": service,
        "fault_active": False,
        "fault_type": "unknown_live_oai",
        "aml_attack_active": False,
        "aml_attack_type": "none",
    }


def compact_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "cell_id": decision["cell_id"],
        "service_class": decision["service_class"],
        "anomaly_detected": decision["anomaly_detected"],
        "risk_score": decision["twin_risk_score"],
        "root_cause": decision["root_cause"],
        "healing_action": decision["healing_action"],
        "automation_decision": decision["automation_safety_decision"],
        "approved": decision["action_approved_by_twin"],
        "ric_control": decision["ric_control"],
        "reasons": decision["anomaly_reasons"][:8],
    }


if __name__ == "__main__":
    main()
