from __future__ import annotations

"""Leakage-resistant calibration on independently captured S-plane sessions.

Inputs may be PTP pcaps or canonical telemetry CSVs. Multiple files are required
for an honest real-trained evaluation: every ``capture_id`` is assigned wholly
to train or test. Leave-one-attack-out additionally removes all sessions for the
held-out attack family from training.
"""

import argparse
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataset.build import build_dataset
from ingest.pcap_ingest import pcap_to_telemetry
from telemetry.features import FEATURE_COLUMNS, window_features


def _cfg() -> dict:
    with (ROOT / "config" / "default.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _infer_attack_family(path: str) -> str:
    name = Path(path).stem.lower().replace("-", "_")
    if "replay" in name:
        return "replay"
    if "singlestep" in name or "single_step" in name:
        return "sync_single_step"
    if "sync" in name and "announce" not in name:
        return "sync_follow_up"
    if "announce" in name:
        return "announce"
    return "unspecified"


def _source_to_windows(
    path: str,
    label: str,
    scenario: str,
    cfg: dict,
    attack_family: str = "none",
) -> pd.DataFrame:
    source = Path(path)
    if source.suffix.lower() in (".pcap", ".pcapng"):
        telemetry = pcap_to_telemetry(source, scenario=scenario, label=label)
    else:
        telemetry = pd.read_csv(source)
    capture_id = (
        str(telemetry["capture_id"].iloc[0])
        if "capture_id" in telemetry and not telemetry.empty
        else source.stem
    )
    family = (
        str(telemetry["attack_family"].iloc[0])
        if "attack_family" in telemetry and not telemetry.empty
        else attack_family
    )
    telemetry["scenario"] = scenario
    telemetry["label"] = label
    telemetry["run_id"] = 0
    windows = window_features(
        telemetry,
        float(cfg["dataset"]["window_s"]),
        float(cfg["dataset"]["step_s"]),
    )
    windows["capture_id"] = capture_id
    windows["attack_family"] = family if label == "H1" else "none"
    windows["source_path"] = str(source)
    return windows


def _load_many(
    paths: list[str],
    label: str,
    cfg: dict,
    families: list[str] | None = None,
) -> pd.DataFrame:
    frames = []
    for index, path in enumerate(paths):
        family = families[index] if families else _infer_attack_family(path)
        frames.append(
            _source_to_windows(
                path,
                label,
                f"real_{label.lower()}_{index}",
                cfg,
                attack_family=family,
            )
        )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _wilson95(successes: int, total: int) -> tuple[float, float]:
    if total == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    rate = successes / total
    denominator = 1.0 + z * z / total
    centre = rate + z * z / (2.0 * total)
    margin = z * math.sqrt(rate * (1.0 - rate) / total + z * z / (4.0 * total * total))
    return (centre - margin) / denominator, (centre + margin) / denominator


def _metric_row(method: str, pred: np.ndarray, truth: np.ndarray, held_out: str) -> dict:
    truth = truth.astype(bool)
    pred = pred.astype(bool)
    benign = ~truth
    attack = truth
    fp_count = int(pred[benign].sum())
    tp_count = int(pred[attack].sum())
    n_benign = int(benign.sum())
    n_attack = int(attack.sum())
    fp_low, fp_high = _wilson95(fp_count, n_benign)
    tp_low, tp_high = _wilson95(tp_count, n_attack)
    return {
        "method": method,
        "held_out": held_out,
        "benign_windows": n_benign,
        "benign_fp_count": fp_count,
        "benign_FP_rate": fp_count / n_benign if n_benign else float("nan"),
        "benign_FP_ci95_low": fp_low,
        "benign_FP_ci95_high": fp_high,
        "attack_windows": n_attack,
        "attack_tp_count": tp_count,
        "attack_TP_rate": tp_count / n_attack if n_attack else float("nan"),
        "attack_TP_ci95_low": tp_low,
        "attack_TP_ci95_high": tp_high,
    }


def _session_holdout(real: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = real["capture_id"].astype(str)
    if groups.nunique() < 2:
        raise ValueError("session-level holdout requires at least two independent capture_id values")
    splitter = GroupShuffleSplit(n_splits=100, test_size=0.35, random_state=seed)
    for train_index, test_index in splitter.split(real, real["is_attack"], groups):
        train = real.iloc[train_index]
        test = real.iloc[test_index]
        if train["is_attack"].nunique() == 2 and test["is_attack"].nunique() == 2:
            return train, test
    raise ValueError(
        "could not form a session-level split containing benign and attack windows "
        "in both train and test; provide more independent captures"
    )


def _fit_real_rf(train: pd.DataFrame, seed: int) -> tuple[StandardScaler, RandomForestClassifier]:
    scaler = StandardScaler().fit(train[FEATURE_COLUMNS])
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=seed,
        class_weight="balanced",
    )
    model.fit(scaler.transform(train[FEATURE_COLUMNS]), train["is_attack"].astype(bool))
    return scaler, model


def _sim_model(cfg: dict) -> RandomForestClassifier:
    with tempfile.TemporaryDirectory() as temp_dir:
        simulated = build_dataset(cfg, Path(temp_dir) / "ds")
    anomalous = simulated[simulated["label"].isin(["H0", "H1"])]
    model = RandomForestClassifier(
        n_estimators=90,
        max_depth=6,
        random_state=cfg["seed"],
        class_weight="balanced",
    )
    model.fit(anomalous[FEATURE_COLUMNS], anomalous["label"])
    return model


def _leave_one_attack_out(real: pd.DataFrame, cfg: dict) -> list[dict]:
    rows: list[dict] = []
    families = sorted(set(real.loc[real["is_attack"], "attack_family"]) - {"none", "unspecified"})
    for family in families:
        held_sessions = set(
            real.loc[
                real["is_attack"] & (real["attack_family"] == family),
                "capture_id",
            ].astype(str)
        )
        test = real[
            real["capture_id"].astype(str).isin(held_sessions)
            & ((~real["is_attack"]) | (real["attack_family"] == family))
        ]
        train = real[~real["capture_id"].astype(str).isin(held_sessions)]
        if train["is_attack"].nunique() < 2 or test["is_attack"].nunique() < 2:
            continue
        scaler, model = _fit_real_rf(train, int(cfg["seed"]))
        prediction = model.predict(scaler.transform(test[FEATURE_COLUMNS]))
        rows.append(_metric_row("real_trained_rf_leave_one_attack_out", prediction, test["is_attack"].to_numpy(), family))
    return rows


def calibrate(benign: pd.DataFrame, attack: pd.DataFrame, cfg: dict, out_dir: Path) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    real = pd.concat(
        [benign.assign(is_attack=False), attack.assign(is_attack=True)],
        ignore_index=True,
    )
    train, test = _session_holdout(real, int(cfg["seed"]))
    truth = test["is_attack"].to_numpy()
    results: list[dict] = []

    sim_model = _sim_model(cfg)
    sim_prediction = sim_model.predict(test[FEATURE_COLUMNS]) == "H1"
    results.append(_metric_row("baseline_sim_rf", sim_prediction, truth, "session_holdout"))

    budget = float(cfg["time_error_budget_ns"])
    flat_prediction = test["offset_abs_max"].to_numpy() > budget
    results.append(_metric_row("baseline_flat_threshold", flat_prediction, truth, "session_holdout"))

    benign_train = train.loc[~train["is_attack"], "offset_abs_max"]
    threshold = float(np.quantile(benign_train, 0.99))
    recal_prediction = test["offset_abs_max"].to_numpy() > threshold
    results.append(
        _metric_row(
            f"recalibrated_threshold_{threshold:.0f}ns",
            recal_prediction,
            truth,
            "session_holdout",
        )
    )

    scaler, real_model = _fit_real_rf(train, int(cfg["seed"]))
    real_prediction = real_model.predict(scaler.transform(test[FEATURE_COLUMNS]))
    results.append(_metric_row("real_trained_rf_session_holdout", real_prediction, truth, "session_holdout"))
    results.extend(_leave_one_attack_out(real, cfg))

    summary = pd.DataFrame(results)
    summary.to_csv(out_dir / "real_calibration_summary.csv", index=False)
    _report(summary, out_dir, train, test, real)
    return summary


def _format_ci(rate: float, low: float, high: float) -> str:
    return f"{rate:.3f} [{low:.3f}, {high:.3f}]"


def _report(
    summary: pd.DataFrame,
    out_dir: Path,
    train: pd.DataFrame,
    test: pd.DataFrame,
    real: pd.DataFrame,
) -> None:
    table_rows = []
    for row in summary.itertuples():
        table_rows.append(
            f"| {row.method} | {row.held_out} | "
            f"{row.benign_fp_count}/{row.benign_windows} | "
            f"{_format_ci(row.benign_FP_rate, row.benign_FP_ci95_low, row.benign_FP_ci95_high)} | "
            f"{row.attack_tp_count}/{row.attack_windows} | "
            f"{_format_ci(row.attack_TP_rate, row.attack_TP_ci95_low, row.attack_TP_ci95_high)} |"
        )
    train_sessions = ", ".join(sorted(train["capture_id"].astype(str).unique()))
    test_sessions = ", ".join(sorted(test["capture_id"].astype(str).unique()))
    report = (
        "# Real-Data Calibration Report\n\n"
        "Evaluation unit: complete capture session. No windows from a test capture "
        "appear in training. Confidence intervals are 95% Wilson intervals.\n\n"
        f"All real windows: {int((~real['is_attack']).sum())} benign, "
        f"{int(real['is_attack'].sum())} attack across {real['capture_id'].nunique()} sessions.\n\n"
        f"Session holdout train captures: `{train_sessions}`.\n\n"
        f"Session holdout test captures: `{test_sessions}`.\n\n"
        "| method | held out | benign FP count | benign FP rate [95% CI] | "
        "attack TP count | attack TP rate [95% CI] |\n"
        "|---|---|---:|---:|---:|---:|\n"
        + "\n".join(table_rows)
        + "\n\n"
        "The session-holdout row is the primary transfer estimate. Leave-one-attack-out "
        "rows test family generalization and are omitted when the supplied captures do "
        "not leave both classes in train and test.\n"
    )
    (out_dir / "REAL_CALIBRATION_REPORT.md").write_text(report, encoding="utf-8")


def _synthetic_selfcheck(cfg: dict, out_dir: Path) -> pd.DataFrame:
    with tempfile.TemporaryDirectory() as temp_dir:
        windows = build_dataset(cfg, Path(temp_dir) / "ds")
    benign = windows[windows["label"] == "H0"].copy()
    attack = windows[windows["label"] == "H1"].copy()
    benign["capture_id"] = (
        "benign_" + benign["scenario"].astype(str) + "_" + benign["run_id"].astype(str)
    )
    attack["capture_id"] = (
        "attack_" + attack["scenario"].astype(str) + "_" + attack["run_id"].astype(str)
    )
    attack["attack_family"] = attack["scenario"].astype(str)
    benign["attack_family"] = "none"
    return calibrate(benign, attack, cfg, out_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benign-files", nargs="+", help="benign capture/telemetry files")
    parser.add_argument("--attack-files", nargs="+", help="attack capture/telemetry files")
    parser.add_argument(
        "--attack-families",
        nargs="+",
        help="family per --attack-files entry; otherwise inferred from each filename",
    )
    parser.add_argument("--benign", help=argparse.SUPPRESS)
    parser.add_argument("--attack", help=argparse.SUPPRESS)
    parser.add_argument("--out-dir", default=str(ROOT / "results" / "tier2" / "real_calibration"))
    args = parser.parse_args()
    benign_files = args.benign_files or ([args.benign] if args.benign else [])
    attack_files = args.attack_files or ([args.attack] if args.attack else [])
    if args.attack_families and len(args.attack_families) != len(attack_files):
        parser.error("--attack-families must contain one value per --attack-files entry")

    cfg = _cfg()
    out_dir = Path(args.out_dir)
    if benign_files and attack_files:
        benign = _load_many(benign_files, "H0", cfg)
        attack = _load_many(attack_files, "H1", cfg, args.attack_families)
        summary = calibrate(benign, attack, cfg, out_dir)
    else:
        print("no real files given: running SYNTHETIC self-check (plumbing only)")
        summary = _synthetic_selfcheck(cfg, out_dir)
    print(summary.to_string(index=False))
    print(f"\nwrote {out_dir / 'REAL_CALIBRATION_REPORT.md'}")


if __name__ == "__main__":
    main()
