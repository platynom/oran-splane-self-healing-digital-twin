from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path


FIELDS = ["cell_id", "latency", "jitter", "throughput", "loss", "prb", "handover", "edgeDelay", "backhaul", "sinr", "bler"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Append normalized live KPI rows to simulate an OAI/srsRAN collector.")
    parser.add_argument("--output", default="data/telemetry/live_oai_feed.csv")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--cell-id", default="CELL_F")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output.exists()
    with output.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        for idx in range(args.samples):
            writer.writerow(generate_row(args.cell_id, idx))
            handle.flush()
            print(f"appended sample={idx + 1} to {output}")
            time.sleep(args.interval)


def generate_row(cell_id: str, idx: int) -> dict[str, float | str]:
    wave = 0.5 + 0.5 * math.sin(idx / 4)
    stress = min(1.0, idx / 20)
    prb = 62 + wave * 12 + stress * 18
    bler = 1.2 + wave * 1.1 + stress * 1.6
    sinr = 21 - wave * 2.5 - stress * 3.2
    throughput = 118 - stress * 38 - wave * 8
    latency = 18 + stress * 18 + wave * 5
    jitter = 3.5 + stress * 5 + wave * 2
    return {
        "cell_id": cell_id,
        "latency": round(latency, 3),
        "jitter": round(jitter, 3),
        "throughput": round(throughput, 3),
        "loss": round(0.18 + stress * 0.8, 4),
        "prb": round(min(100, prb), 3),
        "handover": round(0.8 + stress * 3.5, 3),
        "edgeDelay": round(2.8 + stress * 2.2, 3),
        "backhaul": round(4.1 + stress * 3.5, 3),
        "sinr": round(sinr, 3),
        "bler": round(bler, 3),
    }


if __name__ == "__main__":
    main()
