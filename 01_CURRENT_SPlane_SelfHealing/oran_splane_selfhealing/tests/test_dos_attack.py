from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from faults.injectors import run_scenario
from fronthaul_sim.simulator import SimConfig
from telemetry.features import FEATURE_COLUMNS, window_features


def _config() -> SimConfig:
    return SimConfig(seed=1588, duration_s=8.0, dt_s=0.02, noise_ns=14.0)


def _attack_windows(runs: int = 16) -> pd.DataFrame:
    frames = [
        run_scenario(_config(), scenario, run_id)
        for scenario in ("traffic_burst", "ptp_dos_flood")
        for run_id in range(runs)
    ]
    windows = window_features(pd.concat(frames, ignore_index=True), window_s=0.4, step_s=0.2)
    return windows[windows["label"].isin(["H0", "H1"])].copy()


def test_dos_and_benign_burst_have_distinct_but_overlapping_rates():
    windows = _attack_windows(runs=8)
    burst = windows[windows["scenario"] == "traffic_burst"]
    dos = windows[windows["scenario"] == "ptp_dos_flood"]

    assert set(burst["label"]) == {"H0"}
    assert set(dos["label"]) == {"H1"}
    assert dos["msg_rate_mean"].median() > burst["msg_rate_mean"].median() * 2.0
    assert dos["msg_rate_mean"].min() < burst["msg_rate_mean"].max()
    assert dos["msg_rate_std"].median() > burst["msg_rate_std"].median() * 5.0
    assert windows["msg_rate_mean"].nunique() > 10


def test_model_catches_dos_without_treating_every_traffic_burst_as_attack():
    windows = _attack_windows()
    train = windows[windows["run_id"] < 12]
    test = windows[windows["run_id"] >= 12]
    model = RandomForestClassifier(
        n_estimators=90,
        max_depth=6,
        random_state=1588,
        class_weight="balanced",
    ).fit(train[FEATURE_COLUMNS], train["label"])
    prediction = pd.Series(model.predict(test[FEATURE_COLUMNS]), index=test.index)

    dos_recall = float((prediction[test["label"] == "H1"] == "H1").mean())
    burst_false_positive_rate = float((prediction[test["label"] == "H0"] == "H1").mean())
    assert dos_recall >= 0.90
    assert burst_false_positive_rate <= 0.10

    # A simplistic high-rate detector is not sufficient: at 4x the healthy
    # cadence it catches DoS but also rejects the legitimate traffic bursts.
    naive_high_rate = test["msg_rate_mean"] > 4.0 / _config().dt_s
    assert float(naive_high_rate[test["label"] == "H1"].mean()) >= 0.90
    assert float(naive_high_rate[test["label"] == "H0"].mean()) >= 0.90
