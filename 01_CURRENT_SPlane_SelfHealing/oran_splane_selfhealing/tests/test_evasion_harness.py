from __future__ import annotations

import pytest

from evasion.harness import ReplayParameters, generate_replay_telemetry
from telemetry.features import window_features


def test_replay_parameters_reject_feature_space_or_unknown_fields() -> None:
    params = ReplayParameters(
        magnitude_ns=120.0,
        injection_cadence_s=0.1,
        forged_fields=("offset_abs_max",),
    )
    with pytest.raises(ValueError, match="unsupported replay fields"):
        params.validate(dt_s=0.02)


def test_replay_candidate_is_realizable_and_measurable() -> None:
    params = ReplayParameters(
        magnitude_ns=140.0,
        injection_cadence_s=0.04,
        forged_fields=("sequence_id", "origin_timestamp"),
        ramp_rate_ns_per_s=30.0,
    )
    telemetry = generate_replay_telemetry(params)
    assert telemetry["attack_flag"].any()
    assert (telemetry.loc[telemetry["attack_flag"], "label"] == "H1").all()
    windows = window_features(telemetry, window_s=0.4, step_s=0.2)
    assert windows.loc[windows["label"] == "H1", "offset_abs_max"].max() >= 100.0
