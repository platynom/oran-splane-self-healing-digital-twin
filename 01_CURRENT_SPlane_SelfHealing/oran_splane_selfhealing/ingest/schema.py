from __future__ import annotations

"""Canonical S-plane telemetry schema shared by the simulator and all real-data
ingestion adapters. Keeping one schema is what lets the exact same downstream
pipeline (telemetry.features -> discriminator -> twin -> healing) run on both
synthetic and real inputs."""

import pandas as pd

# Columns telemetry.features.window_features consumes, plus bookkeeping.
TELEMETRY_COLUMNS = [
    "t_s",
    "scenario",
    "offset_ns",
    "measured_offset_ns",
    "path_delay_ns",
    "pdv_ns",
    "freq_error_ppb",
    "synce_ql",
    "ptp_seq_id",
    "ptp_msg_type",
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
    "synce_ql": 1,
    "ptp_msg_type": "Sync",
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
