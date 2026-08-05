from __future__ import annotations

"""Open-set novelty detection for S-plane telemetry windows."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from telemetry.features import FEATURE_COLUMNS


class NoveltyDetector:
    """Flag windows outside a calibrated known-family feature distribution.

    The detector is intentionally label-agnostic: known benign faults and known
    attacks may both be supplied to ``fit``. Callers are responsible for family
    isolation, especially during leave-one-attack-out evaluation.
    """

    def __init__(self, target_known_flag_rate: float = 0.02, random_state: int = 1588) -> None:
        if not 0.0 < target_known_flag_rate < 0.5:
            raise ValueError("target_known_flag_rate must be between 0 and 0.5")
        self.target_known_flag_rate = float(target_known_flag_rate)
        self.random_state = int(random_state)
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=self.random_state,
            n_jobs=1,
        )
        self.threshold_: float | None = None

    @staticmethod
    def _values(X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            return X[FEATURE_COLUMNS].to_numpy(dtype=float)
        values = np.asarray(X, dtype=float)
        if values.ndim != 2 or values.shape[1] != len(FEATURE_COLUMNS):
            raise ValueError(f"expected a 2D array with {len(FEATURE_COLUMNS)} features")
        return values

    def fit(self, X_train: pd.DataFrame | np.ndarray) -> "NoveltyDetector":
        values = self._values(X_train)
        if len(values) < 20:
            raise ValueError("at least 20 known windows are required to calibrate novelty")
        scaled = self.scaler.fit_transform(values)
        self.model.fit(scaled)
        training_scores = -self.model.score_samples(scaled)
        self.threshold_ = float(
            np.quantile(training_scores, 1.0 - self.target_known_flag_rate, method="higher")
        )
        return self

    def score(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("NoveltyDetector.fit must be called before score")
        scaled = self.scaler.transform(self._values(X))
        return -self.model.score_samples(scaled)

    def predict_novel(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("NoveltyDetector.fit must be called before predict_novel")
        return self.score(X) > self.threshold_
