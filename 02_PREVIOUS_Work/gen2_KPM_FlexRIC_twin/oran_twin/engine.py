from __future__ import annotations

from pathlib import Path

from .automation_safety import AutomationSafetyScorer
from .conflict_manager import XAppConflictManager
from .core_transport import CoreTransportImpactTwin
from .detector import BaselineAnomalyDetector
from .digital_twin import DigitalTwin
from .drift_monitor import DriftMonitor
from .dtn_orchestrator import AiEnabledDtnOrchestrator
from .healing import HealingEngine
from .policy_orchestrator import ZsmPolicyOrchestrator
from .profiles import ServiceProfile, load_profiles
from .rca import RootCauseAnalyzer
from .security_guard import AdversarialMlGuard
from .self_learning import OnlineSelfLearningModel
from .slice_impact import SliceSlaImpactTwin
from .smo_governance import SmoGovernanceController
from .spectrum_monitor import SpectrumResourceMonitor
from .timing_security import TimingSecurityTwin


class OranDecisionEngine:
    """Shared decision engine for localhost demo mode and RIC/xApp-style mode."""

    def __init__(
        self,
        profiles: dict[str, ServiceProfile] | None = None,
        self_learning_model_path: str | Path | None = None,
    ) -> None:
        self.profiles = profiles or load_profiles()
        self.self_learning_model_path = Path(self_learning_model_path) if self_learning_model_path else None
        self.twin = DigitalTwin(self.profiles)
        self.detector = BaselineAnomalyDetector()
        self.drift_monitor = DriftMonitor()
        self.rca = RootCauseAnalyzer()
        self.healing = HealingEngine()
        self.conflict_manager = XAppConflictManager()
        self.security_guard = AdversarialMlGuard()
        self.timing_twin = TimingSecurityTwin()
        self.slice_twin = SliceSlaImpactTwin()
        self.spectrum_monitor = SpectrumResourceMonitor()
        self.core_transport_twin = CoreTransportImpactTwin()
        self.policy_orchestrator = ZsmPolicyOrchestrator()
        self.smo_governance = SmoGovernanceController()
        self.dtn_orchestrator = AiEnabledDtnOrchestrator()
        self.automation_safety = AutomationSafetyScorer()
        self.self_learning = self._load_self_learning()

    def reset(self) -> None:
        self.detector = BaselineAnomalyDetector()
        self.drift_monitor.reset()
        self.self_learning = self._load_self_learning()

    def _load_self_learning(self) -> OnlineSelfLearningModel:
        if self.self_learning_model_path and self.self_learning_model_path.exists():
            return OnlineSelfLearningModel.load(self.self_learning_model_path)
        return OnlineSelfLearningModel()

    def assess(self, row: dict[str, object]) -> dict[str, object]:
        normalized = normalize_engine_row(row)
        service = str(normalized["service_class"])
        profile = self.profiles[service]

        assessment = self.twin.assess(normalized)
        anomaly_score, anomaly_reasons = self.detector.score(normalized)
        self_learning = self.self_learning.assess(normalized)
        drift = self.drift_monitor.assess(normalized)
        signature_score, signature_reasons = fault_signature_score(normalized, profile)
        spectrum = self.spectrum_monitor.assess(normalized, profile)
        core_transport = self.core_transport_twin.assess(normalized, profile)
        anomaly_reasons = anomaly_reasons + signature_reasons + self_learning.reasons
        if spectrum.spectrum_state != "spectrum_stable":
            anomaly_reasons = anomaly_reasons + spectrum.reasons
        if core_transport.core_transport_state != "core_transport_stable":
            anomaly_reasons = anomaly_reasons + core_transport.reasons
        is_anomaly = (
            anomaly_score >= 0.35
            or assessment.sla_violation
            or signature_score >= 0.35
            or self_learning.anomaly_score >= 0.72
            or spectrum.spectrum_risk_score >= 0.62
            or core_transport.core_transport_risk_score >= 0.58
        )
        root_cause, explanation = (
            self.rca.infer(normalized, assessment.reasons, anomaly_reasons)
            if is_anomaly
            else ("normal", "Normal state.")
        )
        if (
            is_anomaly
            and root_cause in {"normal", "unknown_anomaly"}
            and self_learning.rca_prediction not in {"normal", "unknown"}
            and self_learning.rca_confidence >= 0.45
        ):
            root_cause = self_learning.rca_prediction
            explanation = (
                f"Online self-learning model matched the current KPI vector to learned "
                f"{self_learning.rca_prediction} centroid with confidence {self_learning.rca_confidence}."
            )
        if (
            is_anomaly
            and root_cause in {"normal", "unknown_anomaly", "capacity_degradation"}
            and core_transport.likely_core_cause != "normal"
            and core_transport.core_transport_risk_score >= 0.4
        ):
            root_cause = core_transport.likely_core_cause
            explanation = f"Core/transport twin detected {core_transport.likely_core_cause}: {', '.join(core_transport.reasons)}."
        action, action_reason = self.healing.recommend(root_cause, profile)
        conflict = self.conflict_manager.propose(
            row=normalized,
            root_cause=root_cause,
            primary_action=action,
            profile_priority=profile.priority_weight,
            risk_score=assessment.risk_score,
        )
        if conflict.selected_action != action:
            action = conflict.selected_action
            action_reason = f"Conflict manager selected {conflict.selected_xapp} action after {conflict.mitigation_strategy}."
        approved, post_risk, validation_note = self.healing.validate(
            {**normalized, "twin_risk_score": assessment.risk_score},
            root_cause,
            action,
        )
        baseline_approved = approved
        security = self.security_guard.assess(
            row=normalized,
            risk_score=assessment.risk_score,
            anomaly_score=anomaly_score,
            root_cause=root_cause,
            healing_action=action,
            twin_reasons=assessment.reasons,
            anomaly_reasons=anomaly_reasons + drift.reasons,
        )
        if drift.drift_status == "drifted" and action != "no_action":
            approved = False
            validation_note = f"{validation_note} Drift monitor: {drift.adaptation_action}."
        approved = approved and security.automation_allowed
        if not security.automation_allowed:
            validation_note = f"{validation_note} Security guard: {security.guard_action}."
        timing = self.timing_twin.assess(normalized, root_cause)
        slice_impact = self.slice_twin.assess(normalized, profile, assessment.risk_score, root_cause)
        policy = self.policy_orchestrator.decide(
            service_class=service,
            healing_action=action,
            approved=approved,
            risk_score=assessment.risk_score,
            drift_status=drift.drift_status,
            aml_threat_level=security.aml_threat_level,
            xapp_conflict_detected=conflict.conflict_detected,
            timing_state=timing.timing_state,
        )
        if policy.policy_state in {"policy_security_incident", "policy_quarantine", "policy_model_lifecycle_hold"} and action != "no_action":
            approved = False
            validation_note = f"{validation_note} Policy orchestrator: {policy.policy_action}."
        if conflict.cooldown_state == "cooldown_active" and action != "no_action":
            approved = False
            validation_note = f"{validation_note} xApp arbitration: cooldown active for {conflict.selected_xapp}."
        smo_governance = self.smo_governance.decide(
            service_class=service,
            root_cause=root_cause,
            risk_score=assessment.risk_score,
            drift_status=drift.drift_status,
            drift_retraining_priority=drift.retraining_priority,
            aml_threat_level=security.aml_threat_level,
            ai_trust_score=security.ai_trust_score,
            xapp_conflict_detected=conflict.conflict_detected,
            cooldown_state=conflict.cooldown_state,
            sla_breach_probability=slice_impact.sla_breach_probability,
            policy_state=policy.policy_state,
            action_approved=approved,
        )
        dtn = self.dtn_orchestrator.assess(
            risk_score=assessment.risk_score,
            anomaly_detected=is_anomaly,
            drift_status=drift.drift_status,
            aml_threat_level=security.aml_threat_level,
            xapp_conflict_detected=conflict.conflict_detected,
            timing_state=timing.timing_state,
            spectrum_state=spectrum.spectrum_state,
            sla_impact_level=slice_impact.sla_impact_level,
            sla_breach_probability=slice_impact.sla_breach_probability,
            policy_state=policy.policy_state,
            action_approved=approved,
        )
        automation_safety = self.automation_safety.assess(
            action=action,
            baseline_approved=baseline_approved,
            guarded_approved=approved,
            ai_trust_score=security.ai_trust_score,
            aml_threat_level=security.aml_threat_level,
            drift_status=drift.drift_status,
            xapp_conflict_detected=conflict.conflict_detected,
            sla_breach_probability=slice_impact.sla_breach_probability,
            timing_state=timing.timing_state,
            spectrum_state=spectrum.spectrum_state,
            policy_state=policy.policy_state,
            dtn_state=dtn.dtn_state,
        )

        confidence = round(min(0.98, 0.48 + assessment.risk_score * 0.52), 3)
        return {
            **normalized,
            "twin_risk_score": assessment.risk_score,
            "sla_violation": assessment.sla_violation,
            "twin_reasons": assessment.reasons,
            "anomaly_score": anomaly_score,
            "anomaly_detected": is_anomaly,
            "anomaly_reasons": anomaly_reasons,
            "fault_signature_score": signature_score,
            "self_learning_anomaly_score": self_learning.anomaly_score,
            "self_learning_anomaly_detected": self_learning.anomaly_detected,
            "self_learning_rca_prediction": self_learning.rca_prediction,
            "self_learning_rca_confidence": self_learning.rca_confidence,
            "self_learning_sample_count": self_learning.sample_count,
            "self_learning_mode": self_learning.learning_mode,
            "self_learning_reasons": self_learning.reasons,
            "drift_score": drift.drift_score,
            "drift_status": drift.drift_status,
            "drift_type": drift.drift_type,
            "drift_adaptation_action": drift.adaptation_action,
            "drift_model_profile_id": drift.model_profile_id,
            "drift_lifecycle_stage": drift.lifecycle_stage,
            "drift_retraining_priority": drift.retraining_priority,
            "drift_automation_mode": drift.automation_mode,
            "drift_reasons": drift.reasons,
            "root_cause": root_cause,
            "root_cause_explanation": explanation,
            "healing_action": action,
            "healing_reason": action_reason,
            "xapp_conflict_detected": conflict.conflict_detected,
            "xapp_conflict_type": conflict.conflict_type,
            "xapp_selected": conflict.selected_xapp,
            "xapp_mitigation_strategy": conflict.mitigation_strategy,
            "xapp_distillation_state": conflict.distillation_state,
            "xapp_replay_record": conflict.replay_record,
            "xapp_proposals": [proposal.__dict__ for proposal in conflict.proposals],
            "xapp_control_loop_latency_ms": conflict.control_loop_latency_ms,
            "xapp_cooldown_state": conflict.cooldown_state,
            "xapp_conflict_reasons": conflict.reasons,
            "timing_risk_score": timing.timing_risk_score,
            "timing_state": timing.timing_state,
            "timing_stride_threats": timing.stride_threats,
            "timing_ptp_domain": timing.ptp_domain,
            "timing_clock_role": timing.clock_role,
            "timing_estimated_ptp_offset_us": timing.estimated_ptp_offset_us,
            "timing_sync_state": timing.sync_state,
            "timing_stride_test_case": timing.stride_test_case,
            "timing_attack_surface": timing.attack_surface,
            "timing_recommended_action": timing.recommended_action,
            "timing_remediation_plan": timing.remediation_plan,
            "timing_reasons": timing.reasons,
            "spectrum_risk_score": spectrum.spectrum_risk_score,
            "spectrum_state": spectrum.spectrum_state,
            "spectrum_action": spectrum.spectrum_action,
            "spectrum_band": spectrum.spectrum_band,
            "spectrum_channel": spectrum.spectrum_channel,
            "spectrum_backup_band": spectrum.backup_band,
            "spectrum_channel_occupancy": spectrum.channel_occupancy,
            "spectrum_efficiency": spectrum.spectral_efficiency,
            "spectrum_interference_source": spectrum.interference_source,
            "spectrum_dsa_policy": spectrum.dsa_policy,
            "spectrum_dsa_confidence": spectrum.dsa_confidence,
            "spectrum_reasons": spectrum.reasons,
            "slice_impact_score": slice_impact.slice_impact_score,
            "sla_impact_level": slice_impact.sla_impact_level,
            "customer_impact": slice_impact.customer_impact,
            "revenue_risk": slice_impact.revenue_risk,
            "slice_id": slice_impact.slice_id,
            "tenant_segment": slice_impact.tenant_segment,
            "predicted_e2e_latency_ms": slice_impact.predicted_e2e_latency_ms,
            "sla_breach_probability": slice_impact.sla_breach_probability,
            "slice_affected_domain": slice_impact.affected_domain,
            "recommended_slice_action": slice_impact.recommended_slice_action,
            "slice_what_if_risk_reduction": slice_impact.what_if_risk_reduction,
            "slice_impact_reasons": slice_impact.reasons,
            "core_transport_risk_score": core_transport.core_transport_risk_score,
            "core_transport_state": core_transport.core_transport_state,
            "core_transport_affected_plane": core_transport.affected_plane,
            "core_transport_likely_cause": core_transport.likely_core_cause,
            "core_transport_recommended_action": core_transport.recommended_core_action,
            "core_transport_e2e_service_impact": core_transport.e2e_service_impact,
            "core_transport_reasons": core_transport.reasons,
            "policy_state": policy.policy_state,
            "policy_action": policy.policy_action,
            "policy_orchestration_domain": policy.orchestration_domain,
            "policy_requires_audit": policy.requires_audit,
            "policy_operator_id": policy.operator_id,
            "policy_tenant_id": policy.tenant_id,
            "policy_trust_zone": policy.trust_zone,
            "policy_federation_policy": policy.federation_policy,
            "policy_zsm_workflow_stage": policy.zsm_workflow_stage,
            "policy_audit_event_id": policy.audit_event_id,
            "policy_confidence": policy.policy_confidence,
            "policy_target_mttd_seconds": policy.target_mttd_seconds,
            "policy_target_mttm_seconds": policy.target_mttm_seconds,
            "policy_escalation_level": policy.escalation_level,
            "policy_reasons": policy.reasons,
            "smo_non_rt_policy_intent": smo_governance.non_rt_policy_intent,
            "smo_model_lifecycle_action": smo_governance.model_lifecycle_action,
            "smo_active_model": smo_governance.active_model,
            "smo_candidate_model": smo_governance.candidate_model,
            "smo_rollback_target": smo_governance.rollback_target,
            "smo_retraining_dataset_action": smo_governance.retraining_dataset_action,
            "smo_approval_gate": smo_governance.approval_gate,
            "smo_governance_state": smo_governance.governance_state,
            "smo_audit_class": smo_governance.audit_class,
            "smo_governance_reasons": smo_governance.reasons,
            "dtn_readiness_score": dtn.readiness_score,
            "dtn_state": dtn.dtn_state,
            "dtn_twin_sync_quality": dtn.twin_sync_quality,
            "dtn_ai_service_chain": dtn.ai_service_chain,
            "dtn_orchestration_mode": dtn.orchestration_mode,
            "dtn_next_best_capability": dtn.next_best_capability,
            "dtn_reasons": dtn.reasons,
            "automation_safety_score": automation_safety.score,
            "automation_safety_decision": automation_safety.decision,
            "automation_baseline_action": automation_safety.baseline_action,
            "automation_baseline_would_execute": automation_safety.baseline_would_execute,
            "automation_guarded_would_execute": automation_safety.guarded_would_execute,
            "automation_improvement": automation_safety.improvement,
            "unsafe_action_prevented": automation_safety.unsafe_action_prevented,
            "automation_safety_evidence": automation_safety.evidence,
            "ai_confidence": confidence,
            "ai_trust_score": security.ai_trust_score,
            "aml_threat_level": security.aml_threat_level,
            "aml_threat_type": security.aml_threat_type,
            "security_guard_action": security.guard_action,
            "security_guard_reasons": security.reasons,
            "action_approved_by_twin": approved,
            "post_action_risk_score": round(post_risk, 4),
            "validation_note": validation_note,
            "ric_control": build_ric_control(action, approved),
        }


