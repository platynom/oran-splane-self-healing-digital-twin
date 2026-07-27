from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityAssessment:
    ai_trust_score: float
    aml_threat_level: str
    aml_threat_type: str
    guard_action: str
    automation_allowed: bool
    reasons: list[str]


class AdversarialMlGuard:
    """AML-aware trust gate for O-RAN telemetry, AI inference, and healing actions."""

    def assess(
        self,
        *,
        row: dict[str, object],
        risk_score: float,
        anomaly_score: float,
        root_cause: str,
        healing_action: str,
        twin_reasons: list[str] | None = None,
        anomaly_reasons: list[str] | None = None,
        ai_confidence: float | None = None,
    ) -> SecurityAssessment:
        reasons = list(twin_reasons or []) + list(anomaly_reasons or [])
        threat_points = 0.0
        threat_type = "none"
        injected_attack = str(row.get("aml_attack_type", "none"))

        service = str(row.get("service_class", row.get("service", "")))
        priority = self._priority_from_service(service)
        prb = self._float(row, "prb_util_pct", "prb")
        latency = self._float(row, "latency_ms", "latency")
        jitter = self._float(row, "jitter_ms", "jitter")
        loss = self._float(row, "packet_loss_pct", "loss")
        throughput = self._float(row, "throughput_mbps", "throughput")
        handover = self._float(row, "handover_fail_pct", "handover")
        edge_delay = self._float(row, "edge_delay_ms", "edgeDelay")
        backhaul = self._float(row, "backhaul_delay_ms", "backhaul")
        bler = self._float(row, "bler_pct", "bler")

        impossible_kpis = [
            latency < 0,
            jitter < 0,
            loss < 0 or loss > 100,
            prb < 0 or prb > 100,
            throughput < 0,
            handover < 0 or handover > 100,
        ]
        if any(impossible_kpis):
            threat_points += 0.55
            threat_type = "telemetry_integrity_attack"
            reasons.append("impossible_kpi_range")

        if injected_attack == "telemetry_poisoning":
            threat_points += 0.55
            threat_type = "telemetry_integrity_attack"
            reasons.append("injected_telemetry_poisoning")
        elif injected_attack == "model_evasion_attack":
            threat_points += 0.42
            threat_type = "model_evasion_or_blind_spot"
            reasons.append("injected_model_evasion_attack")
        elif injected_attack == "unsafe_xapp_action":
            threat_points += 0.36
            threat_type = "unsafe_healing_trigger"
            reasons.append("injected_unsafe_xapp_action")
        elif injected_attack != "none":
            threat_points += 0.3
            threat_type = "aml_attack_unknown_variant"
            reasons.append(f"injected_{injected_attack}")

        if anomaly_score >= 0.55 and risk_score < 0.25:
            threat_points += 0.26
            threat_type = "model_evasion_or_blind_spot"
            reasons.append("anomaly_high_but_twin_risk_low")

        if risk_score >= 0.68 and anomaly_score < 0.15:
            threat_points += 0.22
            threat_type = "baseline_poisoning_or_model_drift"
            reasons.append("twin_risk_high_but_detector_quiet")

        if root_cause == "cell_congestion" and prb < 62 and loss < 0.6:
            threat_points += 0.24
            threat_type = "false_congestion_trigger"
            reasons.append("congestion_rca_without_prb_or_loss_support")

        if root_cause == "backhaul_degradation" and backhaul < 8 and latency < 30:
            threat_points += 0.22
            threat_type = "rca_consistency_attack"
            reasons.append("backhaul_rca_without_delay_support")

        if root_cause == "edge_overload" and edge_delay < 7:
            threat_points += 0.22
            threat_type = "rca_consistency_attack"
            reasons.append("edge_rca_without_edge_delay_support")

        if root_cause == "timing_drift" and not (jitter > 7 and bler > 2.5):
            threat_points += 0.2
            threat_type = "rca_consistency_attack"
            reasons.append("timing_rca_without_jitter_bler_support")

        if healing_action not in {"no_action", "human_review_guarded_mode"} and risk_score < 0.28:
            threat_points += 0.26
            threat_type = "unsafe_healing_trigger"
            reasons.append("healing_requested_for_low_risk_state")

        if priority >= 5 and healing_action in {"prioritize_slice_and_traffic_steer", "failover_to_neighbor_cell"}:
            threat_points += 0.08
            reasons.append("critical_slice_control_action")

        if ai_confidence is not None and ai_confidence < 0.55 and healing_action != "no_action":
            threat_points += 0.18
            threat_type = "low_confidence_ai_action"
            reasons.append("healing_requested_with_low_ai_confidence")

        if throughput > 0 and latency > 80 and loss > 3 and prb < 35:
            threat_points += 0.18
            threat_type = "telemetry_consistency_attack"
            reasons.append("severe_qos_drop_without_resource_pressure")

        threat_points = min(1.0, threat_points)
        trust_score = round(max(0.0, 1.0 - threat_points), 4)
        threat_level = self._level(threat_points)
        automation_allowed = threat_level in {"low", "medium"} and threat_type != "telemetry_integrity_attack"
        if healing_action == "no_action":
            automation_allowed = True

        guard_action = "allow_automation"
        if threat_level == "medium":
            guard_action = "allow_with_monitoring"
        if threat_level == "high":
            guard_action = "require_human_approval"
        if threat_level == "critical" or threat_type == "telemetry_integrity_attack":
            guard_action = "block_and_quarantine"
            automation_allowed = False

        return SecurityAssessment(
            ai_trust_score=trust_score,
            aml_threat_level=threat_level,
            aml_threat_type=threat_type,
            guard_action=guard_action,
            automation_allowed=automation_allowed,
            reasons=sorted(set(reasons)),
        )

    @staticmethod
    def _float(row: dict[str, object], *keys: str) -> float:
        for key in keys:
            if key in row:
                return float(row[key])
        return 0.0

    @staticmethod
    def _priority_from_service(service: str) -> int:
        if service in {"URLLC", "V2X"}:
            return 6
        if service == "mMTC":
            return 4
        return 3

    @staticmethod
    def _level(points: float) -> str:
        if points >= 0.65:
            return "critical"
        if points >= 0.42:
            return "high"
        if points >= 0.2:
            return "medium"
        return "low"
