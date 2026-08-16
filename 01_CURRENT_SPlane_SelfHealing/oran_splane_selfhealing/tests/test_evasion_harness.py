from __future__ import annotations

import pytest

from evasion.harness import (
    ReplayParameters,
    generate_replay_telemetry,
    phase0_packet_features,
    write_replay_pcap,
)
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


def test_transformer_features_come_from_serialized_packet_bytes(tmp_path) -> None:
    pytest.importorskip("torch")
    telemetry = generate_replay_telemetry(
        ReplayParameters(
            magnitude_ns=140.0,
            injection_cadence_s=0.04,
            forged_fields=("sequence_id", "origin_timestamp"),
        )
    )
    pcap = tmp_path / "candidate.pcap"
    labels = write_replay_pcap(telemetry, pcap)
    features = phase0_packet_features(pcap)

    assert len(features) == len(labels) == 4 * len(telemetry)
    assert set(features[:, 0]) == {0.0, 1.0}  # decoded from the two source MACs
    assert set(features[:, 1]) == {58.0}  # actual serialized Ethernet frame length
