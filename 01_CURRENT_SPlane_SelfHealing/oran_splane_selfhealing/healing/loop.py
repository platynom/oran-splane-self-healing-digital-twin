from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import pandas as pd

from telemetry.features import FEATURE_COLUMNS
from twin.model import forecast_all


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    label_estimate: str
    decision_time_s: float
    within_budget: bool
    forecast_peak_ns: float


ATTACK_ACTIONS = ["isolate_rogue_master", "failover_gnss", "failover_lls_c1", "safe_default"]
FAULT_ACTIONS = ["failover_lls_c1", "failover_lls_c2", "reroute_path", "holdover", "safe_default"]


def detect(window: pd.Series, threshold_ns: float) -> bool:
    return bool(float(window["offset_abs_max"]) > threshold_ns or float(window["pdv_std"]) > threshold_ns)


def choose_action(window: pd.Series, clf, config: dict) -> Decision:
    start = perf_counter()
    threshold = float(config["healing"]["anomaly_threshold_ns"])
    budget = float(config["healing"]["decision_budget_s"])
    if not detect(window, threshold):
        elapsed = perf_counter() - start
        return Decision("safe_default", "no anomaly above configured threshold", "healthy", elapsed, elapsed < budget, float(window["offset_abs_max"]))

    X = pd.DataFrame([window[FEATURE_COLUMNS].to_dict()])
    label = str(clf.predict(X)[0])
    candidates = ATTACK_ACTIONS if label == "H1" else FAULT_ACTIONS
    forecasts = forecast_all(window, candidates)
    safe = forecasts[forecasts["action"] == "safe_default"]["steady_abs_error_ns"].min()
    ranked = forecasts.sort_values(["steady_abs_error_ns", "peak_abs_error_ns"])
    best = ranked.iloc[0]
    if float(best["fidelity"]) < 0.35:
        best = forecasts[forecasts["action"] == "safe_default"].iloc[0]
        reason = "low twin fidelity; conservative safe default"
    elif float(best["steady_abs_error_ns"]) <= safe:
        reason = f"{label} candidate beats or matches safe default in twin"
    else:
        best = forecasts[forecasts["action"] == "safe_default"].iloc[0]
        reason = "no candidate beat safe default"
    elapsed = perf_counter() - start
    return Decision(str(best["action"]), reason, label, elapsed, elapsed < budget, float(best["peak_abs_error_ns"]))
