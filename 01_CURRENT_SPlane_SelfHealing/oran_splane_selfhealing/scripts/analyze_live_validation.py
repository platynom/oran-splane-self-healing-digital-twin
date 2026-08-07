from __future__ import annotations

"""Summarize measured live-validation artifacts without extrapolating results."""

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingest.pcap_ingest import pcap_to_telemetry
from telemetry.features import configured_feature_columns, window_features


LIVE = ROOT / "results" / "live"


def transcript_rows(path: Path) -> pd.DataFrame:
    rows = []
    for line in path.read_text(encoding="utf-16", errors="ignore").splitlines():
        start = line.find("{")
        if start < 0:
            continue
        try:
            value = json.loads(line[start:])
        except json.JSONDecodeError:
            continue
        if "window_start_s" in value:
            rows.append(value)
    if rows:
        return pd.DataFrame(rows)
    # Transcripts written directly by Linux are UTF-8 rather than PowerShell UTF-16.
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "window_start_s" in value:
            rows.append(value)
    return pd.DataFrame(rows)


def episode_count(table: pd.DataFrame, flag_col: str, expected_step_s: float = 0.2) -> int:
    flags = table[flag_col].astype(bool).to_numpy()
    # Missing/under-sampled windows do not clear an operator-facing alarm.
    # Only an observed non-protective decision followed by protection starts
    # a new de-duplicated episode.
    return sum(flag and (index == 0 or not flags[index - 1]) for index, flag in enumerate(flags))


def protective_metrics(table: pd.DataFrame, duration_s: float, scope: str) -> list[dict]:
    rows = []
    hours = duration_s / 3600.0
    for setting, column in (("1-of-1", "protective_1of1"), ("2-of-3", "protective_2of3")):
        count = int(table[column].astype(bool).sum())
        episodes = episode_count(table, column)
        rows.append(
            {
                "scope": scope,
                "persistence": setting,
                "duration_s": duration_s,
                "valid_windows": len(table),
                "false_alarm_windows": count,
                "false_alarm_percent": 100.0 * count / max(len(table), 1),
                "false_alarm_windows_per_hour": count / hours,
                "deduplicated_episodes": episodes,
                "deduplicated_episodes_per_hour": episodes / hours,
            }
        )
    return rows


