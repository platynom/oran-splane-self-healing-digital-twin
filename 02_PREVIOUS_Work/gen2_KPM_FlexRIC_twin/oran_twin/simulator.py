from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path

from .config import Paths, load_json
from .profiles import ServiceProfile, load_profiles


@dataclass(frozen=True)
class SimulationConfig:
    duration: int = 240
    seed: int = 42
    users_per_service: int = 32


class OranKpiSimulator:
    """Synthetic O-RAN KPI generator for service-class-aware twin experiments."""

    def __init__(
        self,
        profiles: dict[str, ServiceProfile] | None = None,
        topology_path: Path | None = None,
        scenarios_path: Path | None = None,
        config: SimulationConfig | None = None,
    ) -> None:
        self.profiles = profiles or load_profiles()
        self.topology = load_json(topology_path or (Paths.configs / "topology.json"))
        self.scenarios = load_json(scenarios_path or (Paths.configs / "fault_scenarios.json"))["scenarios"]
        self.attack_scenarios = load_json(Paths.configs / "aml_attack_scenarios.json")["attacks"]
        self.config = config or SimulationConfig()
        self.rng = random.Random(self.config.seed)
        self.cells = self.topology["cells"]
        self.edge_nodes = {node["edge_node"]: node for node in self.topology["edge_nodes"]}

    def run(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for t in range(self.config.duration):
            for cell in self.cells:
                for service_name, profile in self.profiles.items():
                    active_faults = self._active_faults(t, cell)
                    active_attacks = self._active_attacks(t, cell)
                    rows.append(self._build_row(t, cell, service_name, profile, active_faults, active_attacks))
        return rows

    def write_csv(self, rows: list[dict[str, object]], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def _active_faults(self, t: int, cell: dict[str, object]) -> list[dict[str, object]]:
        active = []
        for fault in self.scenarios:
            if not (fault["start_t"] <= t <= fault["end_t"]):
                continue
            if fault.get("cell_id") == cell["cell_id"] or fault.get("edge_node") == cell["edge_node"]:
                active.append(fault)
        return active

    def _active_attacks(self, t: int, cell: dict[str, object]) -> list[dict[str, object]]:
        active = []
        for attack in self.attack_scenarios:
            if not (attack["start_t"] <= t <= attack["end_t"]):
                continue
            if attack.get("cell_id") == cell["cell_id"] or attack.get("edge_node") == cell["edge_node"]:
                active.append(attack)
        return active

    def _build_row(
        self,
        t: int,
        cell: dict[str, object],
        service_name: str,
        profile: ServiceProfile,
        active_faults: list[dict[str, object]],
        active_attacks: list[dict[str, object]],
    ) -> dict[str, object]:
        daily_wave = 0.5 + 0.5 * math.sin((t / 24.0) + self._service_phase(service_name))
        mobility_pressure = profile.mobility_level / 6
        density_pressure = profile.density_level / 6
        priority_relief = (7 - profile.priority_weight) / 7

        prb_util = 28 + 42 * daily_wave + 10 * density_pressure + self.rng.gauss(0, 3)
        latency = profile.latency_ms_target * (0.55 + 0.65 * daily_wave + 0.18 * priority_relief)
        jitter = profile.jitter_ms_target * (0.45 + 0.8 * daily_wave)
        throughput = profile.throughput_mbps_target * (1.1 - 0.34 * daily_wave)
        packet_loss = profile.packet_loss_pct_target * (0.35 + 0.9 * daily_wave)
        handover_fail = 0.08 + 0.7 * mobility_pressure * daily_wave
        edge_delay = profile.edge_dependency_level * (0.25 + 0.45 * daily_wave)
        backhaul_delay = 1.5 + 1.8 * daily_wave
        sinr = 24 - 7 * daily_wave - self.rng.random() * 2
        bler = 0.4 + 2.2 * daily_wave

        fault_types: list[str] = []
        for fault in active_faults:
            sev = float(fault["severity"])
            fault_type = str(fault["fault_type"])
            fault_types.append(fault_type)
            if fault_type == "cell_congestion":
                prb_util += 36 * sev
                latency += profile.latency_ms_target * 1.7 * sev
                jitter += profile.jitter_ms_target * 1.1 * sev
                throughput *= 1 - 0.38 * sev
                packet_loss += profile.packet_loss_pct_target * 1.4 * sev + 0.08 * sev
            elif fault_type == "backhaul_degradation":
                latency += 18 * sev
                jitter += 10 * sev
                packet_loss += 0.35 * sev
                backhaul_delay += 22 * sev
            elif fault_type == "edge_overload":
                edge_delay += 18 * sev * max(1, profile.edge_dependency_level / 3)
                latency += 10 * sev * max(1, profile.edge_dependency_level / 3)
                throughput *= 1 - 0.12 * sev
            elif fault_type == "handover_instability":
                handover_fail += 8 * sev * max(0.4, mobility_pressure)
                latency += 6 * sev * max(0.5, mobility_pressure)
                packet_loss += 0.18 * sev * max(0.5, mobility_pressure)
            elif fault_type == "timing_drift":
                jitter += 12 * sev
                latency += 3 * sev
                bler += 4 * sev
            elif fault_type == "spectrum_interference":
                sinr -= 14 * sev
                bler += 4.6 * sev
                prb_util += 18 * sev
                throughput *= 1 - 0.32 * sev
                latency += profile.latency_ms_target * 0.65 * sev
                packet_loss += profile.packet_loss_pct_target * 0.9 * sev

        attack_types: list[str] = []
        for attack in active_attacks:
            sev = float(attack["severity"])
            attack_type = str(attack["attack_type"])
            attack_types.append(attack_type)
            if attack_type == "telemetry_poisoning":
                latency += 50 * sev
                packet_loss += 3.5 * sev
                prb_util -= 35 * sev
                throughput *= 1 + 0.25 * sev
            elif attack_type == "model_evasion_attack":
                prb_util -= 28 * sev
                latency *= 1 - 0.35 * sev
                packet_loss *= 1 - 0.45 * sev
                throughput *= 1 + 0.18 * sev
            elif attack_type == "unsafe_xapp_action":
                prb_util += 22 * sev
                throughput *= 0.92

        latency += self.rng.gauss(0, max(0.2, profile.latency_ms_target * 0.06))
        jitter += self.rng.gauss(0, max(0.08, profile.jitter_ms_target * 0.08))
        throughput += self.rng.gauss(0, max(0.2, profile.throughput_mbps_target * 0.04))
        prb_util = max(0, min(100, prb_util))
        latency = max(0.1, latency)
        jitter = max(0.01, jitter)
        throughput = max(0.01, throughput)
        packet_loss = max(0.0, packet_loss)
        handover_fail = max(0.0, handover_fail)
        edge_delay = max(0.0, edge_delay)
        backhaul_delay = max(0.0, backhaul_delay)
        sinr = max(-5, sinr)
        bler = max(0.0, bler)

        return {
            "t": t,
            "cell_id": cell["cell_id"],
            "site": cell["site"],
            "lat": cell["lat"],
            "lon": cell["lon"],
            "edge_node": cell["edge_node"],
            "service_class": service_name,
            "fault_active": bool(fault_types),
            "fault_type": "+".join(fault_types) if fault_types else "normal",
            "aml_attack_active": bool(attack_types),
            "aml_attack_type": "+".join(attack_types) if attack_types else "none",
            "latency_ms": round(latency, 3),
            "jitter_ms": round(jitter, 3),
            "throughput_mbps": round(throughput, 3),
            "packet_loss_pct": round(packet_loss, 4),
            "prb_util_pct": round(prb_util, 3),
            "handover_fail_pct": round(handover_fail, 4),
            "edge_delay_ms": round(edge_delay, 3),
            "backhaul_delay_ms": round(backhaul_delay, 3),
            "sinr_db": round(sinr, 3),
            "bler_pct": round(bler, 3),
        }

    @staticmethod
    def _service_phase(service_name: str) -> float:
        return {
            "eMBB": 0.0,
            "mMTC": 1.1,
            "URLLC": 2.0,
            "FWA": 2.8,
            "V2X": 3.7,
        }.get(service_name, 0.0)
