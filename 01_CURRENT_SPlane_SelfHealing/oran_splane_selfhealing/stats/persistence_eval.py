from __future__ import annotations

"""Temporal persistence evaluation for held-family open-set traces."""

import numpy as np
import pandas as pd

from discriminator.openset import apply_persistence


PERSISTENCE_SETTINGS = ((1, 1), (2, 3), (3, 5), (4, 7))


def _persist_streams(trace: pd.DataFrame, n: int, m: int) -> pd.DataFrame:
    parts = []
    for _, stream in trace.groupby(["domain", "attack_family", "kind", "stream_id"], sort=False):
        ordered = stream.sort_values("window_start_s").copy()
        ordered["persistent_h1"] = apply_persistence(ordered["raw_h1"].to_numpy(), n, m)
        ordered["persistent_novel"] = apply_persistence(ordered["raw_novel"].to_numpy(), n, m)
        ordered["persistent_protective"] = ordered["persistent_h1"] | ordered["persistent_novel"]
        parts.append(ordered)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def evaluate_persistence(
    traces: pd.DataFrame,
    step_s: float,
    failure_window_s: float,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Sweep persistence settings and return family summaries and episode rows."""
    summary_rows: list[dict] = []
    episode_rows: list[dict] = []
    for n, m in PERSISTENCE_SETTINGS:
        setting = f"{n}-of-{m}"
        persisted = _persist_streams(traces, n, m)
        for (domain, family), family_trace in persisted.groupby(["domain", "attack_family"]):
            benign = family_trace[family_trace["kind"] == "benign"]
            attack = family_trace[family_trace["kind"] == "attack"]
            benign_fp = float(benign["persistent_protective"].mean())
            false_alarm_episodes = 0
            for _, benign_stream in benign.groupby("stream_id"):
                flags = benign_stream.sort_values("window_start_s")["persistent_protective"].astype(bool)
                false_alarm_episodes += int((flags & ~flags.shift(fill_value=False)).sum())
            benign_hours = len(benign) * step_s / 3600.0
            attack_protection = float(attack["persistent_protective"].mean())
            family_episodes = []
            for stream_id, episode in attack.groupby("stream_id"):
                episode = episode.sort_values("window_start_s")
                start = float(episode["window_start_s"].min())
                raw = episode[episode["raw_h1"] | episode["raw_novel"]]
                detected = episode[episode["persistent_protective"]]
                raw_ttd = float(raw["window_start_s"].iloc[0] - start) if not raw.empty else np.nan
                ttd = float(detected["window_start_s"].iloc[0] - start) if not detected.empty else np.nan
                added = float(ttd - raw_ttd) if np.isfinite(ttd) and np.isfinite(raw_ttd) else np.nan
                within = bool(np.isfinite(ttd) and ttd <= failure_window_s)
                row = {
                    "domain": domain,
                    "attack_family": family,
                    "setting": setting,
                    "n": n,
                    "m": m,
                    "stream_id": stream_id,
                    "detected": bool(np.isfinite(ttd)),
                    "raw_time_to_detection_s": raw_ttd,
                    "time_to_decision_s": ttd,
                    "added_detection_latency_s": added,
                    "within_2s": within,
                }
                episode_rows.append(row)
                family_episodes.append(row)
            episode_frame = pd.DataFrame(family_episodes)
            detected_episodes = episode_frame[episode_frame["detected"]]
            summary_rows.append({
                "domain": domain,
                "attack_family": family,
                "setting": setting,
                "n": n,
                "m": m,
                "benign_windows": int(len(benign)),
                "benign_false_alarm_rate": benign_fp,
                "alarms_per_hour": benign_fp * 3600.0 / step_s,
                "false_alarm_episodes": false_alarm_episodes,
                "episode_alarms_per_hour": false_alarm_episodes / benign_hours if benign_hours else 0.0,
                "attack_windows": int(len(attack)),
                "combined_protective_rate": attack_protection,
                "attack_episodes": int(len(episode_frame)),
                "episode_detection_rate": float(episode_frame["detected"].mean()),
                "mean_time_to_decision_s": float(detected_episodes["time_to_decision_s"].mean()),
                "max_time_to_decision_s": float(detected_episodes["time_to_decision_s"].max()),
                "mean_added_detection_latency_s": float(detected_episodes["added_detection_latency_s"].mean()),
                "within_2s_episode_rate": float(episode_frame["within_2s"].mean()),
            })
    summary = pd.DataFrame(summary_rows)
    episodes = pd.DataFrame(episode_rows)
    recommendation = recommend_setting(summary)
    return summary, episodes, recommendation


def recommend_setting(summary: pd.DataFrame, target_real_fp: float = 0.02) -> str:
    """Choose the closest real FP to budget among settings protecting all episodes in time."""
    candidates = []
    for setting, rows in summary.groupby("setting"):
        real = rows[rows["domain"] == "timesafe_real"]
        if real.empty:
            continue
        real_fp = float(np.average(real["benign_false_alarm_rate"], weights=real["benign_windows"]))
        eligible = bool((rows["within_2s_episode_rate"] >= 0.95).all())
        min_episode_detection = float(rows["episode_detection_rate"].min())
        candidates.append((not eligible, abs(real_fp - target_real_fp), -min_episode_detection, setting))
    return min(candidates)[-1] if candidates else "1-of-1"
