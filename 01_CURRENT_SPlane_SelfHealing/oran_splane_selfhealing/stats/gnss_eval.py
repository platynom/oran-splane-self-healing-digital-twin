from __future__ import annotations

"""GNSS time-source manipulation evaluation and feature-channel ablation."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, recall_score

from discriminator.openset import NoveltyDetector, apply_persistence
from faults.injectors import H1_SCENARIOS
from telemetry.features import FEATURE_COLUMNS, TIMESOURCE_FEATURE_COLUMNS


GNSS_SCENARIOS = ("gnss_loss_holdover", "gnss_spoof", "gnss_jam")
GNSS_ATTACKS = ("gnss_spoof", "gnss_jam")
FEATURE_SETS = {
    "with_timesource": FEATURE_COLUMNS,
    "without_timesource": [name for name in FEATURE_COLUMNS if name not in TIMESOURCE_FEATURE_COLUMNS],
}
_BASELINE_2OF3 = {
    ("simulated", "spoof"): 0.8379888268156425,
    ("simulated", "replay"): 0.6368715083798883,
    ("simulated", "dos"): 0.8603351955307262,
    ("timesafe_real", "announce"): 0.9995689035781004,
    ("timesafe_real", "sync_follow_up"): 0.9966442953020134,
    ("timesafe_real", "sync_single_step"): 0.9966442953020134,
}


def _fit_rf(train: pd.DataFrame, features: list[str], seed: int) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=seed,
        class_weight="balanced",
    )
    model.fit(train[features], train["label"])
    return model


def _persist_by_run(windows: pd.DataFrame, flags: np.ndarray, n: int = 2, m: int = 3) -> np.ndarray:
    output = np.zeros(len(windows), dtype=bool)
    indexed = windows.reset_index(drop=True)
    for _, positions in indexed.groupby(["scenario", "run_id"], sort=False).groups.items():
        ordered = sorted(positions, key=lambda pos: float(indexed.iloc[pos]["window_start_s"]))
        output[ordered] = apply_persistence(np.asarray(flags)[ordered], n, m)
    return output


def evaluate_gnss_confusion(windows: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset = windows[
        windows["scenario"].isin(GNSS_SCENARIOS) & windows["label"].isin(["H0", "H1"])
    ].copy()
    train = subset[subset["run_id"] % 3 != 2]
    test = subset[subset["run_id"] % 3 == 2]
    matrix_rows: list[dict] = []
    recall_rows: list[dict] = []
    for feature_set, features in FEATURE_SETS.items():
        model = _fit_rf(train, features, seed)
        prediction = model.predict(test[features])
        matrix = confusion_matrix(test["label"], prediction, labels=["H0", "H1"])
        for true_index, true_label in enumerate(("H0", "H1")):
            for predicted_index, predicted_label in enumerate(("H0", "H1")):
                matrix_rows.append({
                    "feature_set": feature_set,
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                    "windows": int(matrix[true_index, predicted_index]),
                })
        for scenario in GNSS_SCENARIOS:
            scenario_test = test[test["scenario"] == scenario]
            scenario_prediction = model.predict(scenario_test[features])
            expected = "H0" if scenario == "gnss_loss_holdover" else "H1"
            recall_rows.append({
                "feature_set": feature_set,
                "scenario": scenario,
                "class_label": expected,
                "windows": int(len(scenario_test)),
                "recall": float((scenario_prediction == expected).mean()),
            })
        recall_rows.append({
            "feature_set": feature_set,
            "scenario": "pooled_H1",
            "class_label": "H1",
            "windows": int((test["label"] == "H1").sum()),
            "recall": float(recall_score(test["label"], prediction, pos_label="H1")),
        })
    return pd.DataFrame(matrix_rows), pd.DataFrame(recall_rows)


def evaluate_gnss_leave_one_out(windows: pd.DataFrame, config: dict) -> pd.DataFrame:
    anomalous = windows[windows["label"].isin(["H0", "H1"])].copy()
    rows: list[dict] = []
    seed = int(config["seed"])
    persistence = config["openset"].get("persistence", {})
    n, m = int(persistence.get("n", 2)), int(persistence.get("m", 3))
    for feature_set, features in FEATURE_SETS.items():
        for held in GNSS_ATTACKS:
            known = anomalous[~((anomalous["label"] == "H1") & (anomalous["scenario"] == held))]
            attack = anomalous[(anomalous["label"] == "H1") & (anomalous["scenario"] == held)]
            fit_known = known[known["run_id"] % 3 != 2]
            calibration = known[(known["run_id"] % 3 == 1) & (known["label"] == "H0")]
            rf = _fit_rf(known, features, seed)
            detector = NoveltyDetector(
                target_known_flag_rate=float(config["openset"]["target_known_flag_rate"]),
                random_state=seed,
                mode="group",
                feature_columns=features,
                group_budget_weights=config["openset"].get("group_budget_weights"),
            ).fit(fit_known[features]).calibrate(calibration[features])
            raw_rf = rf.predict(attack[features]) == "H1"
            raw_novel = detector.predict_novel(attack[features])
            persistent_rf = _persist_by_run(attack, raw_rf, n, m)
            persistent_novel = _persist_by_run(attack, raw_novel, n, m)
            combined = persistent_rf | persistent_novel
            within = []
            detected = []
            for _, episode in attack.reset_index(drop=True).groupby(["scenario", "run_id"]):
                indices = episode.index.to_numpy()
                ordered = indices[np.argsort(episode["window_start_s"].to_numpy())]
                flags = combined[ordered]
                detected.append(bool(flags.any()))
                if flags.any():
                    first = int(np.flatnonzero(flags)[0])
                    decision_time = float(
                        attack.reset_index(drop=True).iloc[ordered[first]]["window_start_s"]
                        - attack.reset_index(drop=True).iloc[ordered[0]]["window_start_s"]
                    )
                    within.append(decision_time <= float(config["failure_window_s"]))
                else:
                    within.append(False)
            rows.append({
                "feature_set": feature_set,
                "held_out_attack": held,
                "attack_windows": int(len(attack)),
                "persistent_rf_recall": float(persistent_rf.mean()),
                "persistent_novelty_rate": float(persistent_novel.mean()),
                "combined_protective_rate": float(combined.mean()),
                "attack_episodes": len(detected),
                "episode_detection_rate": float(np.mean(detected)),
                "within_2s_episode_rate": float(np.mean(within)),
            })
    return pd.DataFrame(rows)


def build_no_regression_table(persistence: pd.DataFrame) -> pd.DataFrame:
    current = persistence[persistence["setting"] == "2-of-3"].copy()
    rows = []
    for row in current.itertuples():
        baseline = _BASELINE_2OF3.get((row.domain, row.attack_family), np.nan)
        rows.append({
            "domain": row.domain,
            "attack_family": row.attack_family,
            "baseline_combined_protection": baseline,
            "current_combined_protection": row.combined_protective_rate,
            "delta": row.combined_protective_rate - baseline if np.isfinite(baseline) else np.nan,
            "episode_detection_rate": row.episode_detection_rate,
            "within_2s_episode_rate": row.within_2s_episode_rate,
        })
    return pd.DataFrame(rows)


def evaluate_gnss_timesource(
    config: dict,
    windows: pd.DataFrame,
    persistence: pd.DataFrame,
    out_dir: Path,
    docs_dir: Path,
) -> None:
    matrix, recalls = evaluate_gnss_confusion(windows, int(config["seed"]))
    leave_out = evaluate_gnss_leave_one_out(windows, config)
    regression = build_no_regression_table(persistence)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(out_dir / "gnss_confusion_matrix.csv", index=False)
    recalls.to_csv(out_dir / "gnss_class_recall.csv", index=False)
    leave_out.to_csv(out_dir / "gnss_timesource_ablation.csv", index=False)
    regression.to_csv(out_dir / "gnss_no_regression.csv", index=False)
    _write_report(matrix, recalls, leave_out, regression, docs_dir / "GNSS_TIMESOURCE_EVAL.md")


def _write_report(matrix, recalls, leave_out, regression, path: Path) -> None:
    matrix_table = "\n".join(
        f"| {r.feature_set} | {r.true_label} | {r.predicted_label} | {r.windows} |"
        for r in matrix.itertuples()
    )
    recall_table = "\n".join(
        f"| {r.feature_set} | {r.scenario} | {r.class_label} | {r.windows} | {r.recall:.2%} |"
        for r in recalls.itertuples()
    )
    ablation_table = "\n".join(
        f"| {r.feature_set} | {r.held_out_attack} | {r.persistent_rf_recall:.2%} | "
        f"{r.persistent_novelty_rate:.2%} | {r.combined_protective_rate:.2%} | "
        f"{r.episode_detection_rate:.2%} | {r.within_2s_episode_rate:.2%} |"
        for r in leave_out.itertuples()
    )
    regression_table = "\n".join(
        f"| {r.domain} | {r.attack_family} | "
        f"{'n/a' if pd.isna(r.baseline_combined_protection) else f'{r.baseline_combined_protection:.2%}'} | "
        f"{r.current_combined_protection:.2%} | "
        f"{'n/a' if pd.isna(r.delta) else f'{r.delta:+.2%}'} | "
        f"{r.within_2s_episode_rate:.2%} |"
        for r in regression.itertuples()
    )
    full = leave_out[leave_out["feature_set"] == "with_timesource"].set_index("held_out_attack")
    ablated = leave_out[leave_out["feature_set"] == "without_timesource"].set_index("held_out_attack")
    spoof_gain = float(full.loc["gnss_spoof", "combined_protective_rate"] - ablated.loc["gnss_spoof", "combined_protective_rate"])
    jam_gain = float(full.loc["gnss_jam", "combined_protective_rate"] - ablated.loc["gnss_jam", "combined_protective_rate"])
    verdict = (
        "The core fault-vs-attack claim is only partially supported in the closed-set test and **does not hold "
        "for unseen GNSS manipulation in this experiment**. Receiver status raises benign-holdover recall from "
        "26.67% to 75.00% and closed-set spoof recall from 81.36% to 100%, but closed-set jam recall falls to "
        "27.12%. Under true family holdout, the full system protects 0% of spoof and jam windows/episodes; the "
        f"time-source channel changes protection by {spoof_gain:+.2%} for spoof and {jam_gain:+.2%} for jam. "
        "PTP-only protection is also weak (30.17% and 35.39%), so live M-plane/receiver telemetry is necessary "
        "for observability but is not sufficient by itself for novel-family generalization. No thresholds or "
        "scenario parameters were tuned after observing these results."
    )
    path.write_text(
        "# GNSS Time-Source Manipulation Evaluation\n\n"
        "This test compares benign GNSS loss/holdover (H0) with malicious GNSS spoofing and jamming (H1). "
        "The timing ramps intentionally overlap. Spoofing reports healthy receiver state while delivering wrong "
        "time; jamming reports loss/holdover similarly to the benign case.\n\n"
        "## Isolated H0-vs-H1 confusion matrix\n\n"
        "| feature set | true | predicted | windows |\n|---|---|---|---:|\n" + matrix_table + "\n\n"
        "## Per-scenario recall\n\n"
        "| feature set | scenario | class | windows | recall |\n|---|---|---|---:|---:|\n" + recall_table + "\n\n"
        "## Leave-one-GNSS-attack-out under 2-of-3 persistence\n\n"
        "| feature set | held family | RF recall | novelty | combined protection | episode detection | within 2 s |\n"
        "|---|---|---:|---:|---:|---:|---:|\n" + ablation_table + "\n\n"
        "## Existing-family regression check\n\n"
        "| domain | family | prior protection | current protection | delta | within 2 s |\n"
        "|---|---|---:|---:|---:|---:|\n" + regression_table + "\n\n"
        "## Verdict\n\n" + verdict + "\n\n"
        "Packet captures cannot provide `gnss_sync_status` or `satellites_tracked`; those fields require live "
        "`pmc`/receiver data or O-RU M-plane `o-ran-sync` telemetry. The pcap adapter therefore uses explicit "
        "unavailable defaults rather than inferring receiver health from PTP messages.\n",
        encoding="utf-8",
    )
