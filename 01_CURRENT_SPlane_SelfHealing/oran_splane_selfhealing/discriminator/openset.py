from __future__ import annotations

"""Open-set novelty detection for S-plane telemetry windows."""

from collections import deque

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from telemetry.features import (
    CONSISTENCY_FEATURE_COLUMNS,
    CROSS_SOURCE_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    TIMESOURCE_FEATURE_COLUMNS,
)


def apply_persistence(flags: np.ndarray | list[bool], n: int, m: int) -> np.ndarray:
    """Apply an N-of-M rolling vote; 1-of-1 exactly preserves input flags."""
    if n < 1 or m < 1 or n > m:
        raise ValueError("persistence requires 1 <= n <= m")
    values = np.asarray(flags, dtype=bool)
    history: deque[bool] = deque(maxlen=m)
    persisted = np.zeros(len(values), dtype=bool)
    for index, flag in enumerate(values):
        history.append(bool(flag))
        persisted[index] = len(history) >= n and sum(history) >= n
    return persisted


class TemporalPersistence:
    """Stateful independent N-of-M histories for live decision channels."""

    def __init__(self, n: int = 2, m: int = 3) -> None:
        if n < 1 or m < 1 or n > m:
            raise ValueError("persistence requires 1 <= n <= m")
        self.n = int(n)
        self.m = int(m)
        self._histories: dict[str, deque[bool]] = {}

    def update(self, flag: bool, channel: str = "protective") -> bool:
        history = self._histories.setdefault(channel, deque(maxlen=self.m))
        history.append(bool(flag))
        return len(history) >= self.n and sum(history) >= self.n

    def reset(self) -> None:
        self._histories.clear()


