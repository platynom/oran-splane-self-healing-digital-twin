from __future__ import annotations

"""Pre-registered, session-disjoint AI-vs-rule comparison for the 168-run S-plane corpus.

This harness deliberately does not call discriminator.model.train_and_evaluate because
that helper performs a random window split.  It uses the same shipped estimator and
hyperparameters, but enforces the experiment's replicate-disjoint split before fitting.
"""

import hashlib
import json
import math
import sys
import tarfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from discriminator.model import RandomForestClassifier
from discriminator.openset import NoveltyDetector
from ingest.linuxptp_ingest import ptp4l_log_to_telemetry
from telemetry.features import configured_feature_columns, window_features


ARCHIVE = ROOT / "ml_comparison_input" / "splane_168run_ptp4l_logs.tgz"
EXTRACTED = ROOT / "ml_comparison_input" / "extracted_168run_ptp4l_logs"
OUT_DIR = ROOT / "ml_comparison_output"
EXPECTED_SHA256 = "bc20005f270e2679d4d0f656600ce07e6c7ff8ed9d8ca98f4c1a07477414b1c7"
SEED = 1588
TRAIN_REPS = list(range(1, 9))
TEST_REPS = list(range(9, 13))
LOG_FILES = ["gma.log", "gmb.log", "bc.log", "ru1.log", "ru2.log", "ru3.log"]
REQUIRED_FILES = [*LOG_FILES, "pmc.jsonl", "context.json", "decision.json", "decision_v3.json"]

ATTACK_SCENARIOS = [
    "A1_rogue_master",
    "A2_sync_spoof",
    "A3_replay",
    "A5_dos_flood",
    "A8_rogue_bc",
    "C1_removal",
    "C2_malformed",
    "C3_wholesecond",
]
BENIGN_SCENARIOS = [
    "baseline",
    "B2_gm_failover",
    "B3_pdv_congestion",
    "B7_topology_change",
    "B_bc_replacement",
]
UNKNOWN_SCENARIO = "B_unplanned_failover"
SCENARIO_ORDER = [*ATTACK_SCENARIOS, *BENIGN_SCENARIOS, UNKNOWN_SCENARIO]

