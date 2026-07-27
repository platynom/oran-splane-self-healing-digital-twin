from __future__ import annotations

import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fronthaul_sim.simulator import SimConfig
from stats.multiseed import ci95, leave_one_attack_out, run_multiseed
from stats.twin_validation import twin_action_consistency


def _small_config() -> dict:
    with (ROOT / "config" / "default.yaml").open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg = copy.deepcopy(cfg)
    cfg["dataset"]["scenarios_per_type"] = 6   # keep the test fast
    return cfg


def test_ci95_math():
    mean, half, sd = ci95([0.9, 0.92, 0.88, 0.91])
    assert 0.88 < mean < 0.92
    assert half > 0


def test_multiseed_produces_bounded_cis(tmp_path):
    cfg = _small_config()
    summary = run_multiseed(cfg, seeds=[1, 2, 3], out_dir=tmp_path)
    assert set(summary["metric"]) >= {"accuracy", "recovery_success_rate"}
    for _, r in summary.iterrows():
        # a t-interval on a metric near 1.0 can extend slightly past 1.0; only
        # require internal consistency and non-negative halfwidth.
        assert r["ci95_low"] <= r["mean"] <= r["ci95_high"]
        assert r["ci95_halfwidth"] >= 0
    acc = summary[summary["metric"] == "accuracy"].iloc[0]
    assert acc["mean"] > 0.75   # discriminator clearly better than chance across seeds


def test_leave_one_attack_out_runs(tmp_path):
    cfg = _small_config()
    logo = leave_one_attack_out(cfg, seed=1, out_dir=tmp_path)
    assert not logo.empty
    assert (logo["unseen_attack_recall"] >= 0).all()


def test_twin_consistency_positive(tmp_path):
    cfg = _small_config()
    base = SimConfig(seed=cfg["seed"], time_error_budget_ns=cfg["time_error_budget_ns"], **cfg["sim"])
    df = twin_action_consistency(base, tmp_path)
    # twin action ranking should positively track the simulator's action effects
    assert df.attrs["spearman_r"] > 0.3