def normalize_engine_row(row: dict[str, object]) -> dict[str, object]:
    service = str(row.get("service_class", row.get("service", "eMBB")))
    fault_active = row.get("fault_active")
    if fault_active is None:
        fault_active = row.get("fault", "normal") != "normal"
    return {
        "t": row.get("t", 0),
        "cell_id": row.get("cell_id", row.get("id", "CELL_A")),
        "site": row.get("site", ""),
        "lat": row.get("lat", 0.0),
        "lon": row.get("lon", 0.0),
        "edge_node": row.get("edge_node", row.get("edge", "")),
        "service_class": service,
        "fault_active": _bool(fault_active),
        "fault_type": row.get("fault_type", row.get("fault", "normal")),
        "aml_attack_active": _bool(row.get("aml_attack_active", False)),
        "aml_attack_type": row.get("aml_attack_type", "none"),
        "latency_ms": _float(row, "latency_ms", "latency"),
        "jitter_ms": _float(row, "jitter_ms", "jitter"),
        "throughput_mbps": _float(row, "throughput_mbps", "throughput"),
        "packet_loss_pct": _float(row, "packet_loss_pct", "loss"),
        "prb_util_pct": _float(row, "prb_util_pct", "prb"),
        "handover_fail_pct": _float(row, "handover_fail_pct", "handover"),
        "edge_delay_ms": _float(row, "edge_delay_ms", "edgeDelay"),
        "backhaul_delay_ms": _float(row, "backhaul_delay_ms", "backhaul"),
        "sinr_db": _float(row, "sinr_db", "sinr"),
        "bler_pct": _float(row, "bler_pct", "bler"),
        "cqi": _float(row, "cqi", "cqi_index"),
        "harq_retx_pct": _float(row, "harq_retx_pct", "harq"),
        "rlc_buffer_kbytes": _float(row, "rlc_buffer_kbytes", "rlc_buffer"),
        "mac_scheduler_delay_ms": _float(row, "mac_scheduler_delay_ms", "scheduler_delay"),
        "beam_quality_score": _float(row, "beam_quality_score", "beam_quality"),
        "timing_offset_us": _float(row, "timing_offset_us", "ptp_offset"),
        "fronthaul_delay_ms": _float(row, "fronthaul_delay_ms", "fronthaul_delay"),
        "rsrp_dbm": _float(row, "rsrp_dbm", "rsrp"),
        "rsrq_db": _float(row, "rsrq_db", "rsrq"),
        "rssi_dbm": _float(row, "rssi_dbm", "rssi"),
        "noise_floor_dbm": _float(row, "noise_floor_dbm", "noise_floor"),
        "evm_pct": _float(row, "evm_pct", "evm"),
        "interference_power_dbm": _float(row, "interference_power_dbm", "interference_power"),
        "beam_misalignment_deg": _float(row, "beam_misalignment_deg", "beam_misalignment"),
        "antenna_vswr": _float(row, "antenna_vswr", "vswr"),
        "rf_temperature_c": _float(row, "rf_temperature_c", "rf_temperature"),
        "rrc_setup_fail_pct": _float(row, "rrc_setup_fail_pct", "rrc_setup_fail"),
        "rrc_reestab_rate_pct": _float(row, "rrc_reestab_rate_pct", "rrc_reestab"),
        "pdcp_discard_rate_pct": _float(row, "pdcp_discard_rate_pct", "pdcp_discard"),
        "pdcp_reordering_delay_ms": _float(row, "pdcp_reordering_delay_ms", "pdcp_reordering_delay"),
        "sdap_qos_flow_drop_pct": _float(row, "sdap_qos_flow_drop_pct", "sdap_qos_drop"),
        "qfi_violation_pct": _float(row, "qfi_violation_pct", "qfi_violation"),
        "session_drop_rate_pct": _float(row, "session_drop_rate_pct", "session_drop"),
        "mobility_pingpong_pct": _float(row, "mobility_pingpong_pct", "mobility_pingpong"),
        "amf_registration_fail_pct": _float(row, "amf_registration_fail_pct", "amf_registration_fail"),
        "amf_paging_delay_ms": _float(row, "amf_paging_delay_ms", "amf_paging_delay"),
        "pdu_session_setup_ms": _float(row, "pdu_session_setup_ms", "pdu_session_setup"),
        "pdu_session_fail_pct": _float(row, "pdu_session_fail_pct", "pdu_session_fail"),
        "upf_cpu_util_pct": _float(row, "upf_cpu_util_pct", "upf_cpu"),
        "upf_packet_drop_pct": _float(row, "upf_packet_drop_pct", "upf_packet_drop"),
        "gtp_tunnel_loss_pct": _float(row, "gtp_tunnel_loss_pct", "gtp_loss"),
        "n3_rtt_ms": _float(row, "n3_rtt_ms", "n3_rtt"),
        "n6_internet_rtt_ms": _float(row, "n6_internet_rtt_ms", "n6_rtt"),
        "transport_jitter_ms": _float(row, "transport_jitter_ms", "transport_jitter"),
    }


