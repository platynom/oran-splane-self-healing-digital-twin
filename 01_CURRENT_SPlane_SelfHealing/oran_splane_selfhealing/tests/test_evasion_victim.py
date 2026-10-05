from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from evasion.victim_transformer import (
    FEATURE_NAMES,
    WINDOW_SIZE,
    CaptureSession,
    PacketTransformer,
    session_holdout,
    sliding_windows,
)


def _session(capture_id: str, family: str) -> CaptureSession:
    return CaptureSession(
        capture_id=capture_id,
        attack_family=family,
        packet_features=np.zeros((50, len(FEATURE_NAMES)), dtype=np.float32),
        packet_labels=np.r_[np.zeros(25, dtype=int), np.ones(25, dtype=int)],
        pcap_path=None,  # type: ignore[arg-type]
    )


def test_session_holdout_is_disjoint_and_family_covered() -> None:
    sessions = [
        _session("announce_1", "announce"),
        _session("announce_2", "announce"),
        _session("announce_3", "announce"),
        _session("sync_1", "sync_follow_up"),
        _session("sync_2", "sync_single_step"),
    ]
    train, test, _ = session_holdout(sessions)
    by_id = {item.capture_id: item.attack_family for item in sessions}

    assert set(train).isdisjoint(test)
    assert {"announce", "sync"} == {
        "announce" if by_id[item] == "announce" else "sync" for item in train
    }
    assert {"announce", "sync"} == {
        "announce" if by_id[item] == "announce" else "sync" for item in test
    }


def test_sliding_windows_use_stride_two_and_any_attack_label() -> None:
    features = np.arange(50 * len(FEATURE_NAMES), dtype=np.float32).reshape(50, -1)
    labels = np.zeros(50, dtype=int)
    labels[41] = 1

    windows, targets = sliding_windows(features, labels)

    assert windows.shape == (6, WINDOW_SIZE, len(FEATURE_NAMES))
    assert np.array_equal(windows[1, 0], features[2])
    assert targets.tolist() == [0, 1, 1, 1, 1, 1]


def test_packet_transformer_cpu_forward_shape() -> None:
    model = PacketTransformer()
    packets = torch.zeros(3, WINDOW_SIZE, len(FEATURE_NAMES))

    logits = model(packets)

    assert logits.shape == (3,)
    assert logits.device.type == "cpu"
