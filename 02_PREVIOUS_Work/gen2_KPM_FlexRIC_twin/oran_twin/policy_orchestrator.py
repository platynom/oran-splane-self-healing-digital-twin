from __future__ import annotations

from dataclasses import dataclass

from .config import Paths, load_json


@dataclass(frozen=True)
class PolicyDecision:
    policy_state: str
    policy_action: str
    orchestration_domain: str
    requires_audit: bool
    operator_id: str
    tenant_id: str
    trust_zone: str
    federation_policy: str
    zsm_workflow_stage: str
    audit_event_id: str
    policy_confidence: float
    target_mttd_seconds: int
    target_mttm_seconds: int
    escalation_level: str
    reasons: list[str]


class ZsmPolicyOrchestrator:
    """Policy governance layer inspired by SMO/ZSM secure orchestration work."""

    def __init__(self) -> None:
        profile = load_json(Paths.configs / "zsm_policy_profiles.json")
        self.operators = profile["operators"]
        self.automation_slas = profile["automation_slas"]

    def decide(
        self,
        *,
        service_class: str,
        healing_action: str,
        approved: bool,
        risk_score: float,
        drift_status: str,
        aml_threat_level: str,
        xapp_conflict_detected: bool,
        timing_state: str,
    ) -> PolicyDecision:
        reasons: list[str] = []
        operator = self.operators.get(service_class, self.operators.get("eMBB", {}))
        domain = self._domain_for_action(healing_action)
        state = "policy_allow"
        action = "execute_or_record_decision"
        requires_audit = service_class in {"URLLC", "V2X"} or healing_action != "no_action"

        if not approved:
            state = "policy_blocked"
            action = "hold_action_and_raise_noc_ticket"
            reasons.append("automation_not_approved")
        if aml_threat_level in {"high", "critical"}:
            state = "policy_quarantine"
            action = "quarantine_ai_control_path"
            reasons.append("high_aml_threat")
        if drift_status == "drifted":
            state = "policy_model_lifecycle_hold"
            action = "trigger_model_review_before_control"
            reasons.append("model_drifted")
        if xapp_conflict_detected:
            reasons.append("xapp_conflict_arbitrated")
        if timing_state == "timing_security_incident":
            state = "policy_security_incident"
            action = "isolate_timing_domain_and_escalate"
            reasons.append("timing_security_incident")
        if risk_score >= 0.8 and approved:
            reasons.append("high_risk_action_approved")

        if not reasons:
            reasons.append("policy_normal")
        workflow_stage = self._workflow_stage(state)
        sla = self.automation_slas.get(state, self.automation_slas["policy_allow"])
        confidence = self._policy_confidence(
            approved=approved,
            risk_score=risk_score,
            aml_threat_level=aml_threat_level,
            drift_status=drift_status,
            timing_state=timing_state,
            xapp_conflict_detected=xapp_conflict_detected,
        )
        escalation = self._escalation_level(
            state=state,
            trust_zone=str(operator.get("trust_zone", "standard_managed")),
            risk_score=risk_score,
            aml_threat_level=aml_threat_level,
        )
        audit_event_id = self._audit_id(
            service_class=service_class,
            domain=domain,
            state=state,
            action=healing_action,
        )

        return PolicyDecision(
            policy_state=state,
            policy_action=action,
            orchestration_domain=domain,
            requires_audit=requires_audit,
            operator_id=str(operator.get("operator_id", "operator_default")),
            tenant_id=str(operator.get("tenant_id", "tenant_default")),
            trust_zone=str(operator.get("trust_zone", "standard_managed")),
            federation_policy=str(operator.get("federation_policy", "single_operator")),
            zsm_workflow_stage=workflow_stage,
            audit_event_id=audit_event_id,
            policy_confidence=confidence,
            target_mttd_seconds=int(sla["target_mttd_seconds"]),
            target_mttm_seconds=int(sla["target_mttm_seconds"]),
            escalation_level=escalation,
            reasons=sorted(set(reasons)),
        )

    @staticmethod
    def _domain_for_action(action: str) -> str:
        if action in {"load_balance_neighbor_cell", "prioritize_slice_and_traffic_steer", "handover_parameter_tuning", "resource_reallocation"}:
            return "near_rt_ric"
        if action in {"reroute_transport_path", "switch_timing_source"}:
            return "smo_o1_a1_transport"
        if action in {"amf_pdu_session_recovery_review", "upf_scale_or_traffic_reroute"}:
            return "smo_a1_core_transport"
        if action == "mec_failover_or_scale":
            return "o_cloud_o2"
        if action == "human_review_guarded_mode":
            return "noc_smo"
        return "monitoring"

    @staticmethod
    def _workflow_stage(state: str) -> str:
        mapping = {
            "policy_allow": "detect_decide_execute_record",
            "policy_blocked": "detect_hold_ticket_review",
            "policy_quarantine": "detect_quarantine_forensics_recover",
            "policy_model_lifecycle_hold": "detect_freeze_model_review_retrain",
            "policy_security_incident": "detect_isolate_escalate_recover",
        }
        return mapping.get(state, "detect_review_record")

    @staticmethod
    def _policy_confidence(
        *,
        approved: bool,
        risk_score: float,
        aml_threat_level: str,
        drift_status: str,
        timing_state: str,
        xapp_conflict_detected: bool,
    ) -> float:
        confidence = 0.92 if approved else 0.68
        confidence -= 0.12 if aml_threat_level in {"high", "critical"} else 0.0
        confidence -= 0.08 if drift_status == "drifted" else 0.0
        confidence -= 0.08 if timing_state == "timing_security_incident" else 0.0
        confidence -= 0.03 if xapp_conflict_detected else 0.0
        confidence -= min(0.08, max(0.0, risk_score - 0.75) * 0.2)
        return round(max(0.0, min(1.0, confidence)), 4)

    @staticmethod
    def _escalation_level(*, state: str, trust_zone: str, risk_score: float, aml_threat_level: str) -> str:
        if state in {"policy_security_incident", "policy_quarantine"} or aml_threat_level == "critical":
            return "soc_noc_joint_incident"
        if trust_zone == "critical_managed" and (risk_score >= 0.55 or state != "policy_allow"):
            return "operator_duty_manager"
        if state in {"policy_blocked", "policy_model_lifecycle_hold"}:
            return "noc_engineer_review"
        return "auto_record"

    @staticmethod
    def _audit_id(*, service_class: str, domain: str, state: str, action: str) -> str:
        raw = f"{service_class}:{domain}:{state}:{action}"
        value = sum((idx + 1) * ord(char) for idx, char in enumerate(raw)) % 100000
        return f"audit_{service_class.lower()}_{domain}_{value:05d}"
