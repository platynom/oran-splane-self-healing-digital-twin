from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SimConfig:
    seed: int = 1588
    dt_s: float = 0.02
    duration_s: float = 8.0
    noise_ns: float = 8.0
    base_delay_ns: float = 50_000.0
    servo_gain: float = 0.26
    synce_gain: float = 0.08
    drift_ppb: float = 6.0
    time_error_budget_ns: float = 100.0


TelemetryMutator = Callable[[dict[str, float | int | str | bool], int, np.random.Generator], None]


def apply_action_config(config: SimConfig, action: str) -> SimConfig:
    if action.startswith("failover") or action == "isolate_rogue_master":
        return replace(config, noise_ns=max(3.0, config.noise_ns * 0.55), drift_ppb=2.0)
    if action == "holdover":
        return replace(config, servo_gain=0.0, synce_gain=0.0, drift_ppb=14.0)
    if action == "reroute_path":
        return replace(config, noise_ns=max(4.0, config.noise_ns * 0.75), base_delay_ns=config.base_delay_ns * 0.96)
    return config


def simulate(config: SimConfig, scenario: str = "healthy", mutator: TelemetryMutator | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(config.seed)
    n = int(config.duration_s / config.dt_s)
    offset_ns = 65.0
    freq_error_ppb = config.drift_ppb
    rows: list[dict[str, float | int | str | bool]] = []
    seq = 0
    ql = 1
    baseline_msg_rate_hz = 1.0 / config.dt_s

    for i in range(n):
        t = i * config.dt_s
        path_delay_ns = config.base_delay_ns + rng.normal(0, config.noise_ns)
        measured_offset = offset_ns + rng.normal(0, config.noise_ns)
        correction = config.servo_gain * measured_offset
        freq_correction = config.synce_gain * freq_error_ppb
        offset_ns = offset_ns + (freq_error_ppb * config.dt_s) - correction
        freq_error_ppb = freq_error_ppb - freq_correction + rng.normal(0, 0.04)

        row: dict[str, float | int | str | bool] = {
            "t_s": round(t, 6),
            "scenario": scenario,
            "offset_ns": float(offset_ns),
            "measured_offset_ns": float(measured_offset),
            "path_delay_ns": float(path_delay_ns),
            "pdv_ns": float(path_delay_ns - config.base_delay_ns),
            "freq_error_ppb": float(freq_error_ppb),
            "synce_ql": ql,
            "ptp_seq_id": seq,
            "ptp_msg_type": "Sync" if i % 2 == 0 else "Announce",
            "msg_rate_hz": float(max(0.0, baseline_msg_rate_hz + rng.normal(0, baseline_msg_rate_hz * 0.03))),
            "gnss_available": True,
            "holdover": False,
            "attack_flag": False,
            "fault_flag": False,
        }
        if mutator is not None:
            mutator(row, i, rng)
            offset_ns = float(row["offset_ns"])
            freq_error_ppb = float(row["freq_error_ppb"])
            ql = int(row["synce_ql"])
        rows.append(row)
        seq += 1
    return pd.DataFrame(rows)


def healthy_trace(config: SimConfig) -> pd.DataFrame:
    return simulate(config, "healthy")


def has_linuxptp() -> bool:
    """Best-effort optional realism probe. The prototype never depends on this."""
    import shutil

    return shutil.which("ptp4l") is not None
