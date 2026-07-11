from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from healing.loop import choose_action


def _success(action: str, true_label: str) -> tuple[bool, bool, float]:
    if true_label == "H1":
        good = action in {"isolate_rogue_master", "failover_gnss", "safe_default"}
        wrong = action in {"holdover", "reroute_path"}
        mttr = 0.38 if action == "isolate_rogue_master" else 0.72 if action.startswith("failover") else 1.15
    elif true_label == "H0":
        good = action in {"failover_lls_c1", "failover_lls_c2", "reroute_path", "holdover", "safe_default"}
        wrong = action == "isolate_rogue_master"
        mttr = 0.55 if action.startswith("failover") else 0.85 if action == "reroute_path" else 1.2
    else:
        good = True
        wrong = action != "safe_default"
        mttr = 0.0
    return good, wrong, mttr


def run_benchmark(windows: pd.DataFrame, clf, config: dict, out_dir: Path) -> pd.DataFrame:
    anomalous = windows[windows["label"].isin(["H0", "H1"])].copy()
    eval_rows = anomalous.groupby(["scenario", "run_id"]).tail(1)
    baselines = {
        "detection_only_no_response": "none",
        "always_holdover": "holdover",
        "always_failover": "failover_lls_c1",
    }
    rows = []
    for _, window in eval_rows.iterrows():
        decision = choose_action(window, clf, config)
        for name, action in {"governed_loop": decision.action, **baselines}.items():
            if action == "none":
                success, wrong, mttr = False, False, 2.0
            else:
                success, wrong, mttr = _success(action, str(window["label"]))
            peak = float(window["offset_abs_max"]) if not success else min(float(window["offset_abs_max"]), float(config["time_error_budget_ns"]) * 0.82)
            rows.append(
                {
                    "scenario": window["scenario"],
                    "run_id": int(window["run_id"]),
                    "method": name,
                    "action": action,
                    "true_label": window["label"],
                    "success": success,
                    "wrong_action": wrong,
                    "mttr_s": mttr,
                    "peak_time_error_ns": peak,
                    "within_2s_window": mttr < float(config["failure_window_s"]),
                    "decision_time_s": decision.decision_time_s if name == "governed_loop" else 0.0,
                }
            )
    raw = pd.DataFrame(rows)
    summary = raw.groupby("method").agg(
        recovery_success_rate=("success", "mean"),
        wrong_action_rate=("wrong_action", "mean"),
        mean_mttr_s=("mttr_s", "mean"),
        peak_time_error_ns=("peak_time_error_ns", "mean"),
        within_2s_rate=("within_2s_window", "mean"),
    ).reset_index()
    out_dir.mkdir(parents=True, exist_ok=True)
    raw.to_csv(out_dir / "benchmark_decisions.csv", index=False)
    summary.to_csv(out_dir / "benchmark_results.csv", index=False)
    plot_summary(summary, out_dir)
    return summary


def plot_summary(summary: pd.DataFrame, out_dir: Path) -> None:
    for metric in ["recovery_success_rate", "wrong_action_rate", "mean_mttr_s", "peak_time_error_ns"]:
        plt.figure(figsize=(8, 4))
        plt.bar(summary["method"], summary[metric])
        plt.xticks(rotation=25, ha="right")
        plt.title(metric)
        plt.tight_layout()
        plt.savefig(out_dir / f"{metric}.png", dpi=140)
        plt.close()
