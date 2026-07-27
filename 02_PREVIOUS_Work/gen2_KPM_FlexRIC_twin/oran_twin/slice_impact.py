from __future__ import annotations

from dataclasses import dataclass

from .config import Paths, load_json
from .profiles import ServiceProfile


@dataclass(frozen=True)
class SliceImpactAssessment:
    slice_impact_score: float
    sla_impact_level: str
    customer_impact: str
    revenue_risk: str
    slice_id: str
    tenant_segment: str
    predicted_e2e_latency_ms: float
    sla_breach_probability: float
    affected_domain: str
    recommended_slice_action: str
    what_if_risk_reduction: float
    reasons: list[str]


class SliceSlaImpactTwin:
    """Maps technical twin risk to slice/SLA and business-impact posture."""

    def __init__(self) -> None:
        self.slice_profiles = load_json(Paths.configs / "slice_sla_profiles.json")

    def assess(self, row: dict[str, object], profile: ServiceProfile, risk_score: float, root_cause: str) -> SliceImpactAssessment:
        service = str(row["service_class"])
        slice_profile = self.slice_profiles.get(service, {})
        priority = profile.priority_weight
        latency = float(row["latency_ms"])
        edge_delay = float(row["edge_delay_ms"])
        backhaul_delay = float(row["backhaul_delay_ms"])
        jitter = float(row["jitter_ms"])
        throughput = float(row["throughput_mbps"])
        loss = float(row["packet_loss_pct"])
        score = risk_score * (0.75 + priority * 0.08)
        reasons: list[str] = []
        predicted_latency = self._predict_e2e_latency(row, profile)
        breach_probability = self._breach_probability(
            predicted_latency=predicted_latency,
            latency_target=profile.latency_ms_target,
            throughput=throughput,
            throughput_target=profile.throughput_mbps_target,
            loss=loss,
            loss_target=profile.packet_loss_pct_target,
            margin_pct=float(slice_profile.get("latency_sla_margin_pct", 20)),
        )
        affected_domain = self._affected_domain(root_cause, edge_delay, backhaul_delay, jitter)

        if root_cause != "normal":
            score += 0.08
            reasons.append(f"root_cause_{root_cause}")
        if breach_probability >= 0.65:
            score += 0.12
            reasons.append("predicted_e2e_sla_breach")
        if service in {"URLLC", "V2X"}:
            score += 0.08
            reasons.append("critical_low_latency_slice")
        if service in {"eMBB", "FWA"} and throughput < profile.throughput_mbps_target * 0.7:
            score += 0.08
            reasons.append("throughput_customer_experience_risk")
        if service == "mMTC" and loss > profile.packet_loss_pct_target * 1.4:
            score += 0.06
            reasons.append("iot_reliability_risk")

        score = round(min(1.0, score), 4)
        if score >= 0.72:
            level = "severe"
            customer = "probable_sla_breach"
            revenue = "high"
        elif score >= 0.45:
            level = "moderate"
            customer = "degraded_experience"
            revenue = "medium"
        elif score >= 0.25:
            level = "minor"
            customer = "watchlist"
            revenue = "low"
        else:
            level = "none"
            customer = "no_visible_impact"
            revenue = "none"

        if not reasons:
            reasons.append("within_slice_tolerance")
        recommended_action = self._slice_action(affected_domain, level, breach_probability)
        what_if_reduction = self._what_if_reduction(recommended_action, score)
        return SliceImpactAssessment(
            slice_impact_score=score,
            sla_impact_level=level,
            customer_impact=customer,
            revenue_risk=revenue,
            slice_id=str(slice_profile.get("slice_id", f"slice_{service.lower()}")),
            tenant_segment=str(slice_profile.get("tenant_segment", service.lower())),
            predicted_e2e_latency_ms=predicted_latency,
            sla_breach_probability=breach_probability,
            affected_domain=affected_domain,
            recommended_slice_action=recommended_action,
            what_if_risk_reduction=what_if_reduction,
            reasons=sorted(set(reasons)),
        )

    @staticmethod
    def _predict_e2e_latency(row: dict[str, object], profile: ServiceProfile) -> float:
        ran_latency = float(row["latency_ms"])
        edge_delay = float(row["edge_delay_ms"])
        backhaul_delay = float(row["backhaul_delay_ms"])
        jitter = float(row["jitter_ms"])
        loss = float(row["packet_loss_pct"])
        n3_rtt = float(row.get("n3_rtt_ms", 0.0))
        n6_rtt = float(row.get("n6_internet_rtt_ms", 0.0))
        pdu_setup = float(row.get("pdu_session_setup_ms", 0.0))
        criticality_weight = 1.15 if profile.priority_weight >= 5 else 1.0
        core_path_delay = n3_rtt * 0.22 + n6_rtt * 0.1 + pdu_setup * 0.015
        predicted = ran_latency + backhaul_delay * 0.55 + edge_delay * 0.75 + jitter * 0.18 + loss * 2.0 + core_path_delay
        return round(predicted * criticality_weight, 4)

    @staticmethod
    def _breach_probability(
        *,
        predicted_latency: float,
        latency_target: float,
        throughput: float,
        throughput_target: float,
        loss: float,
        loss_target: float,
        margin_pct: float,
    ) -> float:
        latency_limit = latency_target * (1.0 + margin_pct / 100.0)
        latency_pressure = max(0.0, (predicted_latency - latency_limit) / max(latency_limit, 0.001))
        throughput_pressure = max(0.0, (throughput_target * 0.72 - throughput) / max(throughput_target, 0.001))
        loss_pressure = max(0.0, (loss - loss_target * 1.25) / max(loss_target * 4.0, 0.001))
        probability = min(1.0, latency_pressure * 0.58 + throughput_pressure * 0.26 + loss_pressure * 0.32)
        return round(probability, 4)

    @staticmethod
    def _affected_domain(root_cause: str, edge_delay: float, backhaul_delay: float, jitter: float) -> str:
        if root_cause == "core_control_plane_degradation":
            return "core_control"
        if root_cause == "upf_user_plane_congestion":
            return "core_user"
        if root_cause == "transport_path_degradation":
            return "transport"
        if root_cause == "edge_overload" or edge_delay > 10:
            return "edge"
        if root_cause == "backhaul_degradation" or backhaul_delay > 12:
            return "transport"
        if root_cause == "timing_drift" or jitter > 8:
            return "timing"
        if root_cause in {"cell_congestion", "spectrum_interference", "handover_instability", "capacity_degradation"}:
            return "ran"
        return "service"

    @staticmethod
    def _slice_action(domain: str, level: str, breach_probability: float) -> str:
        if level == "none" and breach_probability < 0.25:
            return "maintain_slice_policy"
        actions = {
            "ran": "reallocate_slice_prbs_and_steer_traffic",
            "transport": "reroute_slice_transport_path",
            "core_control": "hold_slice_session_changes_and_review_amf",
            "core_user": "protect_slice_user_plane_and_reroute_upf",
            "edge": "scale_or_failover_slice_edge_workload",
            "timing": "protect_slice_timing_domain",
            "service": "raise_slice_assurance_watch",
        }
        return actions.get(domain, "raise_slice_assurance_watch")

    @staticmethod
    def _what_if_reduction(action: str, score: float) -> float:
        improvements = {
            "reallocate_slice_prbs_and_steer_traffic": 0.22,
            "reroute_slice_transport_path": 0.24,
            "hold_slice_session_changes_and_review_amf": 0.16,
            "protect_slice_user_plane_and_reroute_upf": 0.23,
            "scale_or_failover_slice_edge_workload": 0.26,
            "protect_slice_timing_domain": 0.2,
            "raise_slice_assurance_watch": 0.08,
            "maintain_slice_policy": 0.0,
        }
        return round(min(score, improvements.get(action, 0.05)), 4)
