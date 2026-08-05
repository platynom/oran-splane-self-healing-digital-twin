from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from discriminator.openset import NoveltyDetector
from healing.loop import choose_action
from stats.openset_eval import evaluate_simulated
from telemetry.features import FEATURE_COLUMNS

ROOT = Path(__file__).resolve().parents[1]


def test_novelty_detector_calibrates_known_budget_and_flags_clear_ood():
    rng = np.random.default_rng(1588)
    known = pd.DataFrame(rng.normal(0, 1, (1000, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
    out_of_distribution = pd.DataFrame(
        rng.normal(8, 0.5, (100, len(FEATURE_COLUMNS))),
        columns=FEATURE_COLUMNS,
    )
    detector = NoveltyDetector(target_known_flag_rate=0.02).fit(known)

    assert detector.predict_novel(known).mean() <= 0.02
    assert detector.predict_novel(out_of_distribution).mean() >= 0.95
    assert detector.score(out_of_distribution).mean() > detector.score(known).mean()


def test_unknown_healing_decision_uses_safe_default():
    class AlwaysNovel:
        def predict_novel(self, _X):
            return np.array([True])

    class MustNotRunClassifier:
        novelty_detector_ = AlwaysNovel()

        def predict(self, _X):
            raise AssertionError("known-family classifier must not run for UNKNOWN")

    window = pd.Series({column: 0.0 for column in FEATURE_COLUMNS})
    window["offset_abs_max"] = 180.0
    window["pdv_std"] = 10.0
    config = {
        "openset": {"enabled": True},
        "healing": {"anomaly_threshold_ns": 100.0, "decision_budget_s": 1.0},
    }
    decision = choose_action(window, MustNotRunClassifier(), config)
    assert decision.label_estimate == "UNKNOWN"
    assert decision.action == "safe_default"
    assert decision.reason == "out-of-distribution / novel; conservative safe response"


def test_combined_protection_converts_unseen_dos_misses():
    with (ROOT / "config" / "default.yaml").open("r", encoding="utf-8") as handle:
        config = copy.deepcopy(yaml.safe_load(handle))
    config["dataset"]["scenarios_per_type"] = 6
    result = evaluate_simulated(config)
    dos = result[result["attack_family"] == "dos"].iloc[0]

    assert dos["rf_only_attack_recall"] <= 0.10
    assert dos["combined_protective_rate"] >= 0.75
    assert dos["combined_protective_rate"] > dos["rf_only_attack_recall"] + 0.60
    assert dos["benign_novelty_false_alarm_rate"] <= 0.04
