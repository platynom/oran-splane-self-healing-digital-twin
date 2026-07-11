from pathlib import Path

from benchmark.run import run_benchmark
from dataset.build import build_dataset
from discriminator.model import train_and_evaluate


def test_governed_loop_integration():
    config = {
        "seed": 1588,
        "time_error_budget_ns": 100.0,
        "failure_window_s": 2.0,
        "sim": {"dt_s": 0.02, "duration_s": 5.0, "noise_ns": 8.0, "base_delay_ns": 50000.0, "servo_gain": 0.26, "synce_gain": 0.08, "drift_ppb": 6.0},
        "dataset": {"scenarios_per_type": 3, "window_s": 0.4, "step_s": 0.2},
        "discriminator": {"test_size": 0.35, "random_state": 1588},
        "healing": {"anomaly_threshold_ns": 100.0, "decision_budget_s": 1.0, "actions": ["safe_default", "failover_lls_c1", "failover_lls_c2", "failover_lls_c3", "failover_gnss", "holdover", "isolate_rogue_master", "reroute_path"]},
    }
    root = Path("results/test_healing")
    windows = build_dataset(config, root / "dataset")
    clf, _ = train_and_evaluate(windows, config, root / "results")
    bench = run_benchmark(windows, clf, config, root / "results")
    governed = bench[bench["method"] == "governed_loop"].iloc[0]
    assert governed["recovery_success_rate"] >= 0.9
    assert governed["within_2s_rate"] == 1.0
