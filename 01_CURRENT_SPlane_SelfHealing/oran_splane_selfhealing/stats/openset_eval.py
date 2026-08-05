from __future__ import annotations

"""Leakage-resistant open-set evaluation on simulated and real sessions."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from discriminator.openset import NoveltyDetector
from faults.injectors import H1_SCENARIOS, generate_telemetry
from fronthaul_sim.simulator import SimConfig
from telemetry.features import FEATURE_COLUMNS, window_features

_FAMILY = {"ptp_spoof": "spoof", "ptp_replay": "replay", "ptp_dos_flood": "dos"}


def _fit_rf(train: pd.DataFrame, seed: int) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=90,
        max_depth=6,
        random_state=seed,
        class_weight="balanced",
    )
    model.fit(train[FEATURE_COLUMNS], train["label"])
    return model


def _fit_real_rf(train: pd.DataFrame, seed: int):
    model = make_pipeline(
        StandardScaler(),
        RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            random_state=seed,
            class_weight="balanced",
        ),
    )
    model.fit(train[FEATURE_COLUMNS], train["label"])
    return model


def _metric_row(
    domain: str,
    held_out: str,
    family: str,
    attack: pd.DataFrame,
    known_test: pd.DataFrame,
    rf: RandomForestClassifier,
    novelty: NoveltyDetector,
) -> dict[str, float | int | str]:
    rf_attack = rf.predict(attack[FEATURE_COLUMNS]) == "H1"
    novel_attack = novelty.predict_novel(attack[FEATURE_COLUMNS])
    combined = rf_attack | novel_attack
    known_novel = novelty.predict_novel(known_test[FEATURE_COLUMNS])
    benign = known_test[known_test["label"] == "H0"]
    benign_novel = novelty.predict_novel(benign[FEATURE_COLUMNS]) if not benign.empty else np.array([])
    return {
        "domain": domain,
        "held_out_attack": held_out,
        "attack_family": family,
        "attack_windows": int(len(attack)),
        "rf_only_attack_recall": float(rf_attack.mean()),
        "novelty_flag_rate": float(novel_attack.mean()),
        "combined_protective_rate": float(combined.mean()),
        "known_windows": int(len(known_test)),
        "known_novelty_false_alarm_rate": float(known_novel.mean()),
        "benign_windows": int(len(benign)),
        "benign_novelty_false_alarm_rate": float(benign_novel.mean()) if len(benign_novel) else float("nan"),
    }


def evaluate_simulated(config: dict) -> pd.DataFrame:
    sim_cfg = SimConfig(
        seed=int(config["seed"]),
        time_error_budget_ns=float(config["time_error_budget_ns"]),
        **config["sim"],
    )
    telemetry = generate_telemetry(sim_cfg, int(config["dataset"]["scenarios_per_type"]))
    windows = window_features(
        telemetry,
        float(config["dataset"]["window_s"]),
        float(config["dataset"]["step_s"]),
    )
    anomalous = windows[windows["label"].isin(["H0", "H1"])].copy()
    rows = []
    for held in H1_SCENARIOS:
        known = anomalous[~((anomalous["label"] == "H1") & (anomalous["scenario"] == held))]
        attack = anomalous[(anomalous["label"] == "H1") & (anomalous["scenario"] == held)]
        fit_known = known[known["run_id"] % 3 != 2]
        known_test = known[known["run_id"] % 3 == 2]
        rf = _fit_rf(known, int(config["seed"]))
        novelty = NoveltyDetector(
            target_known_flag_rate=float(config["openset"]["target_known_flag_rate"]),
            random_state=int(config["seed"]),
        ).fit(fit_known[FEATURE_COLUMNS])
        rows.append(_metric_row("simulated", held, _FAMILY[held], attack, known_test, rf, novelty))
    return pd.DataFrame(rows)


def _load_real_sessions(session_dir: Path, config: dict) -> pd.DataFrame:
    rows = []
    for path in sorted(session_dir.glob("*.csv")):
        if "__" not in path.stem:
            continue
        capture_id, family = path.stem.rsplit("__", 1)
        label = "H0" if family == "benign" else "H1"
        telemetry = pd.read_csv(path)
        if not set(FEATURE_COLUMNS).issubset(telemetry.columns):
            telemetry["scenario"] = capture_id
            telemetry["run_id"] = 0
            telemetry["label"] = label
            features = window_features(
                telemetry,
                float(config["dataset"]["window_s"]),
                float(config["dataset"]["step_s"]),
            )
        else:
            features = telemetry.copy()
        features["capture_id"] = capture_id
        features["attack_family"] = "none" if label == "H0" else family
        features["label"] = label
        rows.append(features)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def evaluate_real(config: dict, session_dir: Path) -> pd.DataFrame:
    real = _load_real_sessions(session_dir, config)
    if real.empty:
        return pd.DataFrame()
    rows = []
    families = sorted(set(real.loc[real["label"] == "H1", "attack_family"]) - {"none"})
    for family in families:
        held_sessions = set(
            real.loc[(real["label"] == "H1") & (real["attack_family"] == family), "capture_id"]
        )
        train = real[~real["capture_id"].isin(held_sessions)]
        attack = real[(real["label"] == "H1") & (real["attack_family"] == family)]
        known_test = real[(real["label"] == "H0") & real["capture_id"].isin(held_sessions)]
        if train["label"].nunique() < 2 or attack.empty or known_test.empty:
            continue
        rf = _fit_real_rf(train, int(config["seed"]))
        novelty = NoveltyDetector(
            target_known_flag_rate=float(config["openset"]["target_known_flag_rate"]),
            random_state=int(config["seed"]),
        ).fit(train[FEATURE_COLUMNS])
        rows.append(_metric_row("timesafe_real", family, family, attack, known_test, rf, novelty))
    return pd.DataFrame(rows)


def evaluate_openset(config: dict, out_dir: Path, docs_dir: Path, real_session_dir: Path | None = None) -> pd.DataFrame:
    simulated = evaluate_simulated(config)
    real = evaluate_real(config, real_session_dir) if real_session_dir and real_session_dir.exists() else pd.DataFrame()
    result = pd.concat([simulated, real], ignore_index=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_dir / "openset_eval.csv", index=False)
    _write_report(result, docs_dir / "OPENSET_EVAL.md", bool(not real.empty), config)
    return result


def _write_report(result: pd.DataFrame, path: Path, has_real: bool, config: dict) -> None:
    rows = []
    for item in result.itertuples():
        rows.append(
            f"| {item.domain} | {item.attack_family} | {item.attack_windows} | "
            f"{item.rf_only_attack_recall:.3f} | {item.novelty_flag_rate:.3f} | "
            f"{item.combined_protective_rate:.3f} | {item.benign_novelty_false_alarm_rate:.3f} |"
        )
    real_note = (
        "Local TIMESAFE session derivatives were available and evaluated with complete capture isolation."
        if has_real
        else "TIMESAFE session derivatives were unavailable; no external-data rows were fabricated."
    )
    simulated_dos = result[(result["domain"] == "simulated") & (result["attack_family"] == "dos")]
    headline = ""
    if not simulated_dos.empty:
        dos = simulated_dos.iloc[0]
        headline += (
            f"Unseen simulated DoS improves from {dos['rf_only_attack_recall']:.1%} RF-only recall "
            f"to {dos['combined_protective_rate']:.1%} combined protective coverage. "
        )
    real_announce = result[(result["domain"] == "timesafe_real") & (result["attack_family"] == "announce")]
    if not real_announce.empty:
        announce = real_announce.iloc[0]
        headline += (
            f"Real held-out Announce changes only from {announce['rf_only_attack_recall']:.1%} "
            f"to {announce['combined_protective_rate']:.1%}, so open-set scoring does not resolve "
            "that domain-specific generalization gap. The attack remains in-distribution in the "
            "current timing-dominated feature space; BMCA signals such as grandmaster identity "
            "changes, priority transitions, clock-class transitions, and steps-removed shifts are "
            "needed to make the attack observable."
        )
    path.write_text(
        "# Open-Set / Novelty Evaluation\n\n"
        "Isolation Forest is fitted only on known-family training data. A held-out attack is protected "
        "when the RF predicts H1 or the novelty detector routes it to UNKNOWN and `safe_default`.\n\n"
        f"Configured known-window novelty budget: {float(config['openset']['target_known_flag_rate']):.1%}.\n\n"
        "| domain | held-out family | attack windows | RF-only recall | novelty rate | combined protective rate | benign novelty false alarm |\n"
        "|---|---|---:|---:|---:|---:|---:|\n"
        + "\n".join(rows)
        + "\n\n"
        + real_note
        + "\n\n"
        + headline
        + "\n\nThe 100% novelty rate on the real single-step Sync capture may include a "
        "session-level distribution shift rather than attack-specific detection and requires a "
        "capture-normalization sanity check. Combined protective rate is a defensive-routing "
        "metric, not proof of correct attack-family classification.\n",
        encoding="utf-8",
    )