class NoveltyDetector:
    """Calibrated global or feature-group Isolation Forest novelty detector."""

    def __init__(
        self,
        target_known_flag_rate: float = 0.02,
        random_state: int = 1588,
        mode: str = "group",
        feature_columns: list[str] | None = None,
        group_budget_weights: dict[str, float] | None = None,
    ) -> None:
        if not 0.0 < target_known_flag_rate < 0.5:
            raise ValueError("target_known_flag_rate must be between 0 and 0.5")
        if mode not in {"global", "group"}:
            raise ValueError("mode must be 'global' or 'group'")
        self.target_known_flag_rate = float(target_known_flag_rate)
        self.random_state = int(random_state)
        self.mode = mode
        self.feature_columns = list(feature_columns or FEATURE_COLUMNS)
        self.group_budget_weights = dict(group_budget_weights or {})
        self.scalers_: dict[str, StandardScaler] = {}
        self.models_: dict[str, IsolationForest] = {}
        self.group_columns_: dict[str, list[str]] = {}
        self.thresholds_: dict[str, float] = {}
        self.inclusive_thresholds_: dict[str, bool] = {}
        self.per_group_target_rate_: float | None = None
        self.per_group_target_rates_: dict[str, float] = {}
        self.threshold_: float | None = None
        self.calibration_size_: int = 0

    def _frame(self, X: pd.DataFrame | np.ndarray) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            return X[self.feature_columns].astype(float)
        values = np.asarray(X, dtype=float)
        if values.ndim != 2 or values.shape[1] != len(self.feature_columns):
            raise ValueError(f"expected a 2D array with {len(self.feature_columns)} features")
        return pd.DataFrame(values, columns=self.feature_columns)

    def _groups(self) -> dict[str, list[str]]:
        if self.mode == "global":
            return {"global": self.feature_columns}
        bmca_prefixes = ("gm_identity_", "clock_class_", "steps_removed_", "priority1_")
        bmca = [name for name in self.feature_columns if name.startswith(bmca_prefixes)]
        rate = [name for name in self.feature_columns if name.startswith("msg_rate_")]
        protocol = [name for name in self.feature_columns if name in {"seq_regressions", "msg_irregularity"}]
        timesource = [name for name in self.feature_columns if name in TIMESOURCE_FEATURE_COLUMNS]
        consistency = [name for name in self.feature_columns if name in CONSISTENCY_FEATURE_COLUMNS]
        cross_source = [name for name in self.feature_columns if name in CROSS_SOURCE_FEATURE_COLUMNS]
        timing = [
            name for name in self.feature_columns
            if name not in set(bmca + rate + protocol + timesource + consistency + cross_source)
        ]
        groups = {
            "timing": timing,
            "protocol": protocol,
            "rate": rate,
            "bmca": bmca,
            "timesource": timesource,
            "consistency": consistency,
            "cross_source": cross_source,
        }
        return {name: columns for name, columns in groups.items() if columns}

    def fit(self, X_train: pd.DataFrame | np.ndarray) -> "NoveltyDetector":
        frame = self._frame(X_train)
        if len(frame) < 20:
            raise ValueError("at least 20 known windows are required to calibrate novelty")
        self.group_columns_ = {
            name: columns
            for name, columns in self._groups().items()
            if any(frame[column].nunique(dropna=False) > 1 for column in columns)
        }
        group_count = len(self.group_columns_)
        weights = {name: float(self.group_budget_weights.get(name, 1.0)) for name in self.group_columns_}
        weight_total = sum(weights.values())
        if weight_total <= 0:
            raise ValueError("group novelty budget weights must have a positive sum")
        self.per_group_target_rates_ = {
            name: 1.0 - (1.0 - self.target_known_flag_rate) ** (weight / weight_total)
            for name, weight in weights.items()
        }
        self.per_group_target_rate_ = max(self.per_group_target_rates_.values())
        self.scalers_ = {}
        self.models_ = {}
        for index, (name, columns) in enumerate(self.group_columns_.items()):
            scaler = StandardScaler()
            scaled = scaler.fit_transform(frame[columns])
            model = IsolationForest(
                n_estimators=200,
                contamination="auto",
                random_state=self.random_state + index,
                n_jobs=1,
            ).fit(scaled)
            self.scalers_[name] = scaler
            self.models_[name] = model
        self.calibrate(frame)
        return self

    def calibrate(self, X_known: pd.DataFrame | np.ndarray) -> "NoveltyDetector":
        """Set thresholds on known data independent of detector fitting when available."""
        if not self.models_:
            raise RuntimeError("NoveltyDetector.fit must be called before calibrate")
        frame = self._frame(X_known)
        if frame.empty:
            raise ValueError("novelty calibration requires at least one known window")
        self.thresholds_ = {}
        self.inclusive_thresholds_ = {}
        for name, scores in self._raw_group_scores(frame).items():
            target_rate = self.per_group_target_rates_[name]
            threshold = float(
                np.quantile(scores, 1.0 - target_rate, method="higher")
            )
            self.thresholds_[name] = threshold
            self.inclusive_thresholds_[name] = bool(
                np.mean(scores >= threshold) <= target_rate
            )
        self.calibration_size_ = len(frame)
        self.threshold_ = max(self.thresholds_.values())
        return self

    def _raw_group_scores(self, frame: pd.DataFrame) -> dict[str, np.ndarray]:
        return {
            name: -self.models_[name].score_samples(self.scalers_[name].transform(frame[columns]))
            for name, columns in self.group_columns_.items()
        }

    def group_scores(self, X: pd.DataFrame | np.ndarray) -> dict[str, np.ndarray]:
        if not self.thresholds_:
            raise RuntimeError("NoveltyDetector.fit must be called before score")
        frame = self._frame(X)
        return self._raw_group_scores(frame)

    def score(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        scores = self.group_scores(X)
        margins = [scores[name] - self.thresholds_[name] for name in scores]
        return np.max(np.column_stack(margins), axis=1)

    def predict_novel(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        scores = self.group_scores(X)
        flags = [
            values >= self.thresholds_[name]
            if self.inclusive_thresholds_[name]
            else values > self.thresholds_[name]
            for name, values in scores.items()
        ]
        return np.any(np.column_stack(flags), axis=1)
