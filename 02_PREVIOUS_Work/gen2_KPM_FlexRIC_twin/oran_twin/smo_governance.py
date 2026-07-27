from __future__ import annotations

from dataclasses import dataclass

from .config import Paths, load_json
from .model_registry import ModelRegistry


@dataclass(frozen=True)
class SmoGovernanceDecision:
    non_rt_policy_intent: str
    model_lifecycle_action: str
    active_model: str
    candidate_model: str
    rollback_target: str
    retraining_dataset_action: str
    approval_gate: str
    governance_state: str
    audit_class: str
    reasons: list[str]


class SmoGovernanceController:
    """Non-RT RIC/SMO governance for policy, model lifecycle, and audit planning."""

    def __init__(self) -> None:
        self.policy = load_json(Paths.configs / "smo_governance_policy.json")
        self.registry = ModelRegistry()

    def decide(
        self,
        *,
        service_class: str,
        root_cause: str,
        risk_score: float,
        drift_status: str,
        drift_retraining_priority: str,
        aml_threat_level: str,
        ai_trust_score: float,
        xapp_conflict_detected: bool,
        cooldown_state: str,
        sla_breach_probability: float,
        policy_state: str,
        action_approved: bool,
    ) -> SmoGovernanceDecision:
        active_model = self._active_model()
        candidate_model = "none"
        rollback_target = str(self.policy.get("rollback_targets", {}).get(active_model, "none"))
        reasons: list[str] = []
        thresholds = self.policy["governance_thresholds"]

        governance_state = "governance_normal"
        non_rt_policy_intent = "maintain_current_policy"
        lifecycle_action = "keep_active_model"
        retraining_action = "append_to_audit_dataset"
        approval_gate = str(self.policy["approval_gates"]["normal"])
        audit_class = "standard_audit"

        if policy_state in {"policy_security_incident", "policy_quarantine"} or aml_threat_level in {"high", "critical"}:
            governance_state = "security_governed"
            non_rt_policy_intent = "quarantine_or_restrict_ai_control_policy"
            lifecycle_action = "freeze_model_and_request_forensics"
            retraining_action = "exclude_until_security_review"
            approval_gate = str(self.policy["approval_gates"]["security"])
            audit_class = "security_audit"
            reasons.append("security_or_aml_governance_required")
        elif drift_status == "drifted" or drift_retraining_priority in {"high", "critical"}:
            governance_state = "model_lifecycle_governed"
            non_rt_policy_intent = "freeze_closed_loop_until_model_review"
            lifecycle_action = "train_candidate_and_compare_before_promotion"
            candidate_model = self._candidate_for_root_cause(root_cause)
            retraining_action = "create_retraining_slice_from_recent_telemetry"
            approval_gate = str(self.policy["approval_gates"]["model"])
            audit_class = "model_lifecycle_audit"
            reasons.append("drift_requires_model_lifecycle_action")
        elif cooldown_state == "cooldown_active" or xapp_conflict_detected:
            governance_state = "control_governed"
            non_rt_policy_intent = "tighten_near_rt_ric_control_policy"
            lifecycle_action = "keep_active_model"
            retraining_action = "append_conflict_outcome_to_policy_replay"
            approval_gate = str(self.policy["approval_gates"]["guarded"])
            audit_class = "control_policy_audit"
            reasons.append("near_rt_control_governance_required")
        elif risk_score >= float(thresholds["critical_risk"]) or (
            sla_breach_probability >= float(thresholds["high_sla_breach"]) and service_class in {"URLLC", "V2X"}
        ):
            governance_state = "critical_service_governed"
            non_rt_policy_intent = "protect_critical_slice_policy"
            lifecycle_action = "keep_active_model_with_shadow_monitoring"
            candidate_model = self._candidate_for_root_cause(root_cause)
            retraining_action = "label_high_impact_incident_for_retraining"
            approval_gate = str(self.policy["approval_gates"]["critical"])
            audit_class = "critical_service_audit"
            reasons.append("critical_service_or_sla_governance_required")
        elif ai_trust_score < float(thresholds["low_trust"]) or not action_approved:
            governance_state = "guarded_operation"
            non_rt_policy_intent = "require_guarded_policy_for_low_trust_action"
            lifecycle_action = "keep_active_model_and_collect_more_evidence"
            retraining_action = "append_low_trust_case_to_review_queue"
            approval_gate = str(self.policy["approval_gates"]["guarded"])
            audit_class = "guarded_action_audit"
            reasons.append("low_trust_or_unapproved_action")

        if not reasons:
            reasons.append("smo_policy_normal")

        return SmoGovernanceDecision(
            non_rt_policy_intent=non_rt_policy_intent,
            model_lifecycle_action=lifecycle_action,
            active_model=active_model,
            candidate_model=candidate_model,
            rollback_target=rollback_target,
            retraining_dataset_action=retraining_action,
            approval_gate=approval_gate,
            governance_state=governance_state,
            audit_class=audit_class,
            reasons=sorted(set(reasons)),
        )

    def _active_model(self) -> str:
        try:
            return self.registry.active_models().get(
                "self_learning",
                str(self.policy.get("active_model", "unknown_model")),
            )
        except (FileNotFoundError, KeyError, ValueError):
            return str(self.policy.get("active_model", "unknown_model"))

    def _candidate_for_root_cause(self, root_cause: str) -> str:
        candidates = self.policy.get("candidate_models", {})
        if root_cause in {"spectrum_interference", "radio_quality_degradation"}:
            return str(candidates.get("oru_low_phy", "none"))
        if root_cause in {"handover_instability", "qos_session_degradation"}:
            return str(candidates.get("ocu", "none"))
        return "none"
