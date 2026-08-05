from __future__ import annotations

"""Canonical S-plane telemetry schema shared by the simulator and all real-data
ingestion adapters. Keeping one schema is what lets the exact same downstream
pipeline (telemetry.features -> discriminator -> twin -> healing) run on both
synthetic and real inputs."""

import pandas as pd

GNSS_SYNC_STATUSES = (
    "SYNCHRONIZED",
    "ACQUIRING-SYNC",
    "HOLDOVER",
    "ANTENNA-DISCONNECTED",
    "ANTENNA-SHORT-CIRCUIT",
    "BOOTING",
)

# Columns telemetry.features.window_features consumes, plus bookkeeping.
TELEMETRY_COLUMNS = [
    "t_s",
    "scenario",
    "offset_ns",
    "measured_offset_ns",
    "path_delay_ns",
    "pdv_ns",
    "freq_error_ppb",
    "oscillator_holdover_nominal_ppb",
    "oscillator_holdover_tolerance_ppb",
    "oscillator_disciplined_tolerance_ppb",
    "synce_ql",
    "ptp_seq_id",
    "ptp_msg_type",
    "msg_rate_hz",
    "grandmaster_identity",
    "grandmaster_priority1",
    "grandmaster_clock_class",
    "grandmaster_clock_accuracy",
    "offset_scaled_log_variance",
    "grandmaster_priority2",
    "steps_removed",
    "time_source",
    "gnss_sync_status",
    "satellites_tracked",
    "gnss_available",
    "holdover",
    "attack_flag",
    "fault_flag",
    "run_id",
    "label",
]

_DEFAULTS = {
    "scenario": "live",
    "measured_offset_ns": None,   # filled from offset_ns if missing
    "freq_error_ppb": 0.0,
    "oscillator_holdover_nominal_ppb": 6.0,
    "oscillator_holdover_tolerance_ppb": 2.0,
    "oscillator_disciplined_tolerance_ppb": 1.5,
    "synce_ql": 1,
    "ptp_msg_type": "Sync",
    "msg_rate_hz": 0.0,
    "grandmaster_identity": "unknown",
    "grandmaster_priority1": 128,
    "grandmaster_clock_class": 248,
    "grandmaster_clock_accuracy": 0xFE,
    "offset_scaled_log_variance": 0xFFFF,
    "grandmaster_priority2": 128,
    "steps_removed": 0,
    "time_source": 0xA0,
    # PTP pcaps cannot supply O-RU receiver status; -1 marks count unavailable.
    "gnss_sync_status": "BOOTING",
    "satellites_tracked": -1,
    "gnss_available": True,
    "holdover": False,
    "attack_flag": False,
    "fault_flag": False,
    "run_id": 0,
    "label": "unlabeled",
}


def coerce_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """Fill defaults, derive missing columns, and order to the canonical schema.

    Real sources give us t_s, offset_ns, path_delay_ns and ptp_seq_id/msg_type;
    everything else is defaulted so the unchanged feature extractor accepts it.
    """
    out = df.copy()
    if "pdv_ns" not in out and "path_delay_ns" in out:
        out["pdv_ns"] = out["path_delay_ns"] - out["path_delay_ns"].median()
    for col, default in _DEFAULTS.items():
        if col not in out:
            out[col] = default
    if out["measured_offset_ns"].isna().all():
        out["measured_offset_ns"] = out["offset_ns"]
    # types
    out["ptp_seq_id"] = out["ptp_seq_id"].astype(int)
    out["synce_ql"] = out["synce_ql"].astype(int)
    for col in (
        "grandmaster_priority1",
        "grandmaster_clock_class",
        "grandmaster_clock_accuracy",
        "offset_scaled_log_variance",
        "grandmaster_priority2",
        "steps_removed",
        "time_source",
    ):
        out[col] = out[col].astype(int)
    out["grandmaster_identity"] = out["grandmaster_identity"].astype(str)
    out["gnss_sync_status"] = out["gnss_sync_status"].astype(str).str.upper()
    invalid_status = ~out["gnss_sync_status"].isin(GNSS_SYNC_STATUSES)
    if invalid_status.any():
        values = sorted(out.loc[invalid_status, "gnss_sync_status"].unique())
        raise ValueError(f"invalid gnss_sync_status values: {values}")
    out["satellites_tracked"] = out["satellites_tracked"].astype(int)
    out["gnss_available"] = out["gnss_available"].astype(bool)
    out["holdover"] = out["holdover"].astype(bool)
    out["attack_flag"] = out["attack_flag"].astype(bool)
    out["fault_flag"] = out["fault_flag"].astype(bool)
    missing = [c for c in TELEMETRY_COLUMNS if c not in out]
    if missing:
        raise ValueError(f"telemetry missing required columns after coercion: {missing}")
    return out[TELEMETRY_COLUMNS]


def validate_telemetry(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    if [c for c in TELEMETRY_COLUMNS if c not in df.columns]:
        return False
    if df[["t_s", "offset_ns", "path_delay_ns"]].isna().any().any():
        return False
    return bool((df["t_s"].diff().dropna() >= 0).all())  # monotonic time
