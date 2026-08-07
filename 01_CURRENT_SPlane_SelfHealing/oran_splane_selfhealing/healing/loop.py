from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd

from discriminator.openset import TemporalPersistence
from telemetry.features import configured_feature_columns
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


VALIDITY_FRACTION_KEYS = ("valid_sample_fraction", "valid_sample_rate")
REQUIRED_DECISION_FEATURES = ("offset_abs_max", "path_delay_mean", "pdv_std")


def telemetry_is_valid(window: pd.Series) -> bool:
    """Return False for missing, stale, or insufficiently observed timing inputs.

    Fail-CLOSED by construction. A window that does not *prove* it was built from
    observed telemetry is treated as invalid, because the original live defect was
    caused by exactly the opposite convention: an absent/zero value being read as
    "healthy". Provenance must be asserted, never assumed.
    """
    # 1. Explicit invalidity always wins.
    if "telemetry_valid" in window and not bool(window["telemetry_valid"]):
        return False

    # 2. Validity metadata must be PRESENT. A window carrying no provenance is
    #    untrusted: absence of evidence is not evidence of health.
    fraction = None
    for key in VALIDITY_FRACTION_KEYS:
        if key in window:
            fraction = window[key]
            break
    if fraction is None:
        # Tolerated only if the window explicitly asserts telemetry_valid=True.
        if "telemetry_valid" not in window:
            return False
    elif pd.isna(fraction) or float(fraction) < 1.0:
        return False

    # 3. The features the decision path actually reads must be present and finite.
    for name in REQUIRED_DECISION_FEATURES:
        if name not in window:
            return False
        value = window[name]
        if pd.isna(value) or not np.isfinite(float(value)):
            return False
    return True


class GovernedHealingLoop:
    """Stateful sequential wrapper that applies configured decision persistence."""

    def __init__(self, clf, config: dict, novelty_detector=None) -> None:
        persistence = config.get("openset", {}).get("persistence", {})
        self.clf = clf
        self.config = config
        self.novelty_detector = novelty_detector
        self.persistence = TemporalPersistence(
            int(persistence.get("n", 2)),
            int(persistence.get("m", 3)),
        )

    def decide(self, window: pd.Series) -> Decision:
        return choose_action(
            window,
            self.clf,
            self.config,
            self.novelty_detector,
            self.persistence,
        )

    def reset(self) -> None:
        self.persistence.reset()


def choose_action(
    window: pd.Series,
    clf,
    config: dict,
    novelty_detector=None,
    persistence_state: TemporalPersistence | None = None,
) -> Decision:
    start = perf_counter()
    threshold = float(config["healing"]["anomaly_threshold_ns"])
    budget = float(config["healing"]["decision_budget_s"])
    openset = config.get("openset", {})
    persistence_config = openset.get("persistence", {})
    persistence_enabled = bool(persistence_config.get("enabled", False)) and persistence_state is not None
    if not telemetry_is_valid(window):
        # Invalid is deliberately its own persistence channel. It must never be
        # averaged into a normal feature vector or short-circuited as healthy.
        persisted_invalid = persistence_state.update(True, "invalid") if persistence_enabled else True
        elapsed = perf_counter() - start
        if persistence_enabled and not persisted_invalid:
            return Decision(
                "safe_default",
                "telemetry invalid or missing; protective candidate awaiting temporal persistence",
                "PENDING",
                elapsed,
                elapsed < budget,
                float(window.get("offset_abs_max", float("nan"))),
            )
        return Decision(
            "safe_default",
            "telemetry invalid or missing; conservative safe response",
            "UNKNOWN",
            elapsed,
            elapsed < budget,
            float(window.get("offset_abs_max", float("nan"))),
        )
    if not detect(window, threshold):
        elapsed = perf_counter() - start
        return Decision("safe_default", "no anomaly above configured threshold", "healthy", elapsed, elapsed < budget, float(window["offset_abs_max"]))

    features = list(getattr(clf, "feature_columns_", configured_feature_columns(config)))
    X = pd.DataFrame([window[features].to_dict()])
    if novelty_detector is None:
        novelty_detector = getattr(clf, "novelty_detector_", None)
    raw_novel = False
    if bool(openset.get("enabled", False)) and novelty_detector is not None:
        raw_novel = bool(novelty_detector.predict_novel(X)[0])
        if raw_novel and not persistence_enabled:
            elapsed = perf_counter() - start
            return Decision(
                "safe_default",
                "out-of-distribution / novel; conservative safe response",
                "UNKNOWN",
                elapsed,
                elapsed < budget,
                float(window["offset_abs_max"]),
            )
    raw_label = str(clf.predict(X)[0])
    raw_h1 = raw_label == "H1"
    if persistence_enabled:
        novel = persistence_state.update(raw_novel, "novel")
        h1 = (
            persistence_state.update(raw_h1, "h1")
            if bool(persistence_config.get("apply_to_h1", True))
            else raw_h1
        )
        if novel:
            elapsed = perf_counter() - start
            return Decision(
                "safe_default",
                "persistent out-of-distribution / novel; conservative safe response",
                "UNKNOWN",
                elapsed,
                elapsed < budget,
                float(window["offset_abs_max"]),
            )
        if (raw_novel or raw_h1) and not h1:
            elapsed = perf_counter() - start
            return Decision(
                "safe_default",
                "protective candidate awaiting temporal persistence",
                "PENDING",
                elapsed,
                elapsed < budget,
                float(window["offset_abs_max"]),
            )
        label = "H1" if h1 else raw_label
    else:
        label = raw_label
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
