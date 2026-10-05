from __future__ import annotations

"""Run the governed S-plane loop on live pmc telemetry in recommend-only mode."""

import argparse
import copy
import csv
import json
import logging
import queue
import sys
import threading
import time
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from discriminator.model import train_and_evaluate
from healing.loop import GovernedHealingLoop
from ingest.schema import TELEMETRY_COLUMNS
from scripts.live_collect import LiveCollector
from telemetry.features import window_features


LOG = logging.getLogger("live_loop")


def _configured_loop(clf, config: dict, n: int, m: int) -> GovernedHealingLoop:
    cfg = copy.deepcopy(config)
    cfg["openset"]["persistence"].update({"enabled": True, "n": n, "m": m})
    return GovernedHealingLoop(clf, cfg)


def _episode_count(flags: list[bool]) -> int:
    return sum(flag and (index == 0 or not flags[index - 1]) for index, flag in enumerate(flags))


def _extract_fixed_window(rows: list[dict], start_s: float, window_s: float) -> pd.Series | None:
    end_s = start_s + window_s
    selected = [row for row in rows if start_s <= float(row["t_s"]) < end_s]
    if len(selected) < 3:
        return None
    # window_features uses the observed max timestamp as its stopping bound.
    # A boundary sentinel is excluded from the half-open window but preserves
    # a stable live grid despite command scheduling jitter.
    frame = pd.DataFrame(selected)
    # Preserve inter-sample deltas but align the first observed sample to the
    # fixed grid; otherwise scheduling jitter moves window_features' anchor.
    frame["t_s"] = frame["t_s"].astype(float) - float(frame["t_s"].iloc[0]) + start_s
    boundary = frame.iloc[-1].to_dict()
    boundary["t_s"] = end_s
    frame = pd.concat([frame, pd.DataFrame([boundary])], ignore_index=True)
    features = window_features(frame, window_s, window_s)
    return None if features.empty else features.iloc[0]


def run_live(
    duration_s: float,
    poll_interval_s: float,
    namespace: str | None,
    scenario: str,
    out: Path,
    pmc_socket: str,
) -> dict:
    config = yaml.safe_load((ROOT / "config" / "default.yaml").read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    windows = pd.read_csv(ROOT / "dataset" / "splane_windows.csv")
    clf, _ = train_and_evaluate(windows, config, out.parent / "model")
    collector = LiveCollector(namespace, scenario, poll_interval_s, pmc_socket=pmc_socket)
    shipped = _configured_loop(clf, config, 2, 3)
    history: list[dict] = []
    decisions: list[dict] = []
    attempted_windows = 0
    telemetry_count = 0
    next_window_start: float | None = None
    window_s = float(config["dataset"]["window_s"])
    step_s = float(config["dataset"]["step_s"])
    started = time.monotonic()
    samples: queue.Queue[dict] = queue.Queue()
    stop = threading.Event()
    telemetry_path = out.with_name(f"{out.stem}_telemetry.csv")
    telemetry_handle = telemetry_path.open("w", newline="", encoding="utf-8")
    telemetry_writer = csv.DictWriter(telemetry_handle, fieldnames=TELEMETRY_COLUMNS)
    telemetry_writer.writeheader()

    def produce() -> None:
        nonlocal telemetry_count
        try:
            while not stop.is_set():
                cycle = time.monotonic()
                row = collector.sample()
                if row is not None:
                    telemetry_writer.writerow(row)
                    telemetry_handle.flush()
                    telemetry_count += 1
                    samples.put(row)
                stop.wait(max(0.0, poll_interval_s - (time.monotonic() - cycle)))
        except Exception:
            LOG.exception("live telemetry producer stopped unexpectedly")
            stop.set()

    producer = threading.Thread(target=produce, name="pmc-live-collector", daemon=True)
    producer.start()
    try:
        while duration_s <= 0 or time.monotonic() - started < duration_s:
            try:
                row = samples.get(timeout=min(0.5, poll_interval_s * 2.0))
            except queue.Empty:
                continue
            if row is not None:
                history.append(row)
                if next_window_start is None:
                    next_window_start = float(row["t_s"])
            if next_window_start is not None and history:
                latest = float(history[-1]["t_s"])
                while latest >= next_window_start + window_s:
                    attempted_windows += 1
                    window = _extract_fixed_window(history, next_window_start, window_s)
                    current_start = next_window_start
                    next_window_start += step_s
                    history = [item for item in history if float(item["t_s"]) >= next_window_start - 0.05]
                    if window is not None:
                        end_to_end = time.perf_counter()
                        decision = shipped.decide(window)
                        latency = time.perf_counter() - end_to_end
                        record = {
                            "wall_time": pd.Timestamp.now(tz="UTC").isoformat(),
                            "scenario": scenario,
                            "window_start_s": current_start,
                            "offset_abs_max_ns": float(window["offset_abs_max"]),
                            "pdv_std_ns": float(window["pdv_std"]),
                            "label": decision.label_estimate,
                            "action": decision.action,
                            "reason": decision.reason,
                            "decision_latency_s": decision.decision_time_s,
                            "end_to_end_latency_s": latency,
                            "within_budget": decision.within_budget,
                            # PENDING means the current raw H1/UNKNOWN flag has
                            # not yet satisfied shipped 2-of-3 persistence.
                            "protective_1of1": decision.label_estimate in {"H1", "UNKNOWN", "PENDING"},
                            "protective_2of3": decision.label_estimate in {"H1", "UNKNOWN"},
                        }
                        decisions.append(record)
                        print(json.dumps(record), flush=True)
    except KeyboardInterrupt:
        LOG.info("live loop interrupted; preserving %d decisions", len(decisions))
    finally:
        stop.set()
        producer.join(timeout=2.0)
        telemetry_handle.close()

    out.parent.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(decisions)
    table.to_csv(out, index=False)
    achieved = time.monotonic() - started
    summary = {
        "duration_s": achieved,
        "telemetry_rows": telemetry_count,
        "attempted_windows": attempted_windows,
        "decision_windows": len(table),
        "skipped_undersampled_windows": attempted_windows - len(table),
    }
    if not table.empty and achieved > 0:
        hours = achieved / 3600.0
        for name in ("protective_1of1", "protective_2of3"):
            flags = table[name].astype(bool).tolist()
            summary[f"{name}_windows_per_hour"] = sum(flags) / hours
            summary[f"{name}_episodes_per_hour"] = _episode_count(flags) / hours
        summary["latency_mean_s"] = float(table["end_to_end_latency_s"].mean())
        summary["latency_max_s"] = float(table["end_to_end_latency_s"].max())
    (out.with_suffix(".summary.json")).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=600.0)
    parser.add_argument("--poll-interval", type=float, default=0.1)
    parser.add_argument("--namespace", default=None)
    parser.add_argument("--scenario", default="live")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pmc-socket", default="/var/run/ptp4l-splane-slave")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    summary = run_live(args.duration, args.poll_interval, args.namespace, args.scenario, args.out, args.pmc_socket)
    LOG.info("recommend-only live run complete: %s", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
