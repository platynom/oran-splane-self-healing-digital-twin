from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.calibrate_real import _session_holdout, _wilson95


def test_session_holdout_never_splits_a_capture():
    rows = []
    for label, is_attack in (("benign", False), ("attack", True)):
        for session in range(4):
            for window in range(5):
                rows.append(
                    {
                        "capture_id": f"{label}_{session}",
                        "is_attack": is_attack,
                        "window": window,
                    }
                )
    train, test = _session_holdout(pd.DataFrame(rows), seed=1588)
    assert set(train["capture_id"]).isdisjoint(set(test["capture_id"]))
    assert train["is_attack"].nunique() == 2
    assert test["is_attack"].nunique() == 2


def test_wilson_interval_contains_observed_rate():
    low, high = _wilson95(20, 100)
    assert low < 0.2 < high
