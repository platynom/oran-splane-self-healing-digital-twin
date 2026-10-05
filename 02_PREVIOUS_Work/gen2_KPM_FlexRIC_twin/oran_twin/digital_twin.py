from __future__ import annotations

from dataclasses import dataclass

from .profiles import ServiceProfile


@dataclass(frozen=True)
class TwinAssessment:
    sla_violation: bool
    risk_score: float
    reasons: list[str]


class DigitalTwin:
    """Service-class-aware state evaluator for simulated O-RAN KPI rows."""

    def __init__(self, profiles: dict[str, ServiceProfile]) -> None:
        self.profiles = profiles

    def assess(self, row: dict[str, object]) -> TwinAssessment:
        profile = self.profiles[str(row["service_class"])]
        reasons: list[str] = []
        score = 0.0
        service = profile.name
        latency_weight = 0.29 if service in {"URLLC", "V2X"} else 0.2
        jitter_weight = 0.22 if service in {"URLLC", "V2X"} else 0.13
        loss_weight = 0.22 if service in {"URLLC", "V2X"} else 0.14
        throughput_weight = 0.2 if service in {"eMBB", "FWA"} else 0.08
        handover_weight = 0.16 if service == "V2X" else 0.08
        edge_weight = 0.16 if service in {"URLLC", "V2X"} else 0.08
        latency_tolerance = 1.15 if service in {"URLLC", "V2X"} else 1.35
        jitter_tolerance = 1.15 if service in {"URLLC", "V2X"} else 1.4
        throughput_floor = 0.74 if service in {"eMBB", "FWA"} else 0.45

        checks = [
            ("latency", float(row["latency_ms"]), profile.latency_ms_target * latency_tolerance, latency_weight, True),
            ("jitter", float(row["jitter_ms"]), profile.jitter_ms_target * jitter_tolerance, jitter_weight, True),
            ("packet_loss", float(row["packet_loss_pct"]), profile.packet_loss_pct_target * 1.5, loss_weight, True),
            ("throughput", float(row["throughput_mbps"]), profile.throughput_mbps_target * throughput_floor, throughput_weight, False),
            ("handover", float(row["handover_fail_pct"]), max(0.8, 4.5 / max(1, profile.mobility_level)), handover_weight, True),
            ("edge_delay", float(row["edge_delay_ms"]), max(2.0, profile.edge_dependency_level * 1.9), edge_weight, True),
        ]

        for name, actual, target, weight, higher_is_bad in checks:
            if higher_is_bad:
                ratio = actual / max(target, 0.001)
                if ratio > 1.0:
                    reasons.append(f"{name}_above_target")
                    score += weight * min(3.0, ratio)
                else:
                    score += weight * ratio * 0.35
            else:
                ratio = target / max(actual, 0.001)
                if actual < target:
                    reasons.append(f"{name}_below_target")
                    score += weight * min(3.0, ratio)
                else:
                    score += weight * 0.25

        priority_boost = 1 + (profile.priority_weight - 3) * 0.08
        risk_score = min(1.0, (score / 2.45) * priority_boost)
        return TwinAssessment(
            sla_violation=risk_score >= 0.68 or len(reasons) >= 3,
            risk_score=round(risk_score, 4),
            reasons=reasons,
        )
