from __future__ import annotations

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "offset_mean",
    "offset_std",
    "offset_abs_max",
    "path_delay_mean",
    "pdv_std",
    "seq_regressions",
    "msg_irregularity",
    "synce_ql_max",
    "gnss_loss_rate",
    "holdover_rate",
    "msg_rate_mean",
    "msg_rate_std",
    "gm_identity_changes",
    "gm_identity_churn",
    "clock_class_changes",
    "clock_class_improve_jump",
    "priority1_changes",
    "steps_removed_changes",
    "steps_removed_min",
]


def _transition_count(series: pd.Series) -> int:
    return int(series.astype(str).ne(series.astype(str).shift()).iloc[1:].sum())


def _largest_quality_improvement(clock_class: pd.Series, accuracy: pd.Series) -> float:
    class_improvement = -clock_class.astype(float).diff()
    accuracy_improvement = -accuracy.astype(float).diff()
    return float(max(0.0, class_improvement.max(skipna=True), accuracy_improvement.max(skipna=True)))


def window_features(df: pd.DataFrame, window_s: float, step_s: float) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for (scenario, run_id), g in df.groupby(["scenario", "run_id"]):
        start = float(g["t_s"].min())
        end = float(g["t_s"].max())
        t = start
        while t + window_s <= end + 1e-9:
            w = g[(g["t_s"] >= t) & (g["t_s"] < t + window_s)]
            if len(w) < 3:
                t += step_s
                continue
            labels = w["label"].value_counts()
            label = labels.index[0]
            seq_diff = w["ptp_seq_id"].diff().fillna(1)
            msg_regular = w["ptp_msg_type"].isin(["Sync", "Announce"])
            rows.append(
                {
                    "scenario": scenario,
                    "run_id": int(run_id),
                    "window_start_s": round(t, 6),
                    "window_end_s": round(t + window_s, 6),
                    "label": label,
                    "is_anomalous": int(label != "healthy"),
                    "offset_mean": float(w["offset_ns"].mean()),
                    "offset_std": float(w["offset_ns"].std(ddof=0)),
                    "offset_abs_max": float(w["offset_ns"].abs().max()),
                    "path_delay_mean": float(w["path_delay_ns"].mean()),
                    "pdv_std": float(w["pdv_ns"].std(ddof=0)),
                    "seq_regressions": int((seq_diff < 0).sum()),
                    "msg_irregularity": float(1.0 - msg_regular.mean()),
                    "synce_ql_max": int(w["synce_ql"].max()),
                    "gnss_loss_rate": float((~w["gnss_available"].astype(bool)).mean()),
                    "holdover_rate": float(w["holdover"].astype(bool).mean()),
                    "msg_rate_mean": float(w["msg_rate_hz"].mean()),
                    "msg_rate_std": float(w["msg_rate_hz"].std(ddof=0)),
                    "gm_identity_changes": _transition_count(w["grandmaster_identity"]),
                    "gm_identity_churn": int(w["grandmaster_identity"].astype(str).nunique()),
                    "clock_class_changes": _transition_count(w["grandmaster_clock_class"]),
                    "clock_class_improve_jump": _largest_quality_improvement(
                        w["grandmaster_clock_class"], w["grandmaster_clock_accuracy"]
                    ),
                    "priority1_changes": _transition_count(w["grandmaster_priority1"]),
                    "steps_removed_changes": _transition_count(w["steps_removed"]),
                    "steps_removed_min": int(w["steps_removed"].min()),
                }
            )
            t += step_s
    return pd.DataFrame(rows)


def label_integrity(windows: pd.DataFrame) -> bool:
    expected = {"healthy", "H0", "H1"}
    return not windows.empty and set(windows["label"]).issubset(expected) and windows[FEATURE_COLUMNS].notna().all().all()
