from __future__ import annotations

import pandas as pd

from stats.persistence_eval import evaluate_persistence


def test_persistence_evaluation_reports_episode_latency_and_alarm_rate():
    rows = []
    for kind, flags in (("attack", [True, True, True, False]), ("benign", [False, True, False, False])):
        for index, flag in enumerate(flags):
            rows.append({
                "domain": "simulated",
                "attack_family": "fixture",
                "kind": kind,
                "stream_id": kind,
                "window_start_s": index * 0.2,
                "raw_h1": flag,
                "raw_novel": False,
            })

    summary, episodes, _ = evaluate_persistence(pd.DataFrame(rows), 0.2, 2.0)
    raw = summary[summary["setting"] == "1-of-1"].iloc[0]
    persisted = summary[summary["setting"] == "2-of-3"].iloc[0]

    assert raw["alarms_per_hour"] == 4500.0
    assert raw["episode_alarms_per_hour"] == 4500.0
    assert persisted["alarms_per_hour"] == 0.0
    assert persisted["episode_alarms_per_hour"] == 0.0
    assert persisted["mean_added_detection_latency_s"] == 0.2
    assert persisted["within_2s_episode_rate"] == 1.0
    episode = episodes[(episodes["setting"] == "2-of-3") & (episodes["stream_id"] == "attack")].iloc[0]
    assert episode["time_to_decision_s"] == 0.2