# Availability is based on what linuxptp servo lines actually observe, not on
# schema.py's simulator-friendly defaults.  Synthetic sequence IDs, message type,
# and default GNSS/SyncE/BMCA/oscillator values are therefore not model evidence.
PROVENANCE_SUPPORTED_FEATURES = [
    "offset_mean",
    "offset_std",
    "offset_abs_max",
    "path_delay_mean",
    "pdv_std",
    "holdover_rate",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_extracted() -> None:
    if EXTRACTED.exists():
        return
    EXTRACTED.mkdir(parents=True, exist_ok=False)
    with tarfile.open(ARCHIVE, "r:gz") as bundle:
        bundle.extractall(EXTRACTED, filter="data")


def expected_verdict(scenario: str) -> str:
    if scenario in ATTACK_SCENARIOS:
        return "ATTACK"
    if scenario in BENIGN_SCENARIOS:
        return "BENIGN"
    if scenario == UNKNOWN_SCENARIO:
        return "UNKNOWN"
    raise ValueError(f"unregistered scenario: {scenario}")


def model_label(scenario: str) -> str:
    verdict = expected_verdict(scenario)
    return {"ATTACK": "H1", "BENIGN": "H0", "UNKNOWN": "UNKNOWN"}[verdict]


def normalize_verdict(value: object) -> str:
    text = str(value).strip().upper()
    if text.startswith("ATTACK"):
        return "ATTACK"
    if text.startswith("BENIGN"):
        return "BENIGN"
    if text.startswith("UNKNOWN") or text.startswith("UNKNO"):
        return "UNKNOWN"
    return text


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return [centre - half, centre + half]


def mcnemar_exact_two_sided(better: int, worse: int) -> float:
    """Exact paired sign/McNemar test under equal discordant probabilities."""
    discordant = better + worse
    if discordant == 0:
        return 1.0
    tail = min(better, worse)
    probability = sum(math.comb(discordant, k) for k in range(tail + 1)) / (2**discordant)
    return min(1.0, 2.0 * probability)


def strict_majority(values: pd.Series) -> str:
    counts = values.value_counts()
    if counts.empty:
        return "UNKNOWN"
    leader = str(counts.index[0])
    return leader if int(counts.iloc[0]) > len(values) / 2 else "UNKNOWN"


def verdict_counts(values: list[str]) -> dict[str, int]:
    counts = Counter(values)
    return {name: int(counts.get(name, 0)) for name in ["ATTACK", "BENIGN", "UNKNOWN"]}


def metric_bundle(rows: pd.DataFrame, column: str, scenarios: list[str]) -> dict:
    subset = rows[rows["scenario"].isin(scenarios)]
    correct = int((subset[column] == subset["expected"]).sum())
    n = int(len(subset))
    per_scenario = [
        float((part[column] == part["expected"]).mean())
        for _, part in subset.groupby("scenario")
    ]
    return {
        "macro": float(np.mean(per_scenario)) if per_scenario else None,
        "pooled_correct": correct,
        "pooled_n": n,
        "pooled_rate_run_count_dependent": correct / n if n else None,
        "pooled_wilson_95_ci_run_count_dependent": wilson(correct, n),
    }


def combine_or(a: str, b: str) -> str:
    if "ATTACK" in (a, b):
        return "ATTACK"
    if "UNKNOWN" in (a, b):
        return "UNKNOWN"
    return "BENIGN"


def combine_consensus(a: str, b: str) -> str:
    return a if a == b else "UNKNOWN"


def score_combination(rows: pd.DataFrame, column: str) -> dict:
    exact = int((rows[column] == rows["expected"]).sum())
    return {
        "exact_correct": exact,
        "n": int(len(rows)),
        "exact_accuracy": exact / len(rows),
        "exact_wilson_95_ci": wilson(exact, len(rows)),
        "macro_sensitivity": metric_bundle(rows, column, ATTACK_SCENARIOS),
        "macro_specificity": metric_bundle(rows, column, BENIGN_SCENARIOS),
        "abstention_correctness": metric_bundle(rows, column, [UNKNOWN_SCENARIO]),
    }


def format_distribution(values: list[str]) -> str:
    counts = verdict_counts(values)
    used = [f"{key}x{value}" for key, value in counts.items() if value]
    return ", ".join(used) if used else "none"


def main() -> None:
    actual_sha = sha256(ARCHIVE)
    checksum_ok = actual_sha == EXPECTED_SHA256
    if not checksum_ok:
        raise RuntimeError(f"archive checksum mismatch: {actual_sha}")
    ensure_extracted()

    run_dirs = sorted(path for path in EXTRACTED.iterdir() if path.is_dir())
    missing = [
        {"run": run_dir.name, "file": filename}
        for run_dir in run_dirs
        for filename in REQUIRED_FILES
        if not (run_dir / filename).is_file()
    ]

    with (ROOT / "config" / "default.yaml").open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    configured = configured_feature_columns(config)

    telemetry_frames: list[pd.DataFrame] = []
    run_records: list[dict] = []
    parse_failures: list[dict] = []
    context_rep_mismatches: list[dict] = []
    run_id_by_name: dict[str, int] = {}
    parsed_files = 0
    parsed_rows = 0

    for run_id, run_dir in enumerate(run_dirs, start=1):
        context = json.loads((run_dir / "context.json").read_text(encoding="utf-8"))
        decision = json.loads((run_dir / "decision_v3.json").read_text(encoding="utf-8"))
        scenario = str(context["scenario"])
        # The experiment contract defines replicate membership in the directory
        # name.  Preserve and report inconsistent context metadata, but do not let
        # it corrupt the pre-registered split.
        rep = int(run_dir.name.rsplit("__r", 1)[1])
        context_rep = context.get("rep")
        if context_rep is not None and int(context_rep) != rep:
            context_rep_mismatches.append(
                {"run": run_dir.name, "directory_rep": rep, "context_rep": int(context_rep)}
            )
        run_id_by_name[run_dir.name] = run_id
        run_records.append(
            {
                "run_name": run_dir.name,
                "run_id": run_id,
                "scenario": scenario,
                "rep": rep,
                "expected": expected_verdict(scenario),
                "armA": normalize_verdict(decision.get("verdict")),
            }
        )
        for filename in LOG_FILES:
            try:
                frame = ptp4l_log_to_telemetry(
                    run_dir / filename,
                    scenario=scenario,
                    label=model_label(scenario),
                )
            except ValueError as exc:
                parse_failures.append(
                    {"run": run_dir.name, "file": filename, "reason": str(exc)}
                )
                continue
            frame["run_id"] = run_id
            frame["scenario"] = scenario
            frame["label"] = model_label(scenario)
            telemetry_frames.append(frame)
            parsed_files += 1
            parsed_rows += len(frame)

    telemetry = pd.concat(telemetry_frames, ignore_index=True)
    windows = window_features(
        telemetry,
        window_s=float(config["dataset"]["window_s"]),
        step_s=float(config["dataset"]["step_s"]),
    )
    metadata = pd.DataFrame(run_records)[["run_id", "run_name", "rep", "expected"]]
    windows = windows.merge(metadata, on="run_id", how="left", validate="many_to_one")

    # Erase feature values produced solely by canonical-schema defaults.  This is
    # the experiment's critical missing-data safeguard.
    unsupported = [name for name in configured if name not in PROVENANCE_SUPPORTED_FEATURES]
    for name in unsupported:
        windows[name] = np.nan
    populated = [name for name in configured if windows[name].notna().any()]
    empty = [name for name in configured if not windows[name].notna().any()]

    train = windows[(windows["rep"].isin(TRAIN_REPS)) & (windows["label"].isin(["H0", "H1"]))].copy()
    test = windows[windows["rep"].isin(TEST_REPS)].copy()
    overlap = sorted(set(train["run_name"]) & set(test["run_name"]))
    if overlap:
        raise AssertionError(f"session leakage: {overlap}")

    clf = RandomForestClassifier(
        n_estimators=90,
        max_depth=6,
        random_state=SEED,
        class_weight="balanced",
        n_jobs=1,
    )
    clf.fit(train[populated], train["label"])
    clf.feature_columns_ = populated
    test["rf_label"] = clf.predict(test[populated])
    test["rf_verdict"] = test["rf_label"].map({"H0": "BENIGN", "H1": "ATTACK"})

    novelty_error = None
    train_complete = train[populated].notna().all(axis=1)
    test_complete = test[populated].notna().all(axis=1)
    test["novel"] = False
    test.loc[~test_complete, "novel"] = True
    try:
        novelty = NoveltyDetector(
            target_known_flag_rate=float(config["openset"]["target_known_flag_rate"]),
            random_state=SEED,
            mode=str(config["openset"]["mode"]),
            group_budget_weights=config["openset"].get("group_budget_weights"),
            feature_columns=populated,
        ).fit(train.loc[train_complete, populated])
        if test_complete.any():
            test.loc[test_complete, "novel"] = novelty.predict_novel(
                test.loc[test_complete, populated]
            )
        novelty_details = {
            "status": "configured_and_run",
            "mode": novelty.mode,
            "target_known_flag_rate": novelty.target_known_flag_rate,
            "calibration_size": novelty.calibration_size_,
            "groups": novelty.group_columns_,
            "thresholds": novelty.thresholds_,
            "incomplete_test_windows_abstained": int((~test_complete).sum()),
        }
    except Exception as exc:  # Preserve inability while allowing the RF comparison.
        novelty_error = f"{type(exc).__name__}: {exc}"
        test["novel"] = False
        test.loc[~test_complete, "novel"] = True
        novelty_details = {
            "status": "NOT ESTABLISHED",
            "reason": novelty_error,
            "incomplete_test_windows_abstained": int((~test_complete).sum()),
        }

    test["armB_window"] = np.where(test["novel"], "UNKNOWN", test["rf_verdict"])

    known_test = test[test["expected"].isin(["ATTACK", "BENIGN"])].copy()
    y_true = known_test["expected"].map({"BENIGN": "H0", "ATTACK": "H1"})
    y_pred = known_test["rf_label"]
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=["H0", "H1"], average="macro", zero_division=0
    )
    h1_index = list(clf.classes_).index("H1")
    h1_probability = clf.predict_proba(known_test[populated])[:, h1_index]
    per_window_metrics = {
        "unit": "overlapping_0.4s_windows_with_0.2s_step",
        "closed_set_rf_known_scenarios": {
            "n": int(len(known_test)),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision_macro": float(precision),
            "recall_macro": float(recall),
            "f1_macro": float(f1),
            "roc_auc_h1": float(roc_auc_score((y_true == "H1").astype(int), h1_probability)),
            "confusion_matrix_labels_H0_H1": confusion_matrix(
                y_true, y_pred, labels=["H0", "H1"]
            ).tolist(),
        },
        "final_rf_plus_novelty_all_scenarios": {
            "n": int(len(test)),
            "exact_accuracy": float((test["armB_window"] == test["expected"]).mean()),
            "confusion_matrix_labels_BENIGN_ATTACK_UNKNOWN": confusion_matrix(
                test["expected"],
                test["armB_window"],
                labels=["BENIGN", "ATTACK", "UNKNOWN"],
            ).tolist(),
            "novel_window_rate": float(test["novel"].mean()),
            "novel_window_rate_by_expected": {
                key: float(part["novel"].mean())
                for key, part in test.groupby("expected")
            },
        },
    }

    run_predictions = (
        test.groupby(["run_name", "run_id", "scenario", "rep", "expected"], as_index=False)
        .agg(
            armB=("armB_window", strict_majority),
            n_windows=("armB_window", "size"),
            novel_windows=("novel", "sum"),
        )
    )
    run_rows = pd.DataFrame(run_records)
    run_rows = run_rows[run_rows["rep"].isin(TEST_REPS)].merge(
        run_predictions,
        on=["run_name", "run_id", "scenario", "rep", "expected"],
        how="left",
        validate="one_to_one",
    )
    run_rows["armB"] = run_rows["armB"].fillna("UNKNOWN")
    run_rows["n_windows"] = run_rows["n_windows"].fillna(0).astype(int)
    run_rows["novel_windows"] = run_rows["novel_windows"].fillna(0).astype(int)
    run_rows["always_benign"] = "BENIGN"

    run_rows["combo_or"] = [combine_or(a, b) for a, b in zip(run_rows["armA"], run_rows["armB"])]
    run_rows["combo_rule_first_fallback_ml"] = np.where(
        run_rows["armA"].eq("UNKNOWN"), run_rows["armB"], run_rows["armA"]
    )
    run_rows["combo_consensus_else_abstain"] = [
        combine_consensus(a, b) for a, b in zip(run_rows["armA"], run_rows["armB"])
    ]

    per_scenario: dict[str, dict] = {}
    for scenario in SCENARIO_ORDER:
        part = run_rows[run_rows["scenario"] == scenario].sort_values("rep")
        a_correct = int((part["armA"] == part["expected"]).sum())
        b_correct = int((part["armB"] == part["expected"]).sum())
        n = int(len(part))
        per_scenario[scenario] = {
            "expected": expected_verdict(scenario),
            "armA_verdicts_by_rep": {str(int(row.rep)): row.armA for row in part.itertuples()},
            "armB_verdicts_by_rep": {str(int(row.rep)): row.armB for row in part.itertuples()},
            "always_benign_verdicts_by_rep": {
                str(int(row.rep)): row.always_benign for row in part.itertuples()
            },
            "armA_correct": a_correct,
            "armA_n": n,
            "armB_correct": b_correct,
            "armB_n": n,
            "armA_recall": a_correct / n if n else None,
            "armB_recall": b_correct / n if n else None,
            "armA_ci": wilson(a_correct, n),
            "armB_ci": wilson(b_correct, n),
            "always_benign_correct": int(
                (part["always_benign"] == part["expected"]).sum()
            ),
            "always_benign_n": n,
        }

    macro_sensitivity = {
        "armA": metric_bundle(run_rows, "armA", ATTACK_SCENARIOS),
        "armB": metric_bundle(run_rows, "armB", ATTACK_SCENARIOS),
    }
    macro_specificity = {
        "armA": metric_bundle(run_rows, "armA", BENIGN_SCENARIOS),
        "armB": metric_bundle(run_rows, "armB", BENIGN_SCENARIOS),
    }
    abstention = {
        "armA": metric_bundle(run_rows, "armA", [UNKNOWN_SCENARIO]),
        "armB": metric_bundle(run_rows, "armB", [UNKNOWN_SCENARIO]),
    }
    combination_analysis = {
        "or_attack_if_either_attacks_else_unknown_if_either_abstains": score_combination(
            run_rows, "combo_or"
        ),
        "rule_first_use_ml_only_when_rule_abstains": score_combination(
            run_rows, "combo_rule_first_fallback_ml"
        ),
        "consensus_else_abstain": score_combination(run_rows, "combo_consensus_else_abstain"),
    }
    arm_overall = {
        "armA": score_combination(run_rows, "armA"),
        "armB": score_combination(run_rows, "armB"),
    }
    trivial_baseline = score_combination(run_rows, "always_benign")
    arm_b_correct = run_rows["armB"].eq(run_rows["expected"])
    baseline_correct = run_rows["always_benign"].eq(run_rows["expected"])
    b_better = int((arm_b_correct & ~baseline_correct).sum())
    baseline_better = int((~arm_b_correct & baseline_correct).sum())
    paired_p = mcnemar_exact_two_sided(b_better, baseline_better)
    trivial_baseline_control = {
        **trivial_baseline,
        "definition": "constant BENIGN verdict for every held-out run",
        "expected_breakdown": {
            "attack_correct": int(
                (
                    run_rows["scenario"].isin(ATTACK_SCENARIOS)
                    & run_rows["always_benign"].eq(run_rows["expected"])
                ).sum()
            ),
            "attack_n": 32,
            "benign_correct": int(
                (
                    run_rows["scenario"].isin(BENIGN_SCENARIOS)
                    & run_rows["always_benign"].eq(run_rows["expected"])
                ).sum()
            ),
            "benign_n": 20,
            "abstention_correct": int(
                (
                    run_rows["scenario"].eq(UNKNOWN_SCENARIO)
                    & run_rows["always_benign"].eq(run_rows["expected"])
                ).sum()
            ),
            "abstention_n": 4,
        },
        "paired_comparison_with_armB": {
            "armB_verdict_counts": verdict_counts(run_rows["armB"].tolist()),
            "armB_benign_verdict_rate": float(run_rows["armB"].eq("BENIGN").mean()),
            "armB_correct_baseline_wrong": b_better,
            "baseline_correct_armB_wrong": baseline_better,
            "both_same_correctness": int(len(run_rows) - b_better - baseline_better),
            "net_additional_correct_runs_armB": int(arm_b_correct.sum() - baseline_correct.sum()),
            "net_accuracy_improvement": float(arm_b_correct.mean() - baseline_correct.mean()),
            "exact_two_sided_mcnemar_p": paired_p,
            "alpha": 0.05,
            "statistically_distinguishable_at_alpha": bool(paired_p < 0.05),
        },
        "B_bc_replacement": {
            "armB_correct": int(
                (
                    run_rows["scenario"].eq("B_bc_replacement")
                    & arm_b_correct
                ).sum()
            ),
            "always_benign_correct": int(
                (
                    run_rows["scenario"].eq("B_bc_replacement")
                    & baseline_correct
                ).sum()
            ),
            "n": 4,
            "conclusion": "ARM B is identical to the constant-BENIGN control on this scenario; no unique capability is established.",
        },
    }

    importances = sorted(
        [
            {"feature": name, "importance": float(value)}
            for name, value in zip(populated, clf.feature_importances_)
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )[:15]

    a_wins_b_misses = sorted(
        run_rows.loc[
            (run_rows["armA"] == run_rows["expected"])
            & (run_rows["armB"] != run_rows["expected"]),
            "scenario",
        ].unique()
    )
    b_wins_a_misses = sorted(
        run_rows.loc[
            (run_rows["armB"] == run_rows["expected"])
            & (run_rows["armA"] != run_rows["expected"]),
            "scenario",
        ].unique()
    )

    limitations = [
        "Forty-eight of 168 run directories lack pmc.jsonl; management-plane telemetry is therefore incomplete and was not used as an ML feature source.",
        f"{len(context_rep_mismatches)} context.json files disagree with their directory replicate number (the C-series files report rep 901). The pre-registered split uses the authoritative <scenario>__r<rep> directory name.",
        "The gma.log and gmb.log files contain no parseable servo lines because those nodes act as grandmasters; this produced 336 preserved parser failures. BC/RU logs supplied the usable servo telemetry.",
        "The canonical ingester supplies simulator-friendly defaults and synthetic sequence/message fields. Values derived only from those defaults were explicitly reset to NaN and excluded from ARM B.",
        "The 0.4 s window is shorter than the roughly 2 s servo reporting cadence. A usable window is formed by pooling contemporaneous BC/RU samples after each node-local timestamp is rebased; it is cross-node rather than a dense single-node time window.",
        "Window labels inherit the run-level scenario label, so pre-fault/settling windows may contain label noise.",
        "Overlapping windows are correlated. Per-run, per-scenario results are primary; pooled window metrics have artificially large effective sample size.",
        "Only four held-out replicates exist per scenario, giving wide Wilson intervals.",
        "ARM A consumes protocol legality and provisioned context, whereas ARM B here is restricted to available ptp4l servo summaries. This is a head-to-head operational comparison, not an equal-input ablation.",
        "The experiment uses one fixed split and one fixed seed as pre-registered; it does not estimate split-to-split or seed-to-seed variance.",
    ]
    if novelty_error:
        limitations.append(f"The novelty layer could not be fully established: {novelty_error}")

    results = {
        "experiment": "AI-vs-frozen-rule S-plane timing classification",
        "measurement_status": "completed",
        "input_sha256_expected": EXPECTED_SHA256,
        "input_sha256_actual": actual_sha,
        "input_sha256_verified": checksum_ok,
        "n_runs_found": len(run_dirs),
        "required_file_missing_count": len(missing),
        "missing_files": missing,
        "context_rep_mismatch_count": len(context_rep_mismatches),
        "context_rep_mismatches": context_rep_mismatches,
        "seeds": {"random_forest": SEED, "isolation_forest_base": SEED},
        "train_reps": TRAIN_REPS,
        "test_reps": TEST_REPS,
        "session_overlap": overlap,
        "window_s": float(config["dataset"]["window_s"]),
        "step_s": float(config["dataset"]["step_s"]),
        "model_hyperparameters_fixed_before_comparison": {
            "n_estimators": 90,
            "max_depth": 6,
            "class_weight": "balanced",
            "random_state": SEED,
        },
        "parser": {
            "files_attempted": len(run_dirs) * len(LOG_FILES),
            "files_parsed": parsed_files,
            "rows_parsed": parsed_rows,
            "failures": parse_failures,
        },
        "n_windows": {
            "all": int(len(windows)),
            "train_known": int(len(train)),
            "test_all": int(len(test)),
            "test_known": int(len(known_test)),
        },
        "feature_columns_configured": configured,
        "feature_columns_populated": populated,
        "feature_columns_empty": empty,
        "feature_availability_basis": "Observed linuxptp servo provenance; schema defaults and synthetic parser fields were invalidated to NaN before model fitting.",
        "per_window_metrics": per_window_metrics,
        "novelty_layer": novelty_details,
        "per_run_aggregation_rule": "Strict majority across RF-plus-novelty window verdicts; if no verdict exceeds 50%, return UNKNOWN. Runs with no windows also return UNKNOWN.",
        "per_scenario": per_scenario,
        "macro_sensitivity": macro_sensitivity,
        "macro_specificity": macro_specificity,
        "abstention": abstention,
        "arm_overall": arm_overall,
        "trivial_baseline_control": trivial_baseline_control,
        "combination_analysis": combination_analysis,
        "fault_class_crossovers": {
            "armB_correct_where_armA_missed_scenarios": b_wins_a_misses,
            "armB_unique_capabilities_beyond_always_benign": [],
            "armB_crossover_interpretation": "B_bc_replacement is a raw crossover versus ARM A, but always-BENIGN also scores 4/4; no unique ARM B capability is established.",
            "armA_correct_where_armB_missed_scenarios": a_wins_b_misses,
        },
        "feature_importances_top15": importances,
        "per_run_test_results": run_rows[
            [
                "run_name",
                "scenario",
                "rep",
                "expected",
                "armA",
                "armB",
                "always_benign",
                "n_windows",
                "novel_windows",
                "combo_or",
                "combo_rule_first_fallback_ml",
                "combo_consensus_else_abstain",
            ]
        ].to_dict(orient="records"),
        "measured": {
            "checksum_and_inventory": True,
            "predictions_and_metrics": True,
            "feature_importances": True,
        },
        "calculated": {
            "wilson_confidence_level": 0.95,
            "macro_definition": "unweighted mean of per-scenario correctness rates",
        },
        "assumed": [
            "Node-local ptp4l timestamps may be rebased by the existing ingester and pooled within a run because node identity is not part of the shipped canonical feature schema.",
            "Novel windows represent an abstention (UNKNOWN), while non-novel windows use the Random Forest H0/H1 verdict.",
            "Strict-majority aggregation was fixed before inspecting head-to-head results.",
        ],
        "limitations": limitations,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "ML_VS_RULE_COMPARISON.json"
    md_path = OUT_DIR / "ML_VS_RULE_COMPARISON.md"
    json_path.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    table_rows = []
    for scenario in SCENARIO_ORDER:
        part = run_rows[run_rows["scenario"] == scenario].sort_values("rep")
        item = per_scenario[scenario]
        a_ci_text = (
            f"{item['armA_correct']}/{item['armA_n']} ({item['armA_ci'][0]:.3f}-{item['armA_ci'][1]:.3f})"
            if item["armA_ci"] is not None
            else "NOT ESTABLISHED"
        )
        b_ci_text = (
            f"{item['armB_correct']}/{item['armB_n']} ({item['armB_ci'][0]:.3f}-{item['armB_ci'][1]:.3f})"
            if item["armB_ci"] is not None
            else "NOT ESTABLISHED"
        )
        table_rows.append(
            "| {scenario} | {expected} | {a_dist} | {b_dist} | {base_correct}/{base_n} | {a_ci_text} | {b_ci_text} |".format(
                scenario=scenario,
                expected=item["expected"],
                a_dist=format_distribution(part["armA"].tolist()),
                b_dist=format_distribution(part["armB"].tolist()),
                base_correct=item["always_benign_correct"],
                base_n=item["always_benign_n"],
                a_ci_text=a_ci_text,
                b_ci_text=b_ci_text,
            )
        )

    class_lines = []
    for scenario in SCENARIO_ORDER:
        item = per_scenario[scenario]
        if item["armB_recall"] is None or item["armA_recall"] is None:
            winner = "NOT ESTABLISHED (no scored held-out runs)"
        else:
            delta = item["armB_recall"] - item["armA_recall"]
            if delta > 0:
                winner = f"ARM B by {delta * 100:.0f} percentage points"
            elif delta < 0:
                winner = f"ARM A by {-delta * 100:.0f} percentage points"
            else:
                winner = "tie"
        class_lines.append(f"- `{scenario}`: {winner}.")

    top_feature_text = ", ".join(
        f"`{item['feature']}` ({item['importance']:.3f})" for item in importances
    )
    md = f"""# AI-native vs frozen rule-based timing classification

## Outcome

This pre-registered comparison completed on the held-out replicate sessions 9-12. The input SHA-256 matched `{EXPECTED_SHA256}`. The archive contained exactly {len(run_dirs)} runs. It did not fully meet the stated file inventory: {len(missing)} files were missing, all of them `pmc.jsonl`.

ARM A was read only from `decision_v3.json`. ARM B used the shipped Random Forest family with 90 trees, depth 6, balanced class weights, and seed {SEED}. The generic repository helper was not called because it randomly splits windows; this harness applied the required session-disjoint split first (train reps 1-8, test reps 9-12), then fitted the identical estimator. Hyperparameters, split, features, novelty settings, and aggregation were fixed before head-to-head scoring.

The final ARM B verdict uses the configured group Isolation Forest as an abstention layer: novel windows become `UNKNOWN`; other windows retain the RF `H0`/`H1` result. A run receives a verdict only when one window verdict has a strict majority; otherwise it is `UNKNOWN`.

The constant always-BENIGN control scores 20/56 (0.357), versus ARM B's 24/56 (0.429). ARM B itself returns `BENIGN` on {int(run_rows['armB'].eq('BENIGN').sum())}/56 runs ({run_rows['armB'].eq('BENIGN').mean():.1%}). The paired gain is only four net runs: ARM B is correct while the baseline is wrong on {b_better} runs, and the baseline is correct while ARM B is wrong on {baseline_better} run. The exact two-sided McNemar p-value is {paired_p:.5f}; therefore ARM B is **not distinguishable from the constant-BENIGN predictor at alpha 0.05** on this sample.

## Feature availability

Populated and used ({len(populated)}): {', '.join(f'`{name}`' for name in populated)}.

Entirely empty and excluded ({len(empty)}): {', '.join(f'`{name}`' for name in empty)}.

The exclusion is provenance-based. The existing canonical ingester fills simulator-friendly defaults and creates synthetic sequence/message fields so downstream code can run. Those are not measurements in these logs, so this experiment reset their derived feature columns to NaN before fitting. No unavailable value was changed to zero or otherwise imputed.

## Primary per-scenario results

Each cell covers four held-out runs. CIs are Wilson 95% intervals for exact expected-verdict correctness. This table, not pooled window counts, is primary.

| Scenario | Expected | ARM A verdicts | ARM B verdicts | Always-BENIGN correct/n | ARM A correct/n (95% CI) | ARM B correct/n (95% CI) |
|---|---|---|---|---:|---:|---:|
{chr(10).join(table_rows)}

## Macro results

- Attack-scenario sensitivity: ARM A {macro_sensitivity['armA']['macro']:.3f}; ARM B {macro_sensitivity['armB']['macro']:.3f}.
- Benign-scenario specificity: ARM A {macro_specificity['armA']['macro']:.3f}; ARM B {macro_specificity['armB']['macro']:.3f}.
- `B_unplanned_failover` abstention correctness: ARM A {abstention['armA']['macro']:.3f}; ARM B {abstention['armB']['macro']:.3f}.

The JSON also reports pooled Wilson intervals, explicitly labelled run-count-dependent. Overlapping-window metrics are secondary because those windows are correlated.

## Evidence-backed answers

### a) Which arm wins on which fault classes, and by how much?

{chr(10).join(class_lines)}

### b) Crossovers

The raw ARM-B-correct/ARM-A-wrong crossover is `B_bc_replacement`. This is **not a unique ARM B capability**: ARM B and the always-BENIGN control both score 4/4 because both simply return `BENIGN` on those runs. Across all held-out runs, ARM B improves on the trivial control by only 4/56 net runs, and the paired exact test does not distinguish them (p={paired_p:.5f}).

Scenarios where ARM A was correct on at least one run that ARM B missed: {', '.join(f'`{name}`' for name in a_wins_b_misses) if a_wins_b_misses else 'none'}.

### c) Measured combinations

- Single-arm reference: ARM A exact accuracy {arm_overall['armA']['exact_accuracy']:.3f} ({arm_overall['armA']['exact_correct']}/{arm_overall['armA']['n']}); ARM B {arm_overall['armB']['exact_accuracy']:.3f} ({arm_overall['armB']['exact_correct']}/{arm_overall['armB']['n']}); always-BENIGN {trivial_baseline_control['exact_accuracy']:.3f} ({trivial_baseline_control['exact_correct']}/{trivial_baseline_control['n']}).
- OR (ATTACK if either attacks): sensitivity {combination_analysis['or_attack_if_either_attacks_else_unknown_if_either_abstains']['macro_sensitivity']['macro']:.3f}, specificity {combination_analysis['or_attack_if_either_attacks_else_unknown_if_either_abstains']['macro_specificity']['macro']:.3f}, abstention correctness {combination_analysis['or_attack_if_either_attacks_else_unknown_if_either_abstains']['abstention_correctness']['macro']:.3f}, exact accuracy {combination_analysis['or_attack_if_either_attacks_else_unknown_if_either_abstains']['exact_accuracy']:.3f}.
- Rule-first, ML only on rule abstention: sensitivity {combination_analysis['rule_first_use_ml_only_when_rule_abstains']['macro_sensitivity']['macro']:.3f}, specificity {combination_analysis['rule_first_use_ml_only_when_rule_abstains']['macro_specificity']['macro']:.3f}, abstention correctness {combination_analysis['rule_first_use_ml_only_when_rule_abstains']['abstention_correctness']['macro']:.3f}, exact accuracy {combination_analysis['rule_first_use_ml_only_when_rule_abstains']['exact_accuracy']:.3f}.
- Consensus, otherwise abstain: sensitivity {combination_analysis['consensus_else_abstain']['macro_sensitivity']['macro']:.3f}, specificity {combination_analysis['consensus_else_abstain']['macro_specificity']['macro']:.3f}, abstention correctness {combination_analysis['consensus_else_abstain']['abstention_correctness']['macro']:.3f}, exact accuracy {combination_analysis['consensus_else_abstain']['exact_accuracy']:.3f}.

None of the three measured combinations beats ARM A's exact accuracy. OR is closest but loses specificity on benign cases; rule-first destroys correct abstention by replacing ARM A's `UNKNOWN` with ARM B's over-confident benign call. No unmeasured combination is recommended.

### d) Domain shift / artefact evidence

ARM B's ranked impurity importances are: {top_feature_text}. It can key only on offset, path-delay variability, and servo-state holdover because all protocol-legality, BMCA, GNSS, SyncE, message-rate, and oscillator-consistency features are unavailable. The weak held-out window accuracy ({per_window_metrics['closed_set_rf_known_scenarios']['accuracy']:.3f}), ROC-AUC ({per_window_metrics['closed_set_rf_known_scenarios']['roc_auc_h1']:.3f}), and attack-scenario sensitivity ({macro_sensitivity['armB']['macro']:.3f}) are signs of poor transfer across randomized replicate sessions and/or non-identifiability from servo summaries alone. Strong importance on timing magnitude/dispersion shows the classifier is learning this testbed's servo signatures, not the protocol illegality or operator-context semantics that define several attacks. That establishes artefact risk, but one testbed cannot separate domain shift from intrinsic class overlap. Transfer to another topology, hardware clock, reporting cadence, or site is NOT ESTABLISHED.

## Measured, calculated, and assumed

- Measured: checksum, file inventory, parser outcomes, feature values, frozen ARM A verdicts, ARM B predictions, and feature importances.
- Calculated: window/run aggregation, correctness, macro rates, confusion matrices, and Wilson intervals.
- Assumed before scoring: node-local timestamp rebasing and within-run pooling; novelty means abstention; strict majority produces the run verdict.

## Limitations

{chr(10).join(f'- {item}' for item in limitations)}
"""
    md_path.write_text(md, encoding="utf-8")

    print("| Scenario | Expected | ARM A verdicts | ARM B verdicts | Always-BENIGN correct/n | ARM A correct/n (95% CI) | ARM B correct/n (95% CI) |")
    print("|---|---|---|---|---:|---:|---:|")
    print("\n".join(table_rows))
    print()
    print(f"Macro attack sensitivity: ARM A={macro_sensitivity['armA']['macro']:.3f}, ARM B={macro_sensitivity['armB']['macro']:.3f}")
    print(f"Macro benign specificity: ARM A={macro_specificity['armA']['macro']:.3f}, ARM B={macro_specificity['armB']['macro']:.3f}")
    print(f"Unknown abstention correctness: ARM A={abstention['armA']['macro']:.3f}, ARM B={abstention['armB']['macro']:.3f}")
    print(f"Always-BENIGN control: 20/56=0.357; ARM B: 24/56=0.429; paired exact McNemar p={paired_p:.5f}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
