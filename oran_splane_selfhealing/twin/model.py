from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Forecast:
    action: str
    peak_abs_error_ns: float
    steady_abs_error_ns: float
    fidelity: float
    forecast: list[float]


ACTION_EFFECT = {
    "safe_default": (0.78, 3.0),
    "failover_lls_c1": (0.48, 4.0),
    "failover_lls_c2": (0.52, 4.2),
    "failover_lls_c3": (0.58, 4.5),
    "failover_gnss": (0.42, 3.5),
    "holdover": (1.04, 9.0),
    "isolate_rogue_master": (0.35, 3.0),
    "reroute_path": (0.62, 5.0),
}


def fidelity_score(window: pd.Series) -> float:
    penalty = 0.0
    penalty += min(float(window.get("pdv_std", 0.0)) / 220.0, 0.35)
    penalty += min(float(window.get("msg_irregularity", 0.0)) * 0.35, 0.35)
    penalty += min(float(window.get("seq_regressions", 0.0)) * 0.08, 0.25)
    return max(0.15, 1.0 - penalty)


def forecast_action(window: pd.Series, action: str, horizon_s: float = 1.0, dt_s: float = 0.1) -> Forecast:
    current = float(window["offset_abs_max"])
    decay, floor = ACTION_EFFECT[action]
    steps = max(1, int(horizon_s / dt_s))
    values = []
    val = current
    for _ in range(steps):
        val = abs(val * decay) + floor
        values.append(float(val))
    fid = fidelity_score(window)
    return Forecast(action, max(values), float(np.mean(values[-3:])), fid, values)


def forecast_all(window: pd.Series, actions: list[str]) -> pd.DataFrame:
    return pd.DataFrame([forecast_action(window, a).__dict__ for a in actions])
