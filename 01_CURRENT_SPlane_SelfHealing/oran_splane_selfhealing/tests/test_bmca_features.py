from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from faults.injectors import run_scenario
from fronthaul_sim.simulator import SimConfig
from telemetry.features import FEATURE_COLUMNS, window_features


def _windows(runs: int = 16) -> pd.DataFrame:
    config = SimConfig(seed=1588, duration_s=8.0, dt_s=0.02, noise_ns=14.0)
    telemetry = pd.concat(
        [
            run_scenario(config, scenario, run_id)
            for scenario in ("planned_gm_failover", "ptp_spoof")
            for run_id in range(runs)
        ],
        ignore_index=True,
    )
    return window_features(telemetry, window_s=0.4, step_s=0.2)


def test_spoof_fires_relative_gm_transition_features():
    windows = _windows(runs=4)
    spoof = windows[(windows["scenario"] == "ptp_spoof") & (windows["label"] == "H1")]
    assert (spoof["gm_identity_changes"] > 0).any()
    assert (spoof["gm_identity_churn"] > 1).any()
    assert (spoof["clock_class_improve_jump"] > 0).any()
    assert (spoof["priority1_changes"] > 0).any()
    assert (spoof["steps_removed_changes"] > 0).any()


def test_planned_gm_failover_is_not_rejected_just_because_identity_changes():
    windows = _windows()
    anomalous = windows[windows["label"].isin(["H0", "H1"])]
    train = anomalous[anomalous["run_id"] < 12]
    test = anomalous[anomalous["run_id"] >= 12]
    model = RandomForestClassifier(
        n_estimators=90,
        max_depth=6,
        random_state=1588,
        class_weight="balanced",
    ).fit(train[FEATURE_COLUMNS], train["label"])
    failover = test[test["scenario"] == "planned_gm_failover"]
    prediction = model.predict(failover[FEATURE_COLUMNS])

    assert (failover["gm_identity_changes"] > 0).any()
    assert float((prediction == "H1").mean()) <= 0.10


def test_raw_identity_and_mac_are_not_model_features():
    forbidden = {"grandmaster_identity", "source_mac", "destination_mac", "mac"}
    assert forbidden.isdisjoint(FEATURE_COLUMNS)
    assert all("raw_identity" not in feature and "mac" not in feature.lower() for feature in FEATURE_COLUMNS)
