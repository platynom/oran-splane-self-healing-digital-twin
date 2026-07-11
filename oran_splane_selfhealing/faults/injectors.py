from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from fronthaul_sim.simulator import SimConfig, simulate


H0_SCENARIOS = ("gnss_loss_holdover", "pdv_congestion", "synce_degrade")
H1_SCENARIOS = ("ptp_spoof", "ptp_replay")
ALL_SCENARIOS = ("healthy",) + H0_SCENARIOS + H1_SCENARIOS


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    label: str
    onset_s: float = 2.0
    duration_s: float = 3.0


def _active(row: dict[str, float | int | str | bool], spec: ScenarioSpec) -> bool:
    t = float(row["t_s"])
    return spec.onset_s <= t <= spec.onset_s + spec.duration_s


def scenario_spec(name: str) -> ScenarioSpec:
    if name == "healthy":
        return ScenarioSpec(name, "healthy", 99.0, 0.0)
    if name in H0_SCENARIOS:
        return ScenarioSpec(name, "H0")
    if name in H1_SCENARIOS:
        return ScenarioSpec(name, "H1")
    raise ValueError(f"unknown scenario {name}")


def run_scenario(config: SimConfig, scenario: str, run_id: int = 0) -> pd.DataFrame:
    spec = scenario_spec(scenario)
    cfg = SimConfig(**{**config.__dict__, "seed": config.seed + run_id * 101 + len(scenario)})

    def mutate(row: dict[str, float | int | str | bool], i: int, rng: np.random.Generator) -> None:
        if not _active(row, spec):
            return
        row["fault_flag"] = spec.label == "H0"
        row["attack_flag"] = spec.label == "H1"
        elapsed = float(row["t_s"]) - spec.onset_s
        if scenario == "gnss_loss_holdover":
            row["gnss_available"] = False
            row["holdover"] = True
            row["offset_ns"] = float(row["offset_ns"]) + 22.0 * elapsed
            row["freq_error_ppb"] = float(row["freq_error_ppb"]) + 0.8
        elif scenario == "pdv_congestion":
            burst = rng.normal(80.0, 22.0)
            row["path_delay_ns"] = float(row["path_delay_ns"]) + burst
            row["pdv_ns"] = float(row["pdv_ns"]) + burst
            row["offset_ns"] = float(row["offset_ns"]) + rng.normal(15.0, 7.0)
        elif scenario == "synce_degrade":
            row["synce_ql"] = 4
            row["freq_error_ppb"] = float(row["freq_error_ppb"]) + 1.9
            row["offset_ns"] = float(row["offset_ns"]) + 12.0 * elapsed
        elif scenario == "ptp_spoof":
            step = 180.0 if elapsed < 0.8 else 260.0
            row["offset_ns"] = float(row["offset_ns"]) + step
            row["measured_offset_ns"] = float(row["measured_offset_ns"]) + step
            row["ptp_msg_type"] = "ForgedSync"
        elif scenario == "ptp_replay":
            if i % 4 == 0:
                row["ptp_seq_id"] = int(row["ptp_seq_id"]) - 3
            row["offset_ns"] = float(row["offset_ns"]) + 130.0 + rng.normal(0, 18.0)
            row["ptp_msg_type"] = "ReplaySync"

    df = simulate(cfg, scenario=scenario, mutator=mutate)
    df["run_id"] = run_id
    df["label"] = "healthy"
    df.loc[df["fault_flag"], "label"] = "H0"
    df.loc[df["attack_flag"], "label"] = "H1"
    return df


def generate_telemetry(config: SimConfig, scenarios_per_type: int) -> pd.DataFrame:
    frames = []
    for scenario in ALL_SCENARIOS:
        reps = scenarios_per_type if scenario != "healthy" else max(3, scenarios_per_type // 2)
        for run_id in range(reps):
            frames.append(run_scenario(config, scenario, run_id))
    return pd.concat(frames, ignore_index=True)
