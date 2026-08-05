from __future__ import annotations

from pathlib import Path

import yaml

from faults.injectors import generate_telemetry, run_scenario
from fronthaul_sim.simulator import SimConfig
from telemetry.features import (
    CROSS_SOURCE_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    configured_feature_columns,
    window_features,
)


ROOT = Path(__file__).resolve().parents[1]


def _config() -> tuple[dict, SimConfig]:
    config = yaml.safe_load((ROOT / "config" / "default.yaml").read_text(encoding="utf-8"))
    sim = SimConfig(
        seed=int(config["seed"]),
        time_error_budget_ns=float(config["time_error_budget_ns"]),
        **config["sim"],
        **config.get("oscillator", {}),
        **config.get("time_sources", {}),
    )
    return config, sim


def _active(frame, label: str):
    return frame[frame["label"] == label]


def test_healthy_independent_references_agree_within_tolerance():
    _, sim = _config()
    healthy = run_scenario(sim, "healthy", 0)
    values = healthy[["gnss_reference_ns", "ptp_reference_ns", "peer_reference_ns"]]
    disagreement = values.max(axis=1) - values.min(axis=1)

    assert (disagreement <= sim.source_agreement_tolerance_ns).mean() >= 0.98


def test_single_source_and_coherent_spoofs_have_distinct_disagreement():
    _, sim = _config()
    single = _active(run_scenario(sim, "gnss_spoof_single_source", 0), "H1")
    coherent = _active(run_scenario(sim, "gnss_spoof_all_sources", 0), "H1")

    def mean_disagreement(frame):
        values = frame[["gnss_reference_ns", "ptp_reference_ns", "peer_reference_ns"]]
        return float((values.max(axis=1) - values.min(axis=1)).mean())

    assert mean_disagreement(single) > mean_disagreement(coherent) * 3.0
    assert set(single["gnss_sync_status"]) == {"SYNCHRONIZED"}
    assert set(coherent["gnss_sync_status"]) == {"SYNCHRONIZED"}


def test_benign_disagreement_confounders_remain_h0():
    _, sim = _config()
    peer = _active(run_scenario(sim, "peer_source_degraded", 0), "H0")
    path = _active(run_scenario(sim, "path_asymmetry_benign", 0), "H0")

    assert not peer.empty and not path.empty
    assert peer["peer_reference_ns"].abs().max() > sim.source_agreement_tolerance_ns
    assert path["ptp_reference_ns"].abs().max() > sim.source_agreement_tolerance_ns


def test_cross_source_features_vary_without_raw_reference_leakage():
    config, sim = _config()
    telemetry = generate_telemetry(sim, 3)
    windows = window_features(
        telemetry,
        float(config["dataset"]["window_s"]),
        float(config["dataset"]["step_s"]),
    )

    assert set(CROSS_SOURCE_FEATURE_COLUMNS).isdisjoint(FEATURE_COLUMNS)
    assert set(CROSS_SOURCE_FEATURE_COLUMNS).issubset(
        configured_feature_columns({"features": {"cross_source": {"enabled": True}}})
    )
    assert windows[CROSS_SOURCE_FEATURE_COLUMNS].nunique().min() > 1
    assert not {"gnss_reference_ns", "ptp_reference_ns", "peer_reference_ns"} & set(FEATURE_COLUMNS)
