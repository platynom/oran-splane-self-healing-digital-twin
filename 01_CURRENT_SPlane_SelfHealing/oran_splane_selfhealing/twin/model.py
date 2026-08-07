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


MIN_FIDELITY = 0.15


def fidelity_score(window: pd.Series) -> float:
    required = ("pdv_std", "msg_irregularity", "seq_regressions")
    if any(key not in window or pd.isna(window[key]) for key in required):
        return MIN_FIDELITY
    if "telemetry_valid" in window and not bool(window["telemetry_valid"]):
        return MIN_FIDELITY
    # Fail-closed: an absent fraction is only tolerated when the window explicitly
    # asserts telemetry_valid=True. A twin that cannot prove its inputs were
    # observed must not report high trust -- the `fidelity < 0.35` fallback in
    # healing/loop.py is the last guard before the loop acts on a forecast.
    valid_fraction = None
    for key in ("valid_sample_fraction", "valid_sample_rate"):
        if key in window:
            valid_fraction = window[key]
            break
    if valid_fraction is None:
        if "telemetry_valid" not in window:
            return MIN_FIDELITY
    elif pd.isna(valid_fraction) or float(valid_fraction) < 1.0:
        return MIN_FIDELITY
    # Direct reads: the guard above already proved these keys exist and are
    # finite, so a silent `.get(..., 0.0)` default here would only be able to
    # hide a future regression.
    penalty = 0.0
    penalty += min(float(window["pdv_std"]) / 220.0, 0.35)
    penalty += min(float(window["msg_irregularity"]) * 0.35, 0.35)
    penalty += min(float(window["seq_regressions"]) * 0.08, 0.25)
    return max(MIN_FIDELITY, 1.0 - penalty)


def _resolve_action(action: str) -> str:
    if action in ACTION_EFFECT:
        return action
    for k in ACTION_EFFECT:
        if k.startswith(action) or action.startswith(k):
            return k
    return "safe_default"


def forecast_action(window: pd.Series, action: str, horizon_s: float = 1.0, dt_s: float = 0.1) -> Forecast:
    current = float(window["offset_abs_max"])
    decay, floor = ACTION_EFFECT[_resolve_action(action)]
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
