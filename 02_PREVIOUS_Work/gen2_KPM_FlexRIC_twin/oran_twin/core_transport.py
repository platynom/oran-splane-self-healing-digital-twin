from __future__ import annotations

from dataclasses import dataclass

from .profiles import ServiceProfile


@dataclass(frozen=True)
class CoreTransportAssessment:
    core_transport_risk_score: float
    core_transport_state: str
    affected_plane: str
    likely_core_cause: str
    recommended_core_action: str
    e2e_service_impact: str
    reasons: list[str]


class CoreTransportImpactTwin:
    """5G Core and transport impact model for AMF/UPF/session/backhaul symptoms."""

    def assess(self, row: dict[str, object], profile: ServiceProfile) -> CoreTransportAssessment:
        amf_fail = float(row.get("amf_registration_fail_pct", 0.0))
        amf_paging = float(row.get("amf_paging_delay_ms", 0.0))
        pdu_setup = float(row.get("pdu_session_setup_ms", 0.0))
        pdu_fail = float(row.get("pdu_session_fail_pct", 0.0))
        upf_cpu = float(row.get("upf_cpu_util_pct", 0.0))
        upf_drop = float(row.get("upf_packet_drop_pct", 0.0))
        gtp_loss = float(row.get("gtp_tunnel_loss_pct", 0.0))
        n3_rtt = float(row.get("n3_rtt_ms", 0.0))
        n6_rtt = float(row.get("n6_internet_rtt_ms", 0.0))
        transport_jitter = float(row.get("transport_jitter_ms", 0.0))

        score = 0.0
        reasons: list[str] = []
        affected_plane = "none"
        likely_cause = "normal"
        action = "maintain_core_transport_policy"

        control_plane = amf_fail > 3.0 or amf_paging > 80.0 or pdu_fail > 3.0 or pdu_setup > 180.0
        user_plane = upf_cpu > 82.0 or upf_drop > 3.0 or gtp_loss > 2.5 or n3_rtt > 45.0
        transport = n6_rtt > 90.0 or transport_jitter > 18.0 or (n3_rtt > 35.0 and gtp_loss > 1.5)

        if control_plane:
            score += 0.38
            affected_plane = "control_plane"
            likely_cause = "core_control_plane_degradation"
            action = "amf_pdu_session_recovery_review"
            reasons.append("amf_or_pdu_session_control_plane_pressure")
        if user_plane:
            score += 0.42
            affected_plane = "user_plane" if affected_plane == "none" else "multi_plane"
            likely_cause = "upf_user_plane_congestion"
            action = "upf_scale_or_traffic_reroute"
            reasons.append("upf_or_gtp_user_plane_pressure")
        if transport:
            score += 0.34
            affected_plane = "transport" if affected_plane == "none" else "multi_plane"
            likely_cause = "transport_path_degradation" if likely_cause == "normal" else likely_cause
            action = "reroute_transport_path" if action == "maintain_core_transport_policy" else action
            reasons.append("n3_n6_transport_path_pressure")

        if profile.priority_weight >= 5 and score > 0:
            score += 0.08
            reasons.append("critical_service_core_transport_impact")

        score = round(min(1.0, score), 4)
        if score >= 0.72:
            state = "core_transport_incident"
            impact = "probable_e2e_service_degradation"
        elif score >= 0.4:
            state = "core_transport_watch"
            impact = "possible_e2e_service_degradation"
        else:
            state = "core_transport_stable"
            impact = "no_visible_core_transport_impact"

        if not reasons:
            reasons.append("core_transport_within_expected_range")

        return CoreTransportAssessment(
            core_transport_risk_score=score,
            core_transport_state=state,
            affected_plane=affected_plane,
            likely_core_cause=likely_cause,
            recommended_core_action=action,
            e2e_service_impact=impact,
            reasons=sorted(set(reasons)),
        )
