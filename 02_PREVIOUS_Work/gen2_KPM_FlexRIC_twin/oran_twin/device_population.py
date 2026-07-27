from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Paths


@dataclass(frozen=True)
class DevicePopulation:
    total_devices: int
    active_devices: int
    affected_devices: int
    representative_ues: list[dict[str, object]]
    by_service: dict[str, dict[str, object]]


class DevicePopulationModel:
    """Aggregates lakhs of virtual devices and exposes a small UE sample."""

    def __init__(self, config_path: Path | None = None) -> None:
        path = config_path or Paths.configs / "device_population_profiles.json"
        self.config = json.loads(path.read_text(encoding="utf-8"))
        self.services: dict[str, dict[str, object]] = self.config["services"]
        self.city_scale = float(self.config.get("city_scale_multiplier", 1.0))

    def assess(
        self,
        *,
        cells: list[dict[str, Any]],
        selected_cell_id: str,
        active_service: str,
        risk_by_cell: dict[str, float],
        fault_type: str,
        severity: float,
        network_load: float,
        mobility: float,
    ) -> DevicePopulation:
        by_service: dict[str, dict[str, object]] = {}
        total_devices = 0
        active_devices = 0
        affected_devices = 0

        for service, profile in self.services.items():
            service_total = 0
            service_active = 0
            service_affected = 0
            for cell in cells:
                cell_id = str(cell["id"])
                base = int(float(profile["base_devices_per_cell"]) * self.city_scale)
                load_factor = 0.72 + float(cell.get("baseLoad", 0.5)) * 0.36 + network_load * 0.28
                selected_factor = 1.12 if cell_id == selected_cell_id else 1.0
                service_factor = 1.15 if service == active_service else 0.92
                count = int(base * load_factor * selected_factor * service_factor)
                active = int(count * float(profile["active_ratio"]) * (0.78 + network_load * 0.44))
                risk = float(risk_by_cell.get(cell_id, 0.0))
                affected_ratio = min(0.95, max(0.0, risk * 0.62 + (severity * 0.22 if cell_id == selected_cell_id else 0.0)))
                affected = int(active * affected_ratio)
                service_total += count
                service_active += active
                service_affected += affected

            by_service[service] = {
                "label": profile["label"],
                "deviceType": profile["device_type"],
                "totalDevices": service_total,
                "activeDevices": service_active,
                "affectedDevices": service_affected,
                "activeRatio": round(service_active / max(1, service_total), 4),
            }
            total_devices += service_total
            active_devices += service_active
            affected_devices += service_affected

        return DevicePopulation(
            total_devices=total_devices,
            active_devices=active_devices,
            affected_devices=affected_devices,
            representative_ues=self._representative_ues(
                selected_cell_id=selected_cell_id,
                active_service=active_service,
                fault_type=fault_type,
                severity=severity,
                mobility=mobility,
                risk=float(risk_by_cell.get(selected_cell_id, 0.0)),
            ),
            by_service=by_service,
        )

    def _representative_ues(
        self,
        *,
        selected_cell_id: str,
        active_service: str,
        fault_type: str,
        severity: float,
        mobility: float,
        risk: float,
    ) -> list[dict[str, object]]:
        samples: list[dict[str, object]] = []
        services = [active_service] + [service for service in self.services if service != active_service]
        for index, service in enumerate(services[:8], start=1):
            profile = self.services[service]
            seed = f"{selected_cell_id}:{service}:{fault_type}:{index}"
            digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
            radio_offset = int(digest[:2], 16) / 255
            ue_risk = min(1.0, max(0.0, risk * (0.78 + radio_offset * 0.32) + (0.08 if service == active_service else 0.0)))
            samples.append(
                {
                    "ueId": f"UE-{selected_cell_id}-{service}-{index:03d}",
                    "service": service,
                    "deviceType": profile["device_type"],
                    "cellId": selected_cell_id,
                    "state": self._ue_state(ue_risk),
                    "risk": round(ue_risk, 4),
                    "mobility": round(min(1.0, mobility * float(profile["mobility_bias"]) + radio_offset * 0.18), 4),
                    "faultExposure": fault_type if service == active_service and fault_type != "normal" else "background_load",
                }
            )
        return samples

    @staticmethod
    def _ue_state(risk: float) -> str:
        if risk >= 0.68:
            return "impacted"
        if risk >= 0.42:
            return "degraded"
        return "nominal"
