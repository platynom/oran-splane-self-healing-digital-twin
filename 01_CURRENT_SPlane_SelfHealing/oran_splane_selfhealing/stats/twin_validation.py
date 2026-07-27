from __future__ import annotations

"""Validate the digital twin two ways:

1. Action-model consistency: does the twin's per-action steady-error ranking match
   what the actual fronthaul simulator produces when that action is applied? A twin
   used to *choose* actions must at least order them like the ground-truth physics.
   Metric: Pearson r and rank correlation across the action set + MAE.

2. Fidelity-score behaviour: does the fidelity score fall as the telemetry it reads
   degrades (PDV, message irregularity, sequence regressions)? A trust score that
   does not drop on degraded input is useless. Metric: correlation of fidelity vs
   those degradation features (expected negative).

Honest caveat recorded in the output: fully *calibrating* twin fidelity against
real prediction error needs hardware-timestamped ground truth; this validates
internal consistency and intended behaviour, which is what is checkable in emulation.
"""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sstats

from fronthaul_sim.simulator import SimConfig, apply_action_config, simulate
from twin.model import ACTION_EFFECT, fidelity_score, forecast_action


def _sim_steady_for_action(base: SimConfig, action: str, n_runs: int = 6, tail: int = 60) -> float:
    vals = []
    for r in range(n_runs):
        cfg = apply_action_config(replace(base, seed=base.seed + 1000 + r), action)
        df = simulate(cfg, scenario=action)
        vals.append(float(df.tail(tail)["offset_ns"].abs().mean()))
    return float(np.mean(vals))


def twin_action_consistency(base: SimConfig, out_dir: Path) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    actions = list(ACTION_EFFECT.keys())
    # a representative post-anomaly window (elevated current error)
    window = pd.Series({"offset_abs_max": 300.0, "pdv_std": 40.0, "msg_irregularity": 0.0, "seq_regressions": 0.0})
    rows = []
    for a in actions:
        twin_steady = forecast_action(window, a).steady_abs_error_ns
        sim_steady = _sim_steady_for_action(base, a)
        rows.append({"action": a, "twin_steady_ns": twin_steady, "sim_steady_ns": sim_steady})
    df = pd.DataFrame(rows)
    pear = float(sstats.pearsonr(df["twin_steady_ns"], df["sim_steady_ns"])[0])
    spear = float(sstats.spearmanr(df["twin_steady_ns"], df["sim_steady_ns"])[0])
    df.attrs["pearson_r"] = pear
    df.attrs["spearman_r"] = spear
    df.attrs["mae_ns"] = float(np.abs(df["twin_steady_ns"] - df["sim_steady_ns"]).mean())
    df.to_csv(out_dir / "twin_action_consistency.csv", index=False)
    return df


def fidelity_behaviour(windows: pd.DataFrame, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    fid = windows.apply(fidelity_score, axis=1)
    out = {}
    for feat in ["pdv_std", "msg_irregularity", "seq_regressions"]:
        if windows[feat].std(ddof=0) > 0:
            out[f"corr_fidelity_vs_{feat}"] = float(np.corrcoef(fid, windows[feat])[0, 1])
    out["fidelity_min"] = float(fid.min())
    out["fidelity_max"] = float(fid.max())
    out["fidelity_mean"] = float(fid.mean())
    pd.DataFrame([out]).to_csv(out_dir / "fidelity_behaviour.csv", index=False)
    return out
