from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split

from telemetry.features import FEATURE_COLUMNS
from discriminator.openset import NoveltyDetector


def train_and_evaluate(windows: pd.DataFrame, config: dict, out_dir: Path) -> tuple[RandomForestClassifier, pd.DataFrame]:
    anomalous = windows[windows["label"].isin(["H0", "H1"])].copy()
    X = anomalous[FEATURE_COLUMNS]
    y = anomalous["label"]
    strat = anomalous["label"] + "_" + anomalous["scenario"].astype(str)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=float(config["discriminator"]["test_size"]),
        random_state=int(config["discriminator"]["random_state"]),
        stratify=strat,
    )
    clf = RandomForestClassifier(n_estimators=90, max_depth=6, random_state=int(config["seed"]), class_weight="balanced")
    clf.fit(X_train, y_train)
    openset = config.get("openset", {})
    if bool(openset.get("enabled", False)):
        clf.novelty_detector_ = NoveltyDetector(
            target_known_flag_rate=float(openset.get("target_known_flag_rate", 0.02)),
            random_state=int(config["seed"]),
            mode=str(openset.get("mode", "group")),
            group_budget_weights=openset.get("group_budget_weights"),
        ).fit(X_train)
    pred = clf.predict(X_test)
    proba = clf.predict_proba(X_test)[:, list(clf.classes_).index("H1")]
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, pred, labels=["H0", "H1"], average="macro", zero_division=0)
    auc = roc_auc_score((y_test == "H1").astype(int), proba)

    # Detection-only baseline has no H0/H1 separation; it labels all anomalies as attack, a common unsafe response.
    baseline_pred = pd.Series(["H1"] * len(y_test), index=y_test.index)
    b_precision, b_recall, b_f1, _ = precision_recall_fscore_support(
        y_test, baseline_pred, labels=["H0", "H1"], average="macro", zero_division=0
    )
    rows = [
        {
            "model": "random_forest_h0_h1",
            "accuracy": accuracy_score(y_test, pred),
            "precision_macro": precision,
            "recall_macro": recall,
            "f1_macro": f1,
            "roc_auc_h1": auc,
            "confusion_matrix": confusion_matrix(y_test, pred, labels=["H0", "H1"]).tolist(),
        },
        {
            "model": "detection_only_all_anomalies_attack",
            "accuracy": accuracy_score(y_test, baseline_pred),
            "precision_macro": b_precision,
            "recall_macro": b_recall,
            "f1_macro": b_f1,
            "roc_auc_h1": 0.5,
            "confusion_matrix": confusion_matrix(y_test, baseline_pred, labels=["H0", "H1"]).tolist(),
        },
    ]
    metrics = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out_dir / "discriminator_metrics.csv", index=False)
    return clf, metrics
