from __future__ import annotations

from dataclasses import dataclass

from .config import Paths, load_json


@dataclass(frozen=True)
class DtnAssessment:
    readiness_score: float
    dtn_state: str
    twin_sync_quality: str
    ai_service_chain: list[str]
    orchestration_mode: str
    next_best_capability: str
    reasons: list[str]


class AiEnabledDtnOrchestrator:
    """Cross-domain AI-enabled DTN readiness layer inspired by 6G DTN survey work."""

    def __init__(self) -> None:
        profile = load_json(Paths.configs / "dtn_capability_profiles.json")
        self.capabilities = profile["capabilities"]
        self.thresholds = profile["readiness_thresholds"]

    def assess(
        self,
        *,
        risk_score: float,
        anomaly_detected: bool,
        drift_status: str,
        aml_threat_level: str,
        xapp_conflict_detected: bool,
        timing_state: str,
        spectrum_state: str,
        sla_impact_level: str,
        sla_breach_probability: float,
        policy_state: str,
        action_approved: bool,
    ) -> DtnAssessment:
        reasons: list[str] = []
        capability_scores = {
            "prediction": self._prediction_score(risk_score, sla_breach_probability),
            "anomaly_detection": 0.92 if anomaly_detected or spectrum_state != "spectrum_stable" else 0.78,
            "optimization": self._optimization_score(action_approved, xapp_conflict_detected, policy_state),
            "security_assurance": self._security_score(aml_threat_level, timing_state, policy_state),
            "slice_assurance": self._slice_score(sla_impact_level, sla_breach_probability),
            "model_lifecycle": self._lifecycle_score(drift_status),
            "closed_loop_governance": self._governance_score(policy_state, action_approved),
        }
        score = 0.0
        for capability, value in capability_scores.items():
            score += value * float(self.capabilities[capability]["weight"])

        if drift_status == "drifted":
            reasons.append("model_lifecycle_unstable")
        if aml_threat_level in {"high", "critical"}:
            reasons.append("security_threat_requires_guarded_dtn")
        if timing_state == "timing_security_incident":
            reasons.append("timing_domain_not_trusted")
        if sla_breach_probability >= 0.65:
            reasons.append("predicted_slice_sla_breach")
        if policy_state != "policy_allow":
            reasons.append(f"governance_{policy_state}")
        if xapp_conflict_detected:
            reasons.append("xapp_distillation_required")

        readiness = round(max(0.0, min(1.0, score)), 4)
        state = self._state(readiness, policy_state, aml_threat_level, drift_status, timing_state)
        sync_quality = self._sync_quality(drift_status, timing_state, spectrum_state)
        chain = self._service_chain(capability_scores)
        mode = self._orchestration_mode(state, action_approved)
        next_best = min(capability_scores.items(), key=lambda item: item[1])[0]
        if not reasons:
            reasons.append("dtn_capabilities_nominal")
        return DtnAssessment(
            readiness_score=readiness,
            dtn_state=state,
            twin_sync_quality=sync_quality,
            ai_service_chain=chain,
            orchestration_mode=mode,
            next_best_capability=next_best,
            reasons=sorted(set(reasons)),
        )

    @staticmethod
    def _prediction_score(risk_score: float, sla_breach_probability: float) -> float:
        if risk_score >= 0.55 or sla_breach_probability >= 0.45:
            return 0.92
        return 0.78

    @staticmethod
    def _optimization_score(action_approved: bool, xapp_conflict_detected: bool, policy_state: str) -> float:
        if policy_state in {"policy_quarantine", "policy_security_incident"}:
            return 0.44
        if not action_approved:
            return 0.58
        return 0.86 if xapp_conflict_detected else 0.8

    @staticmethod
    def _security_score(aml_threat_level: str, timing_state: str, policy_state: str) -> float:
        if aml_threat_level == "critical" or policy_state == "policy_quarantine":
            return 0.96
        if aml_threat_level == "high" or timing_state == "timing_security_incident":
            return 0.9
        if aml_threat_level == "medium":
            return 0.78
        return 0.72

    @staticmethod
    def _slice_score(sla_impact_level: str, sla_breach_probability: float) -> float:
        if sla_impact_level == "severe" or sla_breach_probability >= 0.65:
            return 0.92
        if sla_impact_level == "moderate":
            return 0.82
        if sla_impact_level == "minor":
            return 0.76
        return 0.68

    @staticmethod
    def _lifecycle_score(drift_status: str) -> float:
        return {
            "warming_up": 0.58,
            "stable": 0.86,
            "warning": 0.74,
            "drifted": 0.52,
        }.get(drift_status, 0.62)

    @staticmethod
    def _governance_score(policy_state: str, action_approved: bool) -> float:
        if policy_state == "policy_allow" and action_approved:
            return 0.9
        if policy_state == "policy_allow":
            return 0.78
        if policy_state in {"policy_quarantine", "policy_security_incident"}:
            return 0.86
        return 0.74

    def _state(
        self,
        readiness: float,
        policy_state: str,
        aml_threat_level: str,
        drift_status: str,
        timing_state: str,
    ) -> str:
        if policy_state in {"policy_quarantine", "policy_security_incident"} or aml_threat_level == "critical":
            return "security_hold"
        if drift_status == "drifted" or timing_state == "timing_security_incident":
            return "guarded_operation"
        if readiness >= float(self.thresholds["autonomous_ready"]):
            return "autonomous_ready"
        if readiness >= float(self.thresholds["guarded_operation"]):
            return "guarded_operation"
        if readiness >= float(self.thresholds["degraded_twin"]):
            return "degraded_twin"
        return "not_ready"

    @staticmethod
    def _sync_quality(drift_status: str, timing_state: str, spectrum_state: str) -> str:
        if drift_status == "drifted" or timing_state == "timing_security_incident":
            return "out_of_sync"
        if drift_status == "warning" or timing_state == "timing_watch" or spectrum_state == "spectrum_watch":
            return "partially_synchronized"
        return "synchronized"

    @staticmethod
    def _service_chain(capability_scores: dict[str, float]) -> list[str]:
        return [name for name, score in sorted(capability_scores.items()) if score >= 0.75]

    @staticmethod
    def _orchestration_mode(state: str, action_approved: bool) -> str:
        if state == "autonomous_ready" and action_approved:
            return "closed_loop_autonomous"
        if state in {"guarded_operation", "degraded_twin"}:
            return "human_guarded_closed_loop"
        if state == "security_hold":
            return "closed_loop_suspended"
        return "monitor_only"
