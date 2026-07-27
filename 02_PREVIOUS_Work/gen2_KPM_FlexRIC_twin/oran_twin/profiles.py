from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from .config import Paths, load_json


@dataclass(frozen=True)
class ServiceProfile:
    name: str
    description: str
    latency_ms_target: float
    jitter_ms_target: float
    throughput_mbps_target: float
    packet_loss_pct_target: float
    availability_pct_target: float
    reliability_pct_target: float
    mobility_level: int
    density_level: int
    edge_dependency_level: int
    security_level: int
    priority_weight: int
    ai_optimization_weight: str

    def target_vector(self) -> dict[str, float | int | str]:
        return {
            "latency_ms_target": self.latency_ms_target,
            "jitter_ms_target": self.jitter_ms_target,
            "throughput_mbps_target": self.throughput_mbps_target,
            "packet_loss_pct_target": self.packet_loss_pct_target,
            "availability_pct_target": self.availability_pct_target,
            "reliability_pct_target": self.reliability_pct_target,
            "mobility_level": self.mobility_level,
            "density_level": self.density_level,
            "edge_dependency_level": self.edge_dependency_level,
            "security_level": self.security_level,
            "priority_weight": self.priority_weight,
            "ai_optimization_weight": self.ai_optimization_weight,
        }


def load_profiles(path: Path | None = None) -> dict[str, ServiceProfile]:
    raw = load_json(path or (Paths.configs / "service_profiles.json"))
    allowed = {field.name for field in fields(ServiceProfile)}
    allowed.remove("name")
    return {
        name: ServiceProfile(name=name, **{key: value for key, value in values.items() if key in allowed})
        for name, values in raw.items()
    }