def build_ric_control(action: str, approved: bool) -> dict[str, object]:
    if not approved or action == "no_action":
        return {"type": "none", "approved": approved, "payload": {}}
    payloads = {
        "load_balance_neighbor_cell": {"type": "e2_control", "policy": "traffic_steering", "intent": "rebalance_cell_load"},
        "prioritize_slice_and_traffic_steer": {
            "type": "e2_control",
            "policy": "critical_slice_traffic_steering",
            "intent": "protect_high_priority_slice",
        },
        "reroute_transport_path": {"type": "a1_policy", "policy": "transport_reroute", "intent": "reduce_backhaul_delay"},
        "mec_failover_or_scale": {"type": "o2_orchestration", "policy": "mec_scale_failover", "intent": "reduce_edge_delay"},
        "handover_parameter_tuning": {"type": "e2_control", "policy": "handover_optimization", "intent": "reduce_handover_failures"},
        "rrc_mobility_policy_tuning": {
            "type": "e2_control",
            "policy": "rrc_mobility_optimization",
            "intent": "reduce_ping_pong_and_rrc_reestablishment",
        },
        "qos_flow_remap_and_session_guard": {
            "type": "a1_policy",
            "policy": "sdap_qos_flow_assurance",
            "intent": "protect_qos_flows_and_reduce_session_drops",
        },
        "amf_pdu_session_recovery_review": {
            "type": "a1_policy",
            "policy": "core_control_plane_guard",
            "intent": "protect_registration_and_pdu_session_setup",
        },
        "upf_scale_or_traffic_reroute": {
            "type": "a1_policy",
            "policy": "upf_user_plane_reroute",
            "intent": "reduce_gtp_loss_and_core_user_plane_rtt",
        },
        "switch_timing_source": {"type": "o1_management", "policy": "timing_source_switch", "intent": "restore_sync_stability"},
        "resource_reallocation": {"type": "e2_control", "policy": "resource_reallocation", "intent": "restore_sla_margin"},
        "rebalance_spectrum_and_interference_watch": {
            "type": "e2_control",
            "policy": "spectrum_resource_rebalance",
            "intent": "reduce_radio_interference_or_resource_saturation",
        },
        "dynamic_spectrum_reassignment": {
            "type": "e2_control",
            "policy": "dynamic_spectrum_access",
            "intent": "move_slice_or_users_to_cleaner_channel",
        },
    }
    payload = payloads.get(action, {"type": "guarded_review", "policy": action, "intent": "manual_review"})
    return {"type": payload["type"], "approved": approved, "payload": payload}


