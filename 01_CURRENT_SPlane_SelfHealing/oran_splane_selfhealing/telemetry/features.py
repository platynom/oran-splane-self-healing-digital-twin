from __future__ import annotations

import numpy as np
import pandas as pd


TIMESOURCE_FEATURE_COLUMNS = [
    "gnss_loss_rate",
    "holdover_rate",
    "gnss_status_changes",
    "antenna_fault_rate",
    "satellites_drop_max",
    "satellites_mean",
    "holdover_entry_count",
]

CONSISTENCY_FEATURE_COLUMNS = [
    "drift_vs_declared_state_residual",
    "holdover_spec_violation_rate",
    "status_behaviour_disagreement",
    "offset_step_vs_drift_ratio",
]


FEATURE_COLUMNS = [
    "offset_mean",
    "offset_std",
    "offset_abs_max",
    "path_delay_mean",
    "pdv_std",
    "seq_regressions",
    "msg_irregularity",
    "synce_ql_max",
    *TIMESOURCE_FEATURE_COLUMNS[:2],
    "msg_rate_mean",
    "msg_rate_std",
    "gm_identity_changes",
    "gm_identity_churn",
    "clock_class_changes",
    "clock_class_improve_jump",
    "priority1_changes",
    "steps_removed_changes",
    "steps_removed_min",
    *TIMESOURCE_FEATURE_COLUMNS[2:],
    *CONSISTENCY_FEATURE_COLUMNS,
]


def _transition_count(series: pd.Series) -> int:
    return int(series.astype(str).ne(series.astype(str).shift()).iloc[1:].sum())


def _largest_quality_improvement(clock_class: pd.Series, accuracy: pd.Series) -> float:
    class_improvement = -clock_class.astype(float).diff()
    accuracy_improvement = -accuracy.astype(float).diff()
    return float(max(0.0, class_improvement.max(skipna=True), accuracy_improvement.max(skipna=True)))


def _satellite_drop_max(series: pd.Series) -> float:
    valid = series.astype(float)
    valid = valid[valid >= 0]
    if len(valid) < 2:
        return 0.0
    return float(max(0.0, (-valid.diff()).max(skipna=True)))


def _consistency_features(window: pd.DataFrame) -> dict[str, float]:
    """Compare observed clock behavior with the configured oscillator envelope."""
    freq = window["freq_error_ppb"].astype(float).abs()
    holdover = window["gnss_sync_status"].eq("HOLDOVER") | window["holdover"].astype(bool)
    nominal = window["oscillator_holdover_nominal_ppb"].astype(float)
    hold_tolerance = window["oscillator_holdover_tolerance_ppb"].astype(float).clip(lower=1e-6)
    disciplined_tolerance = window["oscillator_disciplined_tolerance_ppb"].astype(float).clip(lower=1e-6)
    expected = nominal.where(holdover, 0.0)
    tolerance = hold_tolerance.where(holdover, disciplined_tolerance)
    normalized_residual = (freq - expected).abs() / tolerance
    envelope_exceeded = holdover & ((freq - nominal).abs() > hold_tolerance)
    healthy_declared = window["gnss_sync_status"].eq("SYNCHRONIZED") & ~window["holdover"].astype(bool)
    declared_fault = holdover | window["gnss_sync_status"].isin(
        ["ACQUIRING-SYNC", "ANTENNA-DISCONNECTED", "ANTENNA-SHORT-CIRCUIT"]
    )
    free_run_behavior = freq > disciplined_tolerance
    disagreement = (healthy_declared & free_run_behavior) | (declared_fault & ~free_run_behavior)

    dt = window["t_s"].astype(float).diff()
    offset_step = window["offset_ns"].astype(float).diff().abs()
    expected_wander = freq.shift().fillna(freq.iloc[0]) * dt.fillna(0.0)
    excess_step = (offset_step - expected_wander).clip(lower=0.0)
    ratio = excess_step.max(skipna=True) / max(float(expected_wander.abs().median()), 0.1)
    return {
        "drift_vs_declared_state_residual": float(normalized_residual.mean()),
        "holdover_spec_violation_rate": float(envelope_exceeded.mean()),
        "status_behaviour_disagreement": float(disagreement.mean()),
        "offset_step_vs_drift_ratio": float(ratio),
    }


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
            features = {
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
                    "gnss_status_changes": _transition_count(w["gnss_sync_status"]),
                    "antenna_fault_rate": float(
                        w["gnss_sync_status"].isin(
                            ["ANTENNA-DISCONNECTED", "ANTENNA-SHORT-CIRCUIT"]
                        ).mean()
                    ),
                    "satellites_drop_max": _satellite_drop_max(w["satellites_tracked"]),
                    "satellites_mean": float(
                        w.loc[w["satellites_tracked"] >= 0, "satellites_tracked"].mean()
                        if (w["satellites_tracked"] >= 0).any() else -1.0
                    ),
                    "holdover_entry_count": int(
                        (
                            w["gnss_sync_status"].eq("HOLDOVER")
                            & ~w["gnss_sync_status"].shift(fill_value="BOOTING").eq("HOLDOVER")
                        ).sum()
                    ),
            }
            features.update(_consistency_features(w))
            rows.append(features)
            t += step_s
    return pd.DataFrame(rows)


def label_integrity(windows: pd.DataFrame) -> bool:
    expected = {"healthy", "H0", "H1"}
    return not windows.empty and set(windows["label"]).issubset(expected) and windows[FEATURE_COLUMNS].notna().all().all()
