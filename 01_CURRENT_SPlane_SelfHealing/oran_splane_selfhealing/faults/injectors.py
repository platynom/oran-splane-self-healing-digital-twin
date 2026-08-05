from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from fronthaul_sim.simulator import SimConfig, simulate


H0_SCENARIOS = ("gnss_loss_holdover", "pdv_congestion", "synce_degrade", "traffic_burst", "planned_gm_failover")
H1_SCENARIOS = ("ptp_spoof", "ptp_replay", "ptp_dos_flood", "gnss_spoof", "gnss_jam")
ALL_SCENARIOS = ("healthy",) + H0_SCENARIOS + H1_SCENARIOS


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    label: str
    onset_s: float = 2.0
    duration_s: float = 3.0


def scenario_spec(name: str) -> ScenarioSpec:
    if name == "healthy":
        return ScenarioSpec(name, "healthy", 99.0, 0.0)
    if name in H0_SCENARIOS:
        return ScenarioSpec(name, "H0")
    if name in H1_SCENARIOS:
        return ScenarioSpec(name, "H1")
    if name == "gnss_spoof_stealth":
        return ScenarioSpec(name, "H1")
    raise ValueError(f"unknown scenario {name}")


def _add_sensor_noise(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Imperfect monitoring: telemetry values/flags are noisy, so the categorical
    fault signatures (SyncE QL, GNSS, holdover) are not perfectly observable. This
    blurs the fault-vs-attack boundary the way a real KPM stream does."""
    rng = np.random.default_rng(seed + 11)
    n = len(df)
    df["offset_ns"] = df["offset_ns"].to_numpy() + rng.normal(0, 6.0, n)
    pnoise = rng.normal(0, 12.0, n)
    df["path_delay_ns"] = df["path_delay_ns"].to_numpy() + pnoise
    df["pdv_ns"] = df["pdv_ns"].to_numpy() + pnoise
    m = rng.random(n) < 0.03
    if m.any():
        df.loc[m, "synce_ql"] = np.clip(df.loc[m, "synce_ql"].to_numpy() + rng.integers(-1, 2, int(m.sum())), 1, 4)
    m = rng.random(n) < 0.02
    if m.any():
        df.loc[m, "gnss_available"] = ~df.loc[m, "gnss_available"].astype(bool)
    m = rng.random(n) < 0.02
    if m.any():
        df.loc[m, "holdover"] = ~df.loc[m, "holdover"].astype(bool)
    return df


def run_scenario(config: SimConfig, scenario: str, run_id: int = 0) -> pd.DataFrame:
    spec = scenario_spec(scenario)
    seed = config.seed + run_id * 101 + len(scenario)
    cfg = SimConfig(**{**config.__dict__, "seed": seed})

    # Per-run nuisance variation so H0/H1 are NOT trivially separable:
    #  * a real spoof/replay looks like normal Sync/Announce (no label giveaway)
    #  * attack offset magnitudes OVERLAP fault magnitudes (stealthy attacks)
    #  * ~40% of attacks MIMIC a benign-fault signature (forge SyncE/GNSS/holdover)
    #  * ~40% of attacks occur during background congestion (adds path delay)
    #  * telemetry is read through sensor noise (see _add_sensor_noise)
    nz = np.random.default_rng(seed + 7)
    sev = float(nz.uniform(0.6, 1.5))
    onset = spec.onset_s + (float(nz.uniform(-0.6, 0.9)) if spec.duration_s > 0 else 0.0)
    mimic = str(nz.choice(["none", "none", "synce", "synce", "gnss"])) if spec.label == "H1" else "none"
    during_cong = bool(nz.random() < 0.55) if spec.label == "H1" else False
    baseline_rate = 1.0 / cfg.dt_s
    traffic_burst_factor = float(nz.uniform(5.0, 14.0))
    dos_flood_factor = float(nz.uniform(10.0, 35.0))

    def active(row: dict) -> bool:
        t = float(row["t_s"])
        return spec.duration_s > 0 and onset <= t <= onset + spec.duration_s

    def mutate(row: dict, i: int, rng: np.random.Generator) -> None:
        if not active(row):
            return
        row["fault_flag"] = spec.label == "H0"
        row["attack_flag"] = spec.label == "H1"
        row["attack_family"] = "none"
        elapsed = float(row["t_s"]) - onset
        if scenario == "gnss_loss_holdover":
            row["gnss_available"] = False
            row["holdover"] = True
            row["gnss_sync_status"] = "ACQUIRING-SYNC" if elapsed < 0.35 else "HOLDOVER"
            row["satellites_tracked"] = max(0, int(round(12 * max(0.0, 1.0 - elapsed / 0.35))))
            row["grandmaster_clock_class"] = 7
            row["time_source"] = 0xA0
            oscillator_drift = cfg.holdover_nominal_drift_ppb + (
                (sev - 1.0) * cfg.holdover_tolerance_ppb * 0.8
            )
            row["offset_ns"] = float(row["offset_ns"]) + oscillator_drift * cfg.dt_s + rng.normal(0, 0.7)
            row["freq_error_ppb"] = oscillator_drift + rng.normal(0, 0.35)
        elif scenario == "pdv_congestion":
            burst = rng.normal(70.0 * sev, 30.0)
            row["path_delay_ns"] = float(row["path_delay_ns"]) + burst
            row["pdv_ns"] = float(row["pdv_ns"]) + burst
            row["offset_ns"] = float(row["offset_ns"]) + rng.normal(18.0 * sev, 14.0)
            if rng.random() < 0.12:
                row["ptp_seq_id"] = int(row["ptp_seq_id"]) - int(rng.integers(1, 3))
        elif scenario == "synce_degrade":
            row["synce_ql"] = int(rng.choice([3, 4]))
            row["freq_error_ppb"] = float(row["freq_error_ppb"]) + 1.7 * sev
            row["offset_ns"] = float(row["offset_ns"]) + (11.0 * sev) * elapsed + rng.normal(0, 9.0)
        elif scenario == "traffic_burst":
            # Planned control-plane churn/failover can legitimately raise PTP traffic.
            # Its rate overlaps low-end floods but remains comparatively stable.
            row["msg_rate_hz"] = float(max(0.0, baseline_rate * traffic_burst_factor * rng.normal(1.0, 0.07)))
            row["path_delay_ns"] = float(row["path_delay_ns"]) + rng.normal(18.0, 10.0)
            row["pdv_ns"] = float(row["pdv_ns"]) + rng.normal(18.0, 10.0)
        elif scenario == "planned_gm_failover":
            row["grandmaster_identity"] = f"001b19fffe10{run_id:04x}"
            row["grandmaster_clock_class"] = 7
            row["grandmaster_clock_accuracy"] = 0x21
            row["grandmaster_priority1"] = 128
            row["grandmaster_priority2"] = 129
            row["steps_removed"] = 2
            row["time_source"] = 0x20
        elif scenario == "ptp_spoof":
            row["attack_family"] = "spoof"
            row["grandmaster_identity"] = f"deadbeeffe00{run_id:04x}"
            row["grandmaster_clock_class"] = 1
            row["grandmaster_clock_accuracy"] = 0x17
            row["grandmaster_priority1"] = 1
            row["grandmaster_priority2"] = 1
            row["steps_removed"] = 0
            row["time_source"] = 0x20
            step = rng.normal(48.0 * sev, 30.0) * (1.0 + 0.5 * min(elapsed, 1.5))
            row["offset_ns"] = float(row["offset_ns"]) + step
            row["measured_offset_ns"] = float(row["measured_offset_ns"]) + step
            row["freq_error_ppb"] = float(row["freq_error_ppb"]) + rng.normal(0.4, 0.5)
            if rng.random() < 0.06:
                row["ptp_msg_type"] = "Announce"
            if mimic == "synce":
                row["synce_ql"] = int(rng.choice([3, 4]))
            elif mimic == "gnss":
                row["gnss_available"] = False
                row["holdover"] = True
            if during_cong:
                b = rng.normal(55.0, 25.0)
                row["path_delay_ns"] = float(row["path_delay_ns"]) + b
                row["pdv_ns"] = float(row["pdv_ns"]) + b
        elif scenario == "ptp_replay":
            row["attack_family"] = "replay"
            if rng.random() < 0.35:
                row["ptp_seq_id"] = int(row["ptp_seq_id"]) - int(rng.integers(1, 4))
            row["offset_ns"] = float(row["offset_ns"]) + rng.normal(42.0 * sev, 26.0)
            row["freq_error_ppb"] = float(row["freq_error_ppb"]) + rng.normal(0.2, 0.5)
            if mimic == "synce":
                row["synce_ql"] = int(rng.choice([3, 4]))
            if during_cong:
                b = rng.normal(55.0, 25.0)
                row["path_delay_ns"] = float(row["path_delay_ns"]) + b
                row["pdv_ns"] = float(row["pdv_ns"]) + b
        elif scenario == "ptp_dos_flood":
            row["attack_family"] = "dos"
            # Flood intensity is intentionally bursty and overlaps the benign
            # traffic-burst range; timing itself is only mildly disturbed.
            rate_factor = dos_flood_factor * max(0.15, rng.normal(1.0, 0.32))
            if rng.random() < 0.10:
                rate_factor *= rng.uniform(1.4, 2.0)
            row["msg_rate_hz"] = float(baseline_rate * rate_factor)
            row["offset_ns"] = float(row["offset_ns"]) + rng.normal(0.2, 3.0)
            delay_burst = rng.normal(12.0, 8.0)
            row["path_delay_ns"] = float(row["path_delay_ns"]) + delay_burst
            row["pdv_ns"] = float(row["pdv_ns"]) + delay_burst
        elif scenario == "gnss_spoof":
            row["attack_family"] = "gnss_spoof"
            # Receiver health remains plausible even though delivered time is wrong.
            row["gnss_available"] = True
            row["holdover"] = False
            row["gnss_sync_status"] = "SYNCHRONIZED"
            row["satellites_tracked"] = int(np.clip(round(rng.normal(12, 1.0)), 8, 16))
            row["grandmaster_clock_class"] = 6
            row["time_source"] = 0x20
            malicious_drift = cfg.drift_ppb * sev * rng.uniform(1.35, 2.1)
            smooth_bias = 0.09 * sev * np.sin(elapsed * 2.2)
            row["offset_ns"] = float(row["offset_ns"]) + malicious_drift * cfg.dt_s + smooth_bias + rng.normal(0, 0.8)
            row["freq_error_ppb"] = malicious_drift + rng.normal(0, 0.45)
        elif scenario == "gnss_jam":
            row["attack_family"] = "gnss_jam"
            row["gnss_available"] = False
            row["holdover"] = True
            row["gnss_sync_status"] = "ACQUIRING-SYNC" if elapsed < 0.25 else "HOLDOVER"
            row["satellites_tracked"] = max(0, int(round(12 * max(0.0, 1.0 - elapsed / 0.25))))
            row["grandmaster_clock_class"] = 7
            row["time_source"] = 0xA0
            jam_drift = cfg.drift_ppb * sev * rng.uniform(1.5, 2.4)
            intermittent = rng.normal(0, 2.2) if rng.random() < 0.16 else rng.normal(0, 0.8)
            row["offset_ns"] = float(row["offset_ns"]) + jam_drift * cfg.dt_s + intermittent
            row["freq_error_ppb"] = jam_drift + rng.normal(0, 0.6)
        elif scenario == "gnss_spoof_stealth":
            row["attack_family"] = "gnss_spoof_stealth"
            row["gnss_available"] = True
            row["holdover"] = False
            row["gnss_sync_status"] = "SYNCHRONIZED"
            row["satellites_tracked"] = int(np.clip(round(rng.normal(12, 1.0)), 8, 16))
            row["grandmaster_clock_class"] = 6
            row["time_source"] = 0x20
            # Slow spoof remains within the rated holdover envelope by construction.
            stealth_drift = cfg.holdover_nominal_drift_ppb + rng.uniform(
                -0.7 * cfg.holdover_tolerance_ppb,
                0.7 * cfg.holdover_tolerance_ppb,
            )
            row["offset_ns"] = float(row["offset_ns"]) + stealth_drift * cfg.dt_s + rng.normal(0, 0.7)
            row["freq_error_ppb"] = stealth_drift + rng.normal(0, 0.25)

    df = simulate(cfg, scenario=scenario, mutator=mutate)
    df = _add_sensor_noise(df, seed)
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