def phase_metrics(decisions: pd.DataFrame) -> pd.DataFrame:
    wall = pd.to_datetime(decisions["wall_time"], utc=True)
    boundaries = [
        ("pdv", pd.Timestamp("2026-08-06T19:43:11Z"), pd.Timestamp("2026-08-06T19:46:49Z")),
        ("loss", pd.Timestamp("2026-08-06T19:46:49Z"), pd.Timestamp("2026-08-06T19:50:29Z")),
        ("holdover", pd.Timestamp("2026-08-06T19:50:29Z"), pd.Timestamp("2026-08-06T19:54:09Z")),
    ]
    rows = []
    for phase, start, end in boundaries:
        part = decisions[(wall >= start) & (wall < end)]
        rows.append(
            {
                "phase": phase,
                "windows": len(part),
                "h1_percent": 100.0 * part["label"].eq("H1").mean() if len(part) else 0.0,
                "unknown_percent": 100.0 * part["label"].eq("UNKNOWN").mean() if len(part) else 0.0,
                "protective_2of3_percent": 100.0 * part["protective_2of3"].astype(bool).mean() if len(part) else 0.0,
                "latency_mean_s": part["end_to_end_latency_s"].mean(),
                "latency_max_s": part["end_to_end_latency_s"].max(),
                "within_1s_percent": 100.0 * part["within_budget"].astype(bool).mean() if len(part) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def planned_gm_metrics(decisions: pd.DataFrame) -> pd.DataFrame:
    wall = pd.to_datetime(decisions["wall_time"], utc=True)
    switch = pd.Timestamp("2026-08-06T16:19:31Z")
    segments = {
        "pre_switch": (switch - pd.Timedelta(seconds=60), switch),
        "switch_plus_10s": (switch - pd.Timedelta(seconds=5), switch + pd.Timedelta(seconds=10)),
        "post_switch": (switch, switch + pd.Timedelta(seconds=60)),
    }
    rows = []
    for name, (start, end) in segments.items():
        part = decisions[(wall >= start) & (wall < end)]
        rows.append(
            {
                "segment": name,
                "windows": len(part),
                "h1_percent": 100.0 * part["label"].eq("H1").mean() if len(part) else 0.0,
                "unknown_percent": 100.0 * part["label"].eq("UNKNOWN").mean() if len(part) else 0.0,
                "protective_percent": 100.0 * part["protective_2of3"].astype(bool).mean() if len(part) else 0.0,
                "protective_episodes": episode_count(part.reset_index(drop=True), "protective_2of3") if len(part) else 0,
            }
        )
    return pd.DataFrame(rows)


def feature_coverage(config: dict) -> pd.DataFrame:
    features = configured_feature_columns(config)
    live = pd.read_csv(LIVE / "live_loop_10min_corrected_telemetry.csv")
    live = live[live["t_s"] <= min(float(live["t_s"].min()) + 60.0, float(live["t_s"].max()))]
    live_windows = window_features(live, config["dataset"]["window_s"], config["dataset"]["step_s"])

    pcap = pcap_to_telemetry(LIVE / "mixed_pcaps_corrected" / "pdv.pcap", scenario="pcap_pdv", label="healthy")
    pcap = pcap[pcap["t_s"] <= min(float(pcap["t_s"].min()) + 60.0, float(pcap["t_s"].max()))]
    pcap_windows = window_features(pcap, config["dataset"]["window_s"], config["dataset"]["step_s"])
    rows = []
    for feature in features:
        rows.append(
            {
                "feature": feature,
                "live_pmc_nonconstant": bool(live_windows[feature].nunique(dropna=False) > 1),
                "live_pmc_unique_values": int(live_windows[feature].nunique(dropna=False)),
                "pcap_nonconstant": bool(pcap_windows[feature].nunique(dropna=False) > 1),
                "pcap_unique_values": int(pcap_windows[feature].nunique(dropna=False)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    config = yaml.safe_load((ROOT / "config" / "default.yaml").read_text(encoding="utf-8"))
    baseline = transcript_rows(LIVE / "baseline_2h_transcript.txt")
    baseline = baseline.sort_values("window_start_s").drop_duplicates("window_start_s")
    telemetry = pd.read_csv(LIVE / "baseline_2h_decisions_telemetry.csv", usecols=["t_s"])
    telemetry_duration = float(telemetry["t_s"].max() - telemetry["t_s"].min())
    decision_duration = float(baseline["window_start_s"].max() - baseline["window_start_s"].min() + 0.2)
    baseline_metrics = pd.DataFrame(protective_metrics(baseline, decision_duration, "benign_baseline"))
    baseline_metrics["telemetry_duration_s"] = telemetry_duration
    baseline_metrics.to_csv(LIVE / "baseline_false_alarm_metrics.csv", index=False)

    corrected = pd.read_csv(LIVE / "live_loop_10min_corrected.csv")
    phases = phase_metrics(corrected)
    phases.to_csv(LIVE / "mixed_phase_metrics.csv", index=False)

    planned = pd.read_csv(LIVE / "planned_gm_failover_decisions.csv")
    gm = planned_gm_metrics(planned)
    gm.to_csv(LIVE / "planned_gm_metrics.csv", index=False)

    coverage = feature_coverage(config)
    coverage.to_csv(LIVE / "live_feature_coverage.csv", index=False)

    summary = pd.DataFrame(
        [
            {"metric": "baseline_telemetry_duration_s", "value": telemetry_duration},
            {"metric": "baseline_decision_duration_s", "value": decision_duration},
            {"metric": "baseline_valid_decision_windows", "value": len(baseline)},
            {"metric": "baseline_latency_mean_s", "value": baseline["end_to_end_latency_s"].mean()},
            {"metric": "baseline_latency_max_s", "value": baseline["end_to_end_latency_s"].max()},
            {"metric": "baseline_within_1s_percent", "value": 100.0 * baseline["within_budget"].astype(bool).mean()},
            {"metric": "baseline_within_2s_percent", "value": 100.0 * baseline["end_to_end_latency_s"].lt(2.0).mean()},
            {"metric": "live_nonconstant_features", "value": int(coverage["live_pmc_nonconstant"].sum())},
            {"metric": "pcap_nonconstant_features", "value": int(coverage["pcap_nonconstant"].sum())},
            {"metric": "configured_features", "value": len(coverage)},
        ]
    )
    summary.to_csv(LIVE / "live_validation_summary.csv", index=False)
    print(summary.to_string(index=False))
    print("\nBaseline false alarms:\n", baseline_metrics.to_string(index=False))
    print("\nMixed phases:\n", phases.to_string(index=False))
    print("\nPlanned GM change:\n", gm.to_string(index=False))


if __name__ == "__main__":
    main()
