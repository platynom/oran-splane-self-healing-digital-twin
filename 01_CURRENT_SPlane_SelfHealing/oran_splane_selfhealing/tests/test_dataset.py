from pathlib import Path

from dataset.build import build_dataset
from telemetry.features import label_integrity


def test_label_integrity():
    config = {
        "seed": 1588,
        "time_error_budget_ns": 100.0,
        "sim": {"dt_s": 0.02, "duration_s": 4.0, "noise_ns": 8.0, "base_delay_ns": 50000.0, "servo_gain": 0.26, "synce_gain": 0.08, "drift_ppb": 6.0},
        "dataset": {"scenarios_per_type": 2, "window_s": 0.4, "step_s": 0.2},
    }
    windows = build_dataset(config, Path("results/test_dataset"))
    assert label_integrity(windows)
    assert {"healthy", "H0", "H1"}.issubset(set(windows["label"]))
