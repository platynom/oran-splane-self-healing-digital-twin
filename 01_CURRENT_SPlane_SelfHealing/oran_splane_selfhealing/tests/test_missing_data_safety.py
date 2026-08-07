from __future__ import annotations

"""Fail-CLOSED behaviour on missing / invalid telemetry.

Regression tests for the live-validation finding: under severe loss `pmc` returned
zero-valued timing fields, which `detect()` read as "no anomaly" and reported as
healthy -- bypassing the novelty detector, the classifier and persistence entirely.

A timing-security system must never treat "I received nothing" as "everything is
fine". These tests pin the safe behaviour.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from healing.loop import GovernedHealingLoop, choose_action
from ingest.schema import coerce_telemetry
from telemetry.features import configured_feature_columns
from twin.model import fidelity_score

NO_ANOMALY_REASON = "no anomaly above configured threshold"


def _config() -> dict:
    return {
        "healing": {"anomaly_threshold_ns": 100.0, "decision_budget_s": 1.0},
        "openset": {"enabled": False, "persistence": {"enabled": True, "n": 2, "m": 3}},
        "features": {"cross_source": {"enabled": False}},
    }


class _DummyClf:
    """Must never be reached for invalid telemetry; explodes if it is."""

    def predict(self, X):  # pragma: no cover - reaching this is the failure
        raise AssertionError("classifier reached with invalid telemetry")


def _window(valid_sample_rate: float = 1.0, **overrides) -> pd.Series:
    data = {col: 0.0 for col in configured_feature_columns(_config())}
    data["valid_sample_rate"] = valid_sample_rate
    data.update(overrides)
    return pd.Series(data)


def _pmc_frame(offset, delay, n=5):
    """Telemetry as live_collect would emit it."""
    return pd.DataFrame(
        {
            "t_s": np.arange(n) * 0.1,
            "offset_ns": [offset] * n,
            "path_delay_ns": [delay] * n,
            "ptp_seq_id": np.arange(n),
        }
    )


# --- a) missing telemetry must not be called healthy -------------------------

def test_absent_pmc_sample_is_not_healthy():
    decision = choose_action(_window(valid_sample_rate=0.0), _DummyClf(), _config())
    assert decision.label_estimate != "healthy"
    assert decision.reason != NO_ANOMALY_REASON


# --- b) it must be UNKNOWN and take the conservative action ------------------

def test_absent_pmc_sample_routes_to_unknown_safe_default():
    decision = choose_action(_window(valid_sample_rate=0.0), _DummyClf(), _config())
    assert decision.label_estimate == "UNKNOWN"
    assert decision.action == "safe_default"
    assert "invalid" in decision.reason.lower() or "missing" in decision.reason.lower()


# --- c) a real 0 ns offset must be distinguishable from "never observed" -----

def test_true_zero_offset_distinguishable_from_missing():
    genuine = coerce_telemetry(_pmc_frame(0.0, 50_000.0))
    absent = coerce_telemetry(_pmc_frame(np.nan, np.nan))
    assert "telemetry_valid" in genuine.columns
    assert bool(genuine["telemetry_valid"].all()) is True
    assert bool(absent["telemetry_valid"].any()) is False


# --- d) a sustained outage must stay protective, never "no anomaly" ----------

def test_sustained_no_data_stays_protective():
    loop = GovernedHealingLoop(_DummyClf(), _config())
    decisions = [loop.decide(_window(valid_sample_rate=0.0)) for _ in range(5)]
    assert all(d.reason != NO_ANOMALY_REASON for d in decisions)
    assert all(d.action == "safe_default" for d in decisions)
    assert all(d.label_estimate != "healthy" for d in decisions)


# --- e) no regression: genuine healthy traffic stays healthy -----------------

def test_genuine_healthy_window_still_healthy():
    healthy = _window(valid_sample_rate=1.0, offset_abs_max=12.0, pdv_std=8.0)
    decision = choose_action(healthy, _DummyClf(), _config())
    assert decision.label_estimate == "healthy"
    assert decision.reason == NO_ANOMALY_REASON


# --- f) the twin must not report perfect trust when inputs are missing -------

def test_twin_fidelity_fails_closed_on_missing_features():
    # A trusted window must carry provenance (see hardening below): fidelity
    # inputs alone are not sufficient evidence that they were observed.
    complete = pd.Series(
        {
            "pdv_std": 5.0,
            "msg_irregularity": 0.0,
            "seq_regressions": 0.0,
            "valid_sample_fraction": 1.0,
        }
    )
    missing = pd.Series({"offset_abs_max": 300.0})  # fidelity inputs absent
    assert fidelity_score(complete) > 0.9
    # Missing inputs must NOT look maximally trustworthy; must trip the
    # conservative `fidelity < 0.35` fallback in healing/loop.py.
    assert fidelity_score(missing) < 0.35


def test_twin_fidelity_fails_closed_on_nan_features():
    nan_window = pd.Series(
        {"pdv_std": np.nan, "msg_irregularity": np.nan, "seq_regressions": np.nan}
    )
    assert fidelity_score(nan_window) < 0.35


# --- g) HARDENING: a window with NO provenance metadata must be untrusted ----
#
# The original defect was caused by a permissive default (missing -> 0.0 -> healthy).
# A window that cannot prove it was built from observed telemetry must therefore be
# rejected outright, rather than assumed healthy.

def test_window_without_validity_metadata_is_untrusted():
    from healing.loop import telemetry_is_valid

    bare = pd.Series({"offset_abs_max": 0.0, "path_delay_mean": 0.0, "pdv_std": 0.0})
    assert telemetry_is_valid(bare) is False
    decision = choose_action(bare, _DummyClf(), _config())
    assert decision.label_estimate == "UNKNOWN"
    assert decision.action == "safe_default"


def test_infinite_feature_values_are_untrusted():
    from healing.loop import telemetry_is_valid

    window = _window(valid_sample_rate=1.0, offset_abs_max=np.inf)
    assert telemetry_is_valid(window) is False


def test_twin_fidelity_untrusted_without_provenance():
    bare = pd.Series({"pdv_std": 5.0, "msg_irregularity": 0.0, "seq_regressions": 0.0})
    assert fidelity_score(bare) < 0.35
    trusted = pd.Series(
        {
            "pdv_std": 5.0,
            "msg_irregularity": 0.0,
            "seq_regressions": 0.0,
            "valid_sample_fraction": 1.0,
        }
    )
    assert fidelity_score(trusted) > 0.9
