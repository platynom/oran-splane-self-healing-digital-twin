from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from normalize_telemetry import OUTPUT_FIELDS, parse_kv_line


def main() -> None:
    parser = argparse.ArgumentParser(description="Tail OAI/srsRAN-style raw metric logs and append normalized KPI rows.")
    parser.add_argument("--input", default="data/telemetry/raw/live_oai_metrics.log")
    parser.add_argument("--output", default="data/telemetry/live_oai_feed.csv")
    parser.add_argument("--cell-id", default="CELL_A")
    parser.add_argument("--poll", type=float, default=1.0)
    parser.add_argument("--from-start", action="store_true", help="Read existing input content before tailing.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.touch(exist_ok=True)

    offset = 0 if args.from_start else input_path.stat().st_size
    ensure_header(output_path)
    print(f"Watching {input_path} -> {output_path}")

    while True:
        try:
            offset = consume_new_lines(input_path, output_path, offset, args.cell_id)
        except OSError as exc:
            print(f"collector warning: {exc}")
        time.sleep(args.poll)


def consume_new_lines(input_path: Path, output_path: Path, offset: int, cell_id: str) -> int:
    with input_path.open("r", encoding="utf-8", errors="replace") as source:
        source.seek(offset)
        lines = source.readlines()
        offset = source.tell()
    if not lines:
        return offset

    rows = [row for line in lines if (row := parse_kv_line(line, cell_id))]
    if not rows:
        return offset

    with output_path.open("a", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
        writer.writerows(rows)
    print(f"normalized {len(rows)} row(s)")
    return offset


def ensure_header(path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()


if __name__ == "__main__":
    main()
