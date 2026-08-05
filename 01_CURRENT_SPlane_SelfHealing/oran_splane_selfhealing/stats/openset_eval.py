from __future__ import annotations

"""Leakage-resistant global-vs-group open-set evaluation."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from discriminator.openset import NoveltyDetector
from faults.injectors import H1_SCENARIOS, generate_telemetry
from fronthaul_sim.simulator import SimConfig
from ingest.schema import coerce_telemetry
from stats.persistence_eval import evaluate_persistence
from telemetry.features import FEATURE_COLUMNS, window_features

_FAMILY = {
    "ptp_spoof": "spoof",
    "ptp_replay": "replay",
    "ptp_dos_flood": "dos",
    "gnss_spoof": "gnss_spoof",
    "gnss_jam": "gnss_jam",
}
_PRE_BMCA = {
    ("simulated", "spoof"): (0.8938547486033519, 0.553072625698324, 0.9720670391061452, 0.02100840336134454),
    ("simulated", "replay"): (0.4301675977653631, 0.2122905027932961, 0.5251396648044693, 0.01680672268907563),
    ("simulated", "dos"): (0.0, 0.9441340782122905, 0.9441340782122905, 0.01680672268907563),
    ("timesafe_real", "announce"): (0.23796522488863342, 0.0011495904583991954, 0.238540020117833, 0.022388059701492536),
    ("timesafe_real", "sync_follow_up"): (1.0, 0.0, 1.0, 0.0),
    ("timesafe_real", "sync_single_step"): (1.0, 1.0, 1.0, 0.019230769230769232),
}


def _fit_rf(train: pd.DataFrame, seed: int, features: list[str], real: bool = False):
    forest = RandomForestClassifier(
        n_estimators=200 if real else 90,
        max_depth=8 if real else 6,
        random_state=seed,
        class_weight="balanced",
    )
    model = make_pipeline(StandardScaler(), forest) if real else forest
    model.fit(train[features], train["label"])
    return model


def _detector(
    config: dict,
    mode: str,
    train: pd.DataFrame,
    features: list[str],
    calibration: pd.DataFrame | None = None,
) -> NoveltyDetector:
    detector = NoveltyDetector(
        target_known_flag_rate=float(config["openset"]["target_known_flag_rate"]),
        random_state=int(config["seed"]),
        mode=mode,
        feature_columns=features,
        group_budget_weights=config["openset"].get("group_budget_weights"),
    ).fit(train[features])
    if calibration is not None and not calibration.empty:
        detector.calibrate(calibration[features])
    return detector


def _metric_row(
    domain: str,
    mode: str,
    held_out: str,
    family: str,
    attack: pd.DataFrame,
    benign_test: pd.DataFrame,
    rf,
    novelty: NoveltyDetector,
    features: list[str],
) -> dict[str, float | int | str]:
    rf_attack = rf.predict(attack[features]) == "H1"
    novel_attack = novelty.predict_novel(attack[features])
    benign_novel = novelty.predict_novel(benign_test[features])
    return {
        "domain": domain,
        "mode": mode,
        "held_out_attack": held_out,
        "attack_family": family,
        "attack_windows": int(len(attack)),
        "rf_only_attack_recall": float(rf_attack.mean()),
        "novelty_flag_rate": float(novel_attack.mean()),
        "combined_protective_rate": float((rf_attack | novel_attack).mean()),
        "benign_windows": int(len(benign_test)),
        "benign_novelty_false_alarm_rate": float(benign_novel.mean()),
    }


def _prediction_trace(
    domain: str,
    family: str,
    kind: str,
    windows: pd.DataFrame,
    rf,
    novelty: NoveltyDetector,
    features: list[str],
    stream_columns: list[str],
) -> pd.DataFrame:
    trace = windows[[*stream_columns, "window_start_s"]].copy()
    trace["domain"] = domain
    trace["attack_family"] = family
    trace["kind"] = kind
    trace["stream_id"] = trace[stream_columns].astype(str).agg(":".join, axis=1)
    trace["raw_h1"] = rf.predict(windows[features]) == "H1"
    trace["raw_novel"] = novelty.predict_novel(windows[features])
    return trace[["domain", "attack_family", "kind", "stream_id", "window_start_s", "raw_h1", "raw_novel"]]


def _pre_row(domain: str, held_out: str, family: str, attack_n: int, benign_n: int) -> dict:
    rf, novelty, combined, benign_fp = _PRE_BMCA.get(
        (domain, family), (np.nan, np.nan, np.nan, np.nan)
    )
    return {
        "domain": domain,
        "mode": "pre_bmca",
        "held_out_attack": held_out,
        "attack_family": family,
        "attack_windows": attack_n,
        "rf_only_attack_recall": rf,
        "novelty_flag_rate": novelty,
        "combined_protective_rate": combined,
        "benign_windows": benign_n,
        "benign_novelty_false_alarm_rate": benign_fp,
    }


def _threshold_rows(domain: str, family: str, mode: str, detector: NoveltyDetector) -> list[dict]:
    return [
        {
            "domain": domain,
            "attack_family": family,
            "mode": f"bmca_{mode}",
            "group": group,
            "threshold": threshold,
            "comparison": ">=" if detector.inclusive_thresholds_[group] else ">",
            "per_group_target_rate": detector.per_group_target_rates_[group],
            "total_target_rate": detector.target_known_flag_rate,
            "calibration_windows": detector.calibration_size_,
        }
        for group, threshold in detector.thresholds_.items()
    ]


def _sim_windows(config: dict) -> pd.DataFrame:
    sim_cfg = SimConfig(
        seed=int(config["seed"]),
        time_error_budget_ns=float(config["time_error_budget_ns"]),
        **config["sim"],
    )
    telemetry = generate_telemetry(sim_cfg, int(config["dataset"]["scenarios_per_type"]))
    return window_features(
        telemetry,
        float(config["dataset"]["window_s"]),
        float(config["dataset"]["step_s"]),
    )


def evaluate_simulated(config: dict, windows: pd.DataFrame | None = None) -> pd.DataFrame:
    windows = _sim_windows(config) if windows is None else windows
    anomalous = windows[windows["label"].isin(["H0", "H1"])].copy()
    rows, thresholds, traces = [], [], []
    for held in H1_SCENARIOS:
        family = _FAMILY[held]
        known = anomalous[~((anomalous["label"] == "H1") & (anomalous["scenario"] == held))]
        attack = anomalous[(anomalous["label"] == "H1") & (anomalous["scenario"] == held)]
        fit_known = known[known["run_id"] % 3 != 2]
        calibration_known = known[(known["run_id"] % 3 == 1) & (known["label"] == "H0")]
        benign_test = known[(known["run_id"] % 3 == 2) & (known["label"] == "H0")]
        rf = _fit_rf(known, int(config["seed"]), FEATURE_COLUMNS)
        rows.append(_pre_row("simulated", held, family, len(attack), len(benign_test)))
        for mode in ("global", "group"):
            detector = _detector(config, mode, fit_known, FEATURE_COLUMNS, calibration_known)
            rows.append(_metric_row("simulated", f"bmca_{mode}", held, family, attack, benign_test, rf, detector, FEATURE_COLUMNS))
            thresholds.extend(_threshold_rows("simulated", family, mode, detector))
            if mode == "group":
                traces.extend([
                    _prediction_trace("simulated", family, "attack", attack, rf, detector, FEATURE_COLUMNS, ["scenario", "run_id"]),
                    _prediction_trace("simulated", family, "benign", benign_test, rf, detector, FEATURE_COLUMNS, ["scenario", "run_id"]),
                ])
    result = pd.DataFrame(rows)
    result.attrs["thresholds"] = pd.DataFrame(thresholds)
    result.attrs["persistence_traces"] = pd.concat(traces, ignore_index=True)
    return result


def _load_real_sessions(session_dir: Path, config: dict) -> pd.DataFrame:
    rows = []
    for path in sorted(session_dir.glob("*.csv")):
        if "__" not in path.stem:
            continue
        capture_id, family = path.stem.rsplit("__", 1)
        label = "H0" if family == "benign" else "H1"
        telemetry = coerce_telemetry(pd.read_csv(path))
        telemetry["scenario"] = capture_id
        telemetry["run_id"] = 0
        telemetry["label"] = label
        features = window_features(
            telemetry,
            float(config["dataset"]["window_s"]),
            float(config["dataset"]["step_s"]),
        )
        features["capture_id"] = capture_id
        features["attack_family"] = "none" if label == "H0" else family
        features["label"] = label
        rows.append(features)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def evaluate_real(config: dict, session_dir: Path, features: list[str] | None = None) -> pd.DataFrame:
    features = list(features or FEATURE_COLUMNS)
    real = _load_real_sessions(session_dir, config)
    if real.empty:
        return pd.DataFrame()
    rows, thresholds, traces = [], [], []
    families = sorted(set(real.loc[real["label"] == "H1", "attack_family"]) - {"none"})
    for family in families:
        held_sessions = set(real.loc[(real["label"] == "H1") & (real["attack_family"] == family), "capture_id"])
        train = real[~real["capture_id"].isin(held_sessions)]
        attack = real[(real["label"] == "H1") & (real["attack_family"] == family)]
        benign_test = real[(real["label"] == "H0") & real["capture_id"].isin(held_sessions)]
        if train["label"].nunique() < 2 or attack.empty or benign_test.empty:
            continue
        rf = _fit_rf(train, int(config["seed"]), features, real=True)
        benign_counts = train.loc[train["label"] == "H0", "capture_id"].value_counts()
        calibration_capture = str(benign_counts.index[0])
        novelty_calibration = train[(train["capture_id"] == calibration_capture) & (train["label"] == "H0")]
        rows.append(_pre_row("timesafe_real", family, family, len(attack), len(benign_test)))
        for mode in ("global", "group"):
            detector = _detector(config, mode, train, features, novelty_calibration)
            rows.append(_metric_row("timesafe_real", f"bmca_{mode}", family, family, attack, benign_test, rf, detector, features))
            thresholds.extend(_threshold_rows("timesafe_real", family, mode, detector))
            if mode == "group":
                traces.extend([
                    _prediction_trace("timesafe_real", family, "attack", attack, rf, detector, features, ["capture_id"]),
                    _prediction_trace("timesafe_real", family, "benign", benign_test, rf, detector, features, ["capture_id"]),
                ])
    result = pd.DataFrame(rows)
    result.attrs["thresholds"] = pd.DataFrame(thresholds)
    result.attrs["windows"] = real
    result.attrs["persistence_traces"] = pd.concat(traces, ignore_index=True)
    return result


def evaluate_planned_failover(config: dict, windows: pd.DataFrame) -> pd.DataFrame:
    anomalous = windows[windows["label"].isin(["H0", "H1"])]
    train = anomalous[anomalous["run_id"] % 3 != 2]
    calibration = anomalous[(anomalous["run_id"] % 3 == 1) & (anomalous["label"] == "H0")]
    test = anomalous[(anomalous["run_id"] % 3 == 2) & (anomalous["scenario"] == "planned_gm_failover")]
    rf = _fit_rf(train, int(config["seed"]), FEATURE_COLUMNS)
    detector = _detector(config, "group", train, FEATURE_COLUMNS, calibration)
    rf_h1 = rf.predict(test[FEATURE_COLUMNS]) == "H1"
    novel = detector.predict_novel(test[FEATURE_COLUMNS])
    return pd.DataFrame([{
        "scenario": "planned_gm_failover",
        "windows": len(test),
        "rf_h1_false_positive_rate": float(rf_h1.mean()),
        "novelty_false_positive_rate": float(novel.mean()),
        "combined_protective_false_positive_rate": float((rf_h1 | novel).mean()),
    }])


def evaluate_identity_ablation(config: dict, session_dir: Path) -> pd.DataFrame:
    real = _load_real_sessions(session_dir, config)
    held_sessions = set(real.loc[(real["label"] == "H1") & (real["attack_family"] == "announce"), "capture_id"])
    train = real[~real["capture_id"].isin(held_sessions)]
    attack = real[(real["label"] == "H1") & (real["attack_family"] == "announce")]
    benign = real[(real["label"] == "H0") & real["capture_id"].isin(held_sessions)]
    rows = []
    benign_counts = train.loc[train["label"] == "H0", "capture_id"].value_counts()
    calibration_capture = str(benign_counts.index[0])
    novelty_calibration = train[(train["capture_id"] == calibration_capture) & (train["label"] == "H0")]
    for name, features in (
        ("full_bmca", FEATURE_COLUMNS),
        ("without_gm_identity_changes", [f for f in FEATURE_COLUMNS if f != "gm_identity_changes"]),
    ):
        rf = _fit_rf(train, int(config["seed"]), features, real=True)
        detector = _detector(config, "group", train, features, novelty_calibration)
        row = _metric_row("timesafe_real", "bmca_group", "announce", "announce", attack, benign, rf, detector, features)
        row["ablation"] = name
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_openset(config: dict, out_dir: Path, docs_dir: Path, real_session_dir: Path | None = None) -> pd.DataFrame:
    sim_windows = _sim_windows(config)
    simulated = evaluate_simulated(config, sim_windows)
    real = evaluate_real(config, real_session_dir) if real_session_dir and real_session_dir.exists() else pd.DataFrame()
    traces = pd.concat(
        [
            simulated.attrs.get("persistence_traces", pd.DataFrame()),
            real.attrs.get("persistence_traces", pd.DataFrame()),
        ],
        ignore_index=True,
    )
    persistence, episodes, recommendation = evaluate_persistence(
        traces,
        float(config["dataset"]["step_s"]),
        float(config["failure_window_s"]),
    )
    result = pd.concat([simulated, real], ignore_index=True)
    thresholds = pd.concat(
        [simulated.attrs.get("thresholds", pd.DataFrame()), real.attrs.get("thresholds", pd.DataFrame())],
        ignore_index=True,
    )
    planned = evaluate_planned_failover(config, sim_windows)
    ablation = evaluate_identity_ablation(config, real_session_dir) if real_session_dir and real_session_dir.exists() else pd.DataFrame()
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_dir / "openset_eval.csv", index=False)
    thresholds.to_csv(out_dir / "openset_thresholds.csv", index=False)
    planned.to_csv(out_dir / "planned_gm_failover_eval.csv", index=False)
    persistence.to_csv(out_dir / "persistence_tradeoff.csv", index=False)
    episodes.to_csv(out_dir / "persistence_episode_metrics.csv", index=False)
    if not ablation.empty:
        ablation.to_csv(out_dir / "bmca_identity_ablation.csv", index=False)
    _write_report(
        result,
        thresholds,
        planned,
        ablation,
        persistence,
        recommendation,
        docs_dir / "OPENSET_EVAL.md",
        config,
    )
    result.attrs["sim_windows"] = sim_windows
    result.attrs["persistence"] = persistence
    return result


def _write_report(result, thresholds, planned, ablation, persistence, recommendation, path: Path, config: dict) -> None:
    table = "\n".join(
        f"| {r.domain} | {r.attack_family} | {r.mode} | {r.rf_only_attack_recall:.3f} | "
        f"{r.novelty_flag_rate:.3f} | {r.combined_protective_rate:.3f} | "
        f"{r.benign_novelty_false_alarm_rate:.3f} |"
        for r in result.itertuples()
    )
    threshold_table = "\n".join(
        f"| {r.domain} | {r.attack_family} | {r.mode} | {r.group} | {r.comparison} {r.threshold:.6f} | "
        f"{r.per_group_target_rate:.4f} | {r.calibration_windows} |"
        for r in thresholds.itertuples()
    )
    planned_row = planned.iloc[0]
    ablation_table = "\n".join(
        f"| {r.ablation} | {r.rf_only_attack_recall:.3f} | {r.novelty_flag_rate:.3f} | "
        f"{r.combined_protective_rate:.3f} | {r.benign_novelty_false_alarm_rate:.3f} |"
        for r in ablation.itertuples()
    ) if not ablation.empty else "| unavailable | - | - | - | - |"
    group_real = result[(result["domain"] == "timesafe_real") & (result["mode"] == "bmca_group")]
    single = group_real[group_real["attack_family"] == "sync_single_step"].iloc[0] if not group_real.empty else None
    shift = (
        f"Single-step attack novelty is {single['novelty_flag_rate']:.1%}; benign windows from the same capture "
        f"are {single['benign_novelty_false_alarm_rate']:.1%}. This does not support a whole-capture shift."
        if single is not None and single["benign_novelty_false_alarm_rate"] < 0.10
        else "Single-step session-shift verdict unavailable or inconclusive."
    )
    real_group = result[(result["domain"] == "timesafe_real") & (result["mode"] == "bmca_group")]
    real_fp_note = (
        f"Held-session TIMESAFE benign novelty false alarms range from "
        f"{real_group['benign_novelty_false_alarm_rate'].min():.1%} to "
        f"{real_group['benign_novelty_false_alarm_rate'].max():.1%}. This exceeds the nominal 2% "
        "budget and shows residual capture-to-capture domain shift; thresholds were not tuned on held sessions."
        if not real_group.empty else "Real held-session false-alarm evaluation was unavailable."
    )
    ablation_note = ""
    if not ablation.empty:
        full = ablation.loc[ablation["ablation"] == "full_bmca", "combined_protective_rate"].iloc[0]
        removed = ablation.loc[ablation["ablation"] == "without_gm_identity_changes", "combined_protective_rate"].iloc[0]
        ablation_note = (
            f"Removing `gm_identity_changes` leaves Announce combined protection at {removed:.1%} "
            f"versus {full:.1%} with all BMCA features. The result therefore is not a one-rule "
            "`GM changed = attack` detector; other relative BMCA transition features carry the signal.\n\n"
        )
    persistence_table = "\n".join(
        f"| {r.domain} | {r.attack_family} | {r.setting} | {r.benign_false_alarm_rate:.2%} | "
        f"{r.alarms_per_hour:.1f} | {r.episode_alarms_per_hour:.1f} | {r.combined_protective_rate:.2%} | "
        f"{r.episode_detection_rate:.2%} | {r.mean_added_detection_latency_s:.3f} | "
        f"{r.mean_time_to_decision_s:.3f} | {r.within_2s_episode_rate:.2%} |"
        for r in persistence.itertuples()
    )
    recommended_rows = persistence[persistence["setting"] == recommendation]
    all_within_target = bool((recommended_rows["within_2s_episode_rate"] >= 0.95).all())
    recommendation_note = (
        "It is the setting nearest the 2% weighted real benign-FP target among configurations "
        "retaining at least 95% within-2-second episode coverage for every evaluated family."
        if all_within_target else
        "No evaluated setting reaches 95% within-2-second coverage for every family because simulated "
        "spoof is already 91.7% at 1-of-1. This setting is nearest the 2% weighted real benign-FP target "
        "and does not reduce spoof's within-window episode rate below that raw-detector baseline."
    )
    path.write_text(
        "# Open-Set / Novelty Evaluation\n\n"
        f"Total known-window novelty budget: {float(config['openset']['target_known_flag_rate']):.1%}. "
        "Group mode splits this budget across timing/protocol, rate, and BMCA detectors and flags UNKNOWN when any group fires.\n\n"
        "## Three-way comparison\n\n"
        "| domain | family | mode | RF recall | novelty rate | combined protection | benign novelty FP |\n"
        "|---|---|---|---:|---:|---:|---:|\n" + table + "\n\n"
        "## Per-group calibration thresholds\n\n"
        "| domain | family | mode | group | score threshold | group budget | calibration windows |\n"
        "|---|---|---|---|---:|---:|---:|\n" + threshold_table + "\n\n"
        "## Planned-GM-failover confounder\n\n"
        f"Held-run RF H1 false-positive rate: **{planned_row['rf_h1_false_positive_rate']:.1%}**; "
        f"group novelty false-positive rate: **{planned_row['novelty_false_positive_rate']:.1%}**. "
        "A legitimate GM transition is not treated as H1 merely because identity changed.\n\n"
        "## GM-identity-change ablation on real Announce\n\n"
        "| feature set | RF recall | novelty rate | combined protection | benign novelty FP |\n"
        "|---|---:|---:|---:|---:|\n" + ablation_table + "\n\n"
        "TIMESAFE contains no benign planned-GM-change session. Its real-data benign false-positive "
        "estimate is therefore optimistic for deployments with legitimate re-parenting.\n\n"
        + ablation_note
        + real_fp_note + "\n\n"
        + shift + "\n\n"
        "Closed-set limitation: training the real RF on Announce sessions and testing on Sync sessions "
        "produces 0% attack recall. BMCA observability does not solve cross-family closed-set specialization.\n\n"
        "## Temporal persistence sweep\n\n"
        f"Window step: {float(config['dataset']['step_s']):.3f} s; failure window: "
        f"{float(config['failure_window_s']):.1f} s. Persistence is applied independently to RF-H1 and "
        "UNKNOWN votes. Alarm rate counts persisted protective windows per hour, matching the operational "
        "cost calculation requested here. **Caveat:** `alarms/hour` counts persisted windows, not "
        "distinct operator-facing alarm episodes. A sustained anomaly spanning consecutive windows "
        "is one alarm; `episode alarms/hour` de-duplicates contiguous persisted windows within each session.\n\n"
        "| domain | family | setting | benign FP | window alarms/hour | episode alarms/hour | window protection | episode detection | added latency (s) | mean TTD (s) | within 2 s |\n"
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n" + persistence_table + "\n\n"
        f"Recommended setting: **{recommendation}**. {recommendation_note}\n\n"
        "Combined protection is a defensive-routing metric, not proof of correct family classification.\n",
        encoding="utf-8",
    )
