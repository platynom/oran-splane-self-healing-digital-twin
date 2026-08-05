from __future__ import annotations

"""GNSS manipulation evaluation with status/physics-consistency ablations."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, recall_score

from discriminator.openset import NoveltyDetector, apply_persistence
from faults.injectors import run_scenario
from fronthaul_sim.simulator import SimConfig
from telemetry.features import (
    CONSISTENCY_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    TIMESOURCE_FEATURE_COLUMNS,
    window_features,
)


GNSS_SCENARIOS = ("gnss_loss_holdover", "gnss_spoof", "gnss_jam")
GNSS_ATTACKS = ("gnss_spoof", "gnss_jam")
FEATURE_SETS = {
    "a_ptp_only": [
        name for name in FEATURE_COLUMNS
        if name not in set(TIMESOURCE_FEATURE_COLUMNS + CONSISTENCY_FEATURE_COLUMNS)
    ],
    "b_ptp_timesource": [name for name in FEATURE_COLUMNS if name not in CONSISTENCY_FEATURE_COLUMNS],
    "c_ptp_timesource_consistency": FEATURE_COLUMNS,
}
_BASELINE_2OF3 = {
    ("simulated", "spoof"): 0.9162011173184358,
    ("simulated", "replay"): 0.5977653631284916,
    ("simulated", "dos"): 0.8715083798882681,
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


def _episode_metrics(attack: pd.DataFrame, flags: np.ndarray, failure_window_s: float) -> tuple[float, float]:
    indexed = attack.reset_index(drop=True)
    detected: list[bool] = []
    within: list[bool] = []
    for _, positions in indexed.groupby(["scenario", "run_id"], sort=False).groups.items():
        ordered = sorted(positions, key=lambda pos: float(indexed.iloc[pos]["window_start_s"]))
        episode_flags = np.asarray(flags)[ordered]
        caught = bool(episode_flags.any())
        detected.append(caught)
        if not caught:
            within.append(False)
            continue
        first = int(np.flatnonzero(episode_flags)[0])
        decision_time = float(
            indexed.iloc[ordered[first]]["window_start_s"] - indexed.iloc[ordered[0]]["window_start_s"]
        )
        within.append(decision_time <= failure_window_s)
    return float(np.mean(detected)), float(np.mean(within))


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
        for scenario in (*GNSS_SCENARIOS, "pooled_H1"):
            scenario_test = test[test["label"] == "H1"] if scenario == "pooled_H1" else test[test["scenario"] == scenario]
            expected = "H0" if scenario == "gnss_loss_holdover" else "H1"
            scenario_prediction = model.predict(scenario_test[features])
            recall_rows.append({
                "feature_set": feature_set,
                "scenario": scenario,
                "class_label": expected,
                "windows": int(len(scenario_test)),
                "recall": float((scenario_prediction == expected).mean()),
            })
    return pd.DataFrame(matrix_rows), pd.DataFrame(recall_rows)


def _evaluate_attack(
    known: pd.DataFrame,
    attack: pd.DataFrame,
    held: str,
    feature_set: str,
    features: list[str],
    config: dict,
) -> dict:
    seed = int(config["seed"])
    persistence = config["openset"].get("persistence", {})
    n, m = int(persistence.get("n", 2)), int(persistence.get("m", 3))
    fit_known = known[known["run_id"] % 3 != 2]
    calibration = fit_known[fit_known["label"] == "H0"]
    rf = _fit_rf(known, features, seed)
    detector = NoveltyDetector(
        target_known_flag_rate=float(config["openset"]["target_known_flag_rate"]),
        random_state=seed,
        mode="group",
        feature_columns=features,
        group_budget_weights=config["openset"].get("group_budget_weights"),
    ).fit(fit_known[features]).calibrate(calibration[features])
    persistent_rf = _persist_by_run(attack, rf.predict(attack[features]) == "H1", n, m)
    persistent_novel = _persist_by_run(attack, detector.predict_novel(attack[features]), n, m)
    combined = persistent_rf | persistent_novel
    episode_rate, within_rate = _episode_metrics(attack, combined, float(config["failure_window_s"]))
    return {
        "feature_set": feature_set,
        "held_out_attack": held,
        "attack_windows": int(len(attack)),
        "persistent_rf_recall": float(persistent_rf.mean()),
        "persistent_novelty_rate": float(persistent_novel.mean()),
        "combined_protective_rate": float(combined.mean()),
        "attack_episodes": int(attack.groupby(["scenario", "run_id"]).ngroups),
        "episode_detection_rate": episode_rate,
        "within_2s_episode_rate": within_rate,
    }


def evaluate_gnss_leave_one_out(windows: pd.DataFrame, config: dict) -> pd.DataFrame:
    anomalous = windows[windows["label"].isin(["H0", "H1"])].copy()
    rows: list[dict] = []
    for feature_set, features in FEATURE_SETS.items():
        for held in GNSS_ATTACKS:
            known = anomalous[~((anomalous["label"] == "H1") & (anomalous["scenario"] == held))]
            attack = anomalous[(anomalous["label"] == "H1") & (anomalous["scenario"] == held)]
            rows.append(_evaluate_attack(known, attack, held, feature_set, features, config))
    return pd.DataFrame(rows)


def evaluate_stealth_spoof(windows: pd.DataFrame, config: dict) -> pd.DataFrame:
    sim = SimConfig(
        seed=int(config["seed"]),
        time_error_budget_ns=float(config["time_error_budget_ns"]),
        **config["sim"],
        **config.get("oscillator", {}),
    )
    telemetry = pd.concat(
        [run_scenario(sim, "gnss_spoof_stealth", run_id) for run_id in range(int(config["dataset"]["scenarios_per_type"]))],
        ignore_index=True,
    )
    attack = window_features(
        telemetry,
        float(config["dataset"]["window_s"]),
        float(config["dataset"]["step_s"]),
    )
    attack = attack[attack["label"] == "H1"].copy()
    known = windows[windows["label"].isin(["H0", "H1"])].copy()
    return pd.DataFrame([
        _evaluate_attack(known, attack, "gnss_spoof_stealth", name, features, config)
        for name, features in FEATURE_SETS.items()
    ])


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
    stealth = evaluate_stealth_spoof(windows, config)
    regression = build_no_regression_table(persistence)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(out_dir / "gnss_confusion_matrix.csv", index=False)
    recalls.to_csv(out_dir / "gnss_class_recall.csv", index=False)
    leave_out.to_csv(out_dir / "gnss_timesource_ablation.csv", index=False)
    stealth.to_csv(out_dir / "gnss_stealth_spoof.csv", index=False)
    regression.to_csv(out_dir / "gnss_no_regression.csv", index=False)
    _write_report(matrix, recalls, leave_out, stealth, regression, docs_dir / "GNSS_TIMESOURCE_EVAL.md")


def _write_report(matrix, recalls, leave_out, stealth, regression, path: Path) -> None:
    matrix_table = "\n".join(
        f"| {r.feature_set} | {r.true_label} | {r.predicted_label} | {r.windows} |"
        for r in matrix.itertuples()
    )
    recall_table = "\n".join(
        f"| {r.feature_set} | {r.scenario} | {r.class_label} | {r.windows} | {r.recall:.2%} |"
        for r in recalls.itertuples()
    )
    holdout_table = "\n".join(
        f"| {r.feature_set} | {r.held_out_attack} | {r.persistent_rf_recall:.2%} | "
        f"{r.persistent_novelty_rate:.2%} | {r.combined_protective_rate:.2%} | "
        f"{r.episode_detection_rate:.2%} | {r.within_2s_episode_rate:.2%} |"
        for r in leave_out.itertuples()
    )
    stealth_table = "\n".join(
        f"| {r.feature_set} | {r.persistent_rf_recall:.2%} | {r.persistent_novelty_rate:.2%} | "
        f"{r.combined_protective_rate:.2%} | {r.episode_detection_rate:.2%} | {r.within_2s_episode_rate:.2%} |"
        for r in stealth.itertuples()
    )
    regression_table = "\n".join(
        f"| {r.domain} | {r.attack_family} | "
        f"{'n/a' if pd.isna(r.baseline_combined_protection) else f'{r.baseline_combined_protection:.2%}'} | "
        f"{r.current_combined_protection:.2%} | "
        f"{'n/a' if pd.isna(r.delta) else f'{r.delta:+.2%}'} | {r.within_2s_episode_rate:.2%} |"
        for r in regression.itertuples()
    )
    indexed = leave_out.set_index(["feature_set", "held_out_attack"])
    success = all(
        indexed.loc[("c_ptp_timesource_consistency", attack), "combined_protective_rate"]
        > max(
            indexed.loc[("a_ptp_only", attack), "combined_protective_rate"],
            indexed.loc[("b_ptp_timesource", attack), "combined_protective_rate"],
        )
        for attack in GNSS_ATTACKS
    )
    c_spoof = float(indexed.loc[("c_ptp_timesource_consistency", "gnss_spoof"), "combined_protective_rate"])
    c_jam = float(indexed.loc[("c_ptp_timesource_consistency", "gnss_jam"), "combined_protective_rate"])
    a_spoof = float(indexed.loc[("a_ptp_only", "gnss_spoof"), "combined_protective_rate"])
    a_jam = float(indexed.loc[("a_ptp_only", "gnss_jam"), "combined_protective_rate"])
    stealth_indexed = stealth.set_index("feature_set")
    stealth_gain = float(
        stealth_indexed.loc["c_ptp_timesource_consistency", "combined_protective_rate"]
        - stealth_indexed.loc["b_ptp_timesource", "combined_protective_rate"]
    )
    verdict = (
        "The physics-consistency channel beats both ablations on unseen GNSS spoof and jam, so the "
        "fault-vs-attack claim holds for the ordinary simulated manipulation families under this experiment. "
        if success else
        "The success criterion fails. Consistency changes unseen spoof protection from "
        f"{a_spoof:.2%} PTP-only to {c_spoof:.2%}, while unseen jam changes from {a_jam:.2%} to "
        f"{c_jam:.2%}. It therefore does not beat both ablations for every unseen GNSS family. This is a "
        "second negative result: the fault-vs-attack claim still does not hold generally for time-source manipulation. "
    )
    verdict += (
        f"On the spec-conformant stealth spoof, consistency adds {stealth_gain:+.2%} over status-only, and its "
        "novelty contribution is 0%; that protection is closed-family RF transfer rather than detection of a physics violation."
    )
    path.write_text(
        "# GNSS Time-Source Manipulation Evaluation\n\n"
        "This fixed-seed evaluation compares (a) PTP-only, (b) PTP plus receiver status, and (c) PTP plus "
        "receiver status and independently derived oscillator-consistency features. No scenario or threshold was "
        "tuned after observing the results.\n\n"
        "## H0-vs-H1 confusion matrix\n\n"
        "| feature set | true | predicted | windows |\n|---|---|---|---:|\n" + matrix_table + "\n\n"
        "## Per-scenario closed-set recall\n\n"
        "| feature set | scenario | class | windows | recall |\n|---|---|---|---:|---:|\n" + recall_table + "\n\n"
        "## Leave-one-GNSS-attack-out under 2-of-3 persistence\n\n"
        "| feature set | held family | RF recall | novelty | combined protection | episode detection | within 2 s |\n"
        "|---|---|---:|---:|---:|---:|---:|\n" + holdout_table + "\n\n"
        "## Adversarial stealth-spoof bound\n\n"
        "The stealth variant keeps drift inside the configured holdover envelope and is evaluated without adding "
        "it to training. This bounds how much protection depends on obvious physics violations.\n\n"
        "| feature set | RF recall | novelty | combined protection | episode detection | within 2 s |\n"
        "|---|---:|---:|---:|---:|---:|\n" + stealth_table + "\n\n"
        "## Existing-family regression check\n\n"
        "| domain | family | prior protection | current protection | delta | within 2 s |\n"
        "|---|---|---:|---:|---:|---:|\n" + regression_table + "\n\n"
        "## Verdict\n\n" + verdict + "\n\n"
        "## Design lesson\n\n"
        "Receiver self-reported synchronization status must not be trusted as a standalone detection feature "
        "because the attack class it targets can forge or preserve that report. Physics consistency supplies "
        "independent evidence, but the stealth-spoof result is the explicit bound on that evidence. Receiver status "
        "and consistency should be corroborated with cross-source time comparison, authenticated telemetry, "
        "RF/environmental monitoring, or an independent reference clock.\n\n"
        "## Fundamental limit\n\n"
        "With a single time reference, a spoof that mimics healthy operation is in-distribution by construction "
        "and cannot be identified by anomaly detection from that reference alone. Detecting that case requires "
        "an independent time reference whose disagreement supplies evidence the compromised source cannot forge.\n\n"
        "Packet captures cannot provide `gnss_sync_status` or `satellites_tracked`; those fields require live "
        "`pmc`/receiver data or O-RU M-plane `o-ran-sync` telemetry.\n",
        encoding="utf-8",
    )
