from __future__ import annotations

import copy
from pathlib import Path

import yaml

from faults.injectors import generate_telemetry, run_scenario
from fronthaul_sim.simulator import SimConfig
from stats.gnss_eval import evaluate_gnss_confusion
from telemetry.features import CONSISTENCY_FEATURE_COLUMNS, FEATURE_COLUMNS, TIMESOURCE_FEATURE_COLUMNS, window_features

ROOT = Path(__file__).resolve().parents[1]


def _config() -> dict:
    with (ROOT / "config" / "default.yaml").open("r", encoding="utf-8") as handle:
        return copy.deepcopy(yaml.safe_load(handle))


def _sim_config(config: dict) -> SimConfig:
    return SimConfig(
        seed=int(config["seed"]),
        time_error_budget_ns=float(config["time_error_budget_ns"]),
        **config["sim"],
        **config.get("oscillator", {}),
    )


def test_gnss_scenarios_expose_hard_receiver_status_difference():
    config = _config()
    sim = _sim_config(config)
    benign = run_scenario(sim, "gnss_loss_holdover", 0)
    spoof = run_scenario(sim, "gnss_spoof", 0)
    jam = run_scenario(sim, "gnss_jam", 0)

    benign_active = benign[benign["label"] == "H0"]
    spoof_active = spoof[spoof["label"] == "H1"]
    jam_active = jam[jam["label"] == "H1"]
    assert set(benign_active["gnss_sync_status"]) <= {"ACQUIRING-SYNC", "HOLDOVER"}
    assert set(spoof_active["gnss_sync_status"]) == {"SYNCHRONIZED"}
    assert set(jam_active["gnss_sync_status"]) <= {"ACQUIRING-SYNC", "HOLDOVER"}
    assert spoof_active["satellites_tracked"].min() >= 8
    assert benign_active["satellites_tracked"].iloc[-1] == 0
    assert jam_active["satellites_tracked"].iloc[-1] == 0


def test_timesource_features_vary_without_exposing_raw_status():
    config = _config()
    telemetry = generate_telemetry(_sim_config(config), 3)
    windows = window_features(
        telemetry,
        float(config["dataset"]["window_s"]),
        float(config["dataset"]["step_s"]),
    )

    assert set(TIMESOURCE_FEATURE_COLUMNS).issubset(FEATURE_COLUMNS)
    assert "gnss_sync_status" not in FEATURE_COLUMNS
    assert "satellites_tracked" not in FEATURE_COLUMNS
    assert windows[TIMESOURCE_FEATURE_COLUMNS].nunique().max() > 1


def test_gnss_confusion_evaluation_has_both_feature_sets():
    config = _config()
    telemetry = generate_telemetry(_sim_config(config), 6)
    windows = window_features(
        telemetry,
        float(config["dataset"]["window_s"]),
        float(config["dataset"]["step_s"]),
    )
    matrix, recalls = evaluate_gnss_confusion(windows, int(config["seed"]))

    assert set(matrix["feature_set"]) == {
        "a_ptp_only",
        "b_ptp_timesource",
        "c_ptp_timesource_consistency",
    }
    assert matrix.groupby("feature_set")["windows"].sum().min() > 0
    assert {"gnss_loss_holdover", "gnss_spoof", "gnss_jam", "pooled_H1"}.issubset(
        set(recalls["scenario"])
    )


def test_benign_holdover_follows_configured_oscillator_envelope():
    config = _config()
    sim = _sim_config(config)
    benign = run_scenario(sim, "gnss_loss_holdover", 0)
    active = benign[benign["label"] == "H0"]
    lower = sim.holdover_nominal_drift_ppb - sim.holdover_tolerance_ppb
    upper = sim.holdover_nominal_drift_ppb + sim.holdover_tolerance_ppb

    assert active["freq_error_ppb"].between(lower, upper).mean() >= 0.95


def test_consistency_features_are_derived_and_nonconstant():
    config = _config()
    telemetry = generate_telemetry(_sim_config(config), 3)
    windows = window_features(
        telemetry,
        float(config["dataset"]["window_s"]),
        float(config["dataset"]["step_s"]),
    )

    assert set(CONSISTENCY_FEATURE_COLUMNS).issubset(FEATURE_COLUMNS)
    assert windows[CONSISTENCY_FEATURE_COLUMNS].nunique().min() > 1
    assert not set(CONSISTENCY_FEATURE_COLUMNS) & {"gnss_sync_status", "satellites_tracked"}


def test_stealth_spoof_stays_inside_holdover_envelope():
    config = _config()
    sim = _sim_config(config)
    stealth = run_scenario(sim, "gnss_spoof_stealth", 0)
    active = stealth[stealth["label"] == "H1"]
    lower = sim.holdover_nominal_drift_ppb - sim.holdover_tolerance_ppb
    upper = sim.holdover_nominal_drift_ppb + sim.holdover_tolerance_ppb

    assert set(active["gnss_sync_status"]) == {"SYNCHRONIZED"}
    assert active["freq_error_ppb"].between(lower, upper).mean() >= 0.95