def _float(row: dict[str, object], *keys: str) -> float:
    for key in keys:
        if key in row:
            return float(row[key])
    return 0.0


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def fault_signature_score(row: dict[str, object], profile: ServiceProfile) -> tuple[float, list[str]]:
    latency = float(row["latency_ms"])
    jitter = float(row["jitter_ms"])
    loss = float(row["packet_loss_pct"])
    prb = float(row["prb_util_pct"])
    handover = float(row["handover_fail_pct"])
    edge = float(row["edge_delay_ms"])
    backhaul = float(row["backhaul_delay_ms"])
    sinr = float(row["sinr_db"])
    bler = float(row["bler_pct"])
    throughput = float(row["throughput_mbps"])
    cqi = float(row.get("cqi", 0.0))
    harq = float(row.get("harq_retx_pct", 0.0))
    rlc_buffer = float(row.get("rlc_buffer_kbytes", 0.0))
    scheduler_delay = float(row.get("mac_scheduler_delay_ms", 0.0))
    timing_offset = float(row.get("timing_offset_us", 0.0))
    fronthaul_delay = float(row.get("fronthaul_delay_ms", 0.0))
    rsrp = float(row.get("rsrp_dbm", 0.0))
    rsrq = float(row.get("rsrq_db", 0.0))
    evm = float(row.get("evm_pct", 0.0))
    interference_power = float(row.get("interference_power_dbm", 0.0))
    beam_misalignment = float(row.get("beam_misalignment_deg", 0.0))
    antenna_vswr = float(row.get("antenna_vswr", 0.0))
    rf_temperature = float(row.get("rf_temperature_c", 0.0))
    rrc_setup_fail = float(row.get("rrc_setup_fail_pct", 0.0))
    rrc_reestab = float(row.get("rrc_reestab_rate_pct", 0.0))
    pdcp_discard = float(row.get("pdcp_discard_rate_pct", 0.0))
    pdcp_reorder = float(row.get("pdcp_reordering_delay_ms", 0.0))
    sdap_drop = float(row.get("sdap_qos_flow_drop_pct", 0.0))
    qfi_violation = float(row.get("qfi_violation_pct", 0.0))
    session_drop = float(row.get("session_drop_rate_pct", 0.0))
    mobility_pingpong = float(row.get("mobility_pingpong_pct", 0.0))

    score = 0.0
    reasons: list[str] = []
    congestion_signature = (
        prb > 84 and latency > profile.latency_ms_target * 1.18 and loss > profile.packet_loss_pct_target * 0.85
    ) or (
        prb > 70 and latency > profile.latency_ms_target * 1.35 and loss > profile.packet_loss_pct_target * 1.15
    ) or (
        prb > 88 and latency > profile.latency_ms_target * 1.35 and throughput < profile.throughput_mbps_target * 0.65
    )
    if congestion_signature:
        score += 0.42
        reasons.append("signature_cell_congestion")
    if backhaul > 14 or (backhaul > 10 and (jitter > profile.jitter_ms_target * 0.65 or loss > profile.packet_loss_pct_target * 1.4)):
        score += 0.42
        reasons.append("signature_backhaul_degradation")
    if loss > max(2.5, profile.packet_loss_pct_target * 4) and jitter > profile.jitter_ms_target * 0.75 and backhaul <= 12:
        score += 0.4
        reasons.append("signature_packet_loss_degradation")
    if sinr < 8 and bler > 5:
        score += 0.42
        reasons.append("signature_radio_link_degradation")
    if edge > max(4.5, profile.edge_dependency_level * 2.2) and latency > profile.latency_ms_target * 0.75:
        score += 0.42
        reasons.append("signature_edge_overload")
    if handover > max(2.35, 1.35 + profile.mobility_level * 0.38):
        score += 0.4
        reasons.append("signature_handover_instability")
    if jitter > profile.jitter_ms_target * 1.25 and bler > 2.8:
        score += 0.38
        reasons.append("signature_timing_drift")
    if throughput < profile.throughput_mbps_target * 0.55 and prb > 62:
        score += 0.32
        reasons.append("signature_capacity_pressure")
    if rlc_buffer > 850 and scheduler_delay > 7:
        score += 0.34
        reasons.append("signature_odu_scheduler_pressure")
    if cqi and cqi < 6.5 and harq > 9:
        score += 0.34
        reasons.append("signature_high_phy_link_retransmission")
    if timing_offset > 18 or fronthaul_delay > 4.5:
        score += 0.32
        reasons.append("signature_fronthaul_timing_pressure")
    if interference_power > -78 and rsrq < -15 and evm > 8:
        score += 0.36
        reasons.append("signature_oru_external_interference")
    if beam_misalignment > 18 and rsrp < -105:
        score += 0.34
        reasons.append("signature_oru_beam_misalignment")
    if antenna_vswr > 2.1 or rf_temperature > 78:
        score += 0.32
        reasons.append("signature_oru_rf_chain_degradation")
    if mobility_pingpong > 5 or rrc_reestab > 4 or (rrc_setup_fail > 5 and handover > 3):
        score += 0.36
        reasons.append("signature_ocu_mobility_control_instability")
    if sdap_drop > 4 or qfi_violation > 6 or session_drop > 3:
        score += 0.36
        reasons.append("signature_ocu_qos_session_degradation")
    if pdcp_discard > 4 and pdcp_reorder > 8:
        score += 0.32
        reasons.append("signature_ocu_pdcp_user_plane_degradation")
    return round(min(1.0, score), 4), reasons
