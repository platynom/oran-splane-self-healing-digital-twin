from __future__ import annotations

from dataclasses import dataclass

from .config import Paths, load_json


@dataclass(frozen=True)
class TimingAssessment:
    timing_risk_score: float
    timing_state: str
    stride_threats: list[str]
    ptp_domain: str
    clock_role: str
    estimated_ptp_offset_us: float
    sync_state: str
    stride_test_case: str
    attack_surface: str
    recommended_action: str
    remediation_plan: str
    reasons: list[str]


class TimingSecurityTwin:
    """PTP/TSN-inspired timing security twin for fronthaul and transport risk."""

    def __init__(self) -> None:
        profile = load_json(Paths.configs / "timing_security_profiles.json")
        self.domains = profile["domains"]
        self.stride_tests = profile["stride_tests"]

    def assess(self, row: dict[str, object], root_cause: str) -> TimingAssessment:
        jitter = float(row["jitter_ms"])
        backhaul = float(row["backhaul_delay_ms"])
        bler = float(row["bler_pct"])
        latency = float(row["latency_ms"])
        service = str(row["service_class"])
        edge_node = str(row.get("edge_node", "MEC_1"))
        domain = self.domains.get(edge_node, self.domains.get("MEC_1", {}))
        critical = service in {"URLLC", "V2X"}
        offset = self._estimate_ptp_offset_us(jitter, backhaul, bler, latency)
        max_offset = float(domain.get("max_offset_us", 2.0))

        score = 0.0
        threats: list[str] = []
        reasons: list[str] = []

        if jitter > (7.0 if critical else 14.0) and bler > 2.5:
            score += 0.38
            threats.extend(["tampering", "denial_of_service"])
            reasons.append("jitter_bler_timing_signature")
        if backhaul > 14 and jitter > 8:
            score += 0.26
            threats.append("denial_of_service")
            reasons.append("transport_delay_jitter_coupling")
        if offset > max_offset * (2.8 if critical else 3.6):
            score += 0.22
            threats.extend(["spoofing", "tampering"])
            reasons.append("ptp_offset_exceeds_domain_budget")
        if root_cause == "timing_drift":
            score += 0.34
            threats.extend(["spoofing", "tampering"])
            reasons.append("rca_timing_drift")
        if latency > 70 and critical:
            score += 0.16
            threats.append("service_degradation")
            reasons.append("critical_slice_latency_exposure")

        score = round(min(1.0, score), 4)
        state = "stable"
        action = "monitor_timing_domain"
        sync_state = "synchronized"
        if score >= 0.65:
            state = "timing_security_incident"
            action = "isolate_timing_domain_and_switch_source"
            sync_state = "unsafe_sync"
        elif score >= 0.35:
            state = "timing_watch"
            action = "increase_ptp_sync_monitoring"
            sync_state = "sync_degraded"
        elif offset > max_offset:
            sync_state = "sync_watch"

        primary_threat = self._primary_threat(threats)
        test_case = self.stride_tests.get(primary_threat, "ptp_baseline_sync_health_check")
        attack_surface = self._attack_surface(primary_threat, backhaul, jitter)
        remediation = self._remediation_plan(state, primary_threat, str(domain.get("backup_grandmaster_id", "backup_gm")))

        return TimingAssessment(
            timing_risk_score=score,
            timing_state=state,
            stride_threats=sorted(set(threats)),
            ptp_domain=str(domain.get("ptp_domain", "ptp_domain_unknown")),
            clock_role=str(domain.get("clock_role", "ordinary_clock")),
            estimated_ptp_offset_us=offset,
            sync_state=sync_state,
            stride_test_case=test_case,
            attack_surface=attack_surface,
            recommended_action=action,
            remediation_plan=remediation,
            reasons=sorted(set(reasons)),
        )

    @staticmethod
    def _estimate_ptp_offset_us(jitter: float, backhaul: float, bler: float, latency: float) -> float:
        offset = jitter * 0.38 + max(0.0, backhaul - 4.0) * 0.16 + bler * 0.22 + max(0.0, latency - 20.0) * 0.025
        return round(max(0.0, offset), 4)

    @staticmethod
    def _primary_threat(threats: list[str]) -> str:
        priority = ["spoofing", "tampering", "denial_of_service", "service_degradation"]
        for threat in priority:
            if threat in threats:
                return threat
        return "baseline"

    @staticmethod
    def _attack_surface(primary_threat: str, backhaul: float, jitter: float) -> str:
        if primary_threat in {"spoofing", "tampering"}:
            return "ptp_grandmaster_and_sync_messages"
        if primary_threat == "denial_of_service" or backhaul > 14:
            return "fronthaul_midhaul_timing_transport"
        if jitter > 8:
            return "tsn_scheduled_traffic_queue"
        return "timing_monitoring_plane"

    @staticmethod
    def _remediation_plan(state: str, primary_threat: str, backup_grandmaster: str) -> str:
        if state == "timing_security_incident":
            if primary_threat in {"spoofing", "tampering"}:
                return f"validate_grandmaster_identity_switch_to_{backup_grandmaster}_and_isolate_domain"
            if primary_threat == "denial_of_service":
                return "rate_limit_sync_path_reroute_timing_transport_and_escalate"
            return "isolate_timing_domain_and_trigger_ptp_forensics"
        if state == "timing_watch":
            return "increase_sync_sampling_and_verify_ptp_message_integrity"
        return "continue_ptp_baseline_monitoring"
