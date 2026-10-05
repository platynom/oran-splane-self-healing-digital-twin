from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from oran_twin.engine import OranDecisionEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the O-RAN decision engine in RIC/xApp-style mode.")
    parser.add_argument("--input", default="data/telemetry/sample_oai_like_kpis.csv", help="Normalized KPI CSV input.")
    parser.add_argument("--output", default="outputs/xapp_decisions.jsonl", help="JSONL decision output path.")
    parser.add_argument("--service", default="eMBB", help="Service class to evaluate when input has no service column.")
    parser.add_argument("--cell-id", default="", help="Optional cell filter.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    rows = load_rows(input_path, default_service=args.service)
    if args.cell_id:
        rows = [row for row in rows if str(row.get("cell_id", "")) == args.cell_id]

    engine = OranDecisionEngine()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for t, row in enumerate(rows):
            decision = engine.assess({**row, "t": row.get("t", t)})
            handle.write(json.dumps(to_xapp_decision(decision), separators=(",", ":")) + "\n")

    print(f"xApp-style decisions written to: {output_path}")
    print(f"records: {len(rows)}")


def load_rows(path: Path, default_service: str) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row.setdefault("service_class", default_service)
        row.setdefault("fault_type", "unknown_live_kpi")
        row.setdefault("fault_active", False)
    return rows


def to_xapp_decision(decision: dict[str, object]) -> dict[str, object]:
    return {
        "runtime": "near_rt_ric_xapp_style",
        "cell_id": decision["cell_id"],
        "service_class": decision["service_class"],
        "aml_attack": {
            "active": decision.get("aml_attack_active", False),
            "type": decision.get("aml_attack_type", "none"),
        },
        "risk_score": decision["twin_risk_score"],
        "sla_violation": decision["sla_violation"],
        "anomaly": {
            "detected": decision["anomaly_detected"],
            "score": decision["anomaly_score"],
            "reasons": decision["anomaly_reasons"],
        },
        "drift": {
            "score": decision["drift_score"],
            "status": decision["drift_status"],
            "type": decision["drift_type"],
            "adaptation_action": decision["drift_adaptation_action"],
            "model_profile_id": decision["drift_model_profile_id"],
            "lifecycle_stage": decision["drift_lifecycle_stage"],
            "retraining_priority": decision["drift_retraining_priority"],
            "automation_mode": decision["drift_automation_mode"],
            "reasons": decision["drift_reasons"],
        },
        "rca": {
            "root_cause": decision["root_cause"],
            "explanation": decision["root_cause_explanation"],
        },
        "healing": {
            "action": decision["healing_action"],
            "reason": decision["healing_reason"],
            "approved": decision["action_approved_by_twin"],
            "post_action_risk_score": decision["post_action_risk_score"],
            "validation_note": decision["validation_note"],
        },
        "automation_safety": {
            "score": decision["automation_safety_score"],
            "decision": decision["automation_safety_decision"],
            "baseline_action": decision["automation_baseline_action"],
            "baseline_would_execute": decision["automation_baseline_would_execute"],
            "guarded_would_execute": decision["automation_guarded_would_execute"],
            "unsafe_action_prevented": decision["unsafe_action_prevented"],
            "improvement": decision["automation_improvement"],
            "evidence": decision["automation_safety_evidence"],
        },
        "xapp_conflict": {
            "detected": decision["xapp_conflict_detected"],
            "type": decision["xapp_conflict_type"],
            "selected_xapp": decision["xapp_selected"],
            "mitigation_strategy": decision["xapp_mitigation_strategy"],
            "distillation_state": decision["xapp_distillation_state"],
            "control_loop_latency_ms": decision["xapp_control_loop_latency_ms"],
            "cooldown_state": decision["xapp_cooldown_state"],
            "replay_record": decision["xapp_replay_record"],
            "proposals": decision["xapp_proposals"],
            "reasons": decision["xapp_conflict_reasons"],
        },
        "timing_security": {
            "risk_score": decision["timing_risk_score"],
            "state": decision["timing_state"],
            "stride_threats": decision["timing_stride_threats"],
            "ptp_domain": decision["timing_ptp_domain"],
            "clock_role": decision["timing_clock_role"],
            "estimated_ptp_offset_us": decision["timing_estimated_ptp_offset_us"],
            "sync_state": decision["timing_sync_state"],
            "stride_test_case": decision["timing_stride_test_case"],
            "attack_surface": decision["timing_attack_surface"],
            "recommended_action": decision["timing_recommended_action"],
            "remediation_plan": decision["timing_remediation_plan"],
            "reasons": decision["timing_reasons"],
        },
        "spectrum": {
            "risk_score": decision["spectrum_risk_score"],
            "state": decision["spectrum_state"],
            "action": decision["spectrum_action"],
            "band": decision["spectrum_band"],
            "channel": decision["spectrum_channel"],
            "backup_band": decision["spectrum_backup_band"],
            "channel_occupancy": decision["spectrum_channel_occupancy"],
            "spectral_efficiency": decision["spectrum_efficiency"],
            "interference_source": decision["spectrum_interference_source"],
            "dsa_policy": decision["spectrum_dsa_policy"],
            "dsa_confidence": decision["spectrum_dsa_confidence"],
            "reasons": decision["spectrum_reasons"],
        },
        "slice_impact": {
            "score": decision["slice_impact_score"],
            "sla_impact_level": decision["sla_impact_level"],
            "customer_impact": decision["customer_impact"],
            "revenue_risk": decision["revenue_risk"],
            "slice_id": decision["slice_id"],
            "tenant_segment": decision["tenant_segment"],
            "predicted_e2e_latency_ms": decision["predicted_e2e_latency_ms"],
            "sla_breach_probability": decision["sla_breach_probability"],
            "affected_domain": decision["slice_affected_domain"],
            "recommended_slice_action": decision["recommended_slice_action"],
            "what_if_risk_reduction": decision["slice_what_if_risk_reduction"],
            "reasons": decision["slice_impact_reasons"],
        },
        "core_transport": {
            "risk_score": decision["core_transport_risk_score"],
            "state": decision["core_transport_state"],
            "affected_plane": decision["core_transport_affected_plane"],
            "likely_cause": decision["core_transport_likely_cause"],
            "recommended_action": decision["core_transport_recommended_action"],
            "e2e_service_impact": decision["core_transport_e2e_service_impact"],
            "reasons": decision["core_transport_reasons"],
        },
        "policy": {
            "state": decision["policy_state"],
            "action": decision["policy_action"],
            "domain": decision["policy_orchestration_domain"],
            "requires_audit": decision["policy_requires_audit"],
            "operator_id": decision["policy_operator_id"],
            "tenant_id": decision["policy_tenant_id"],
            "trust_zone": decision["policy_trust_zone"],
            "federation_policy": decision["policy_federation_policy"],
            "zsm_workflow_stage": decision["policy_zsm_workflow_stage"],
            "audit_event_id": decision["policy_audit_event_id"],
            "confidence": decision["policy_confidence"],
            "target_mttd_seconds": decision["policy_target_mttd_seconds"],
            "target_mttm_seconds": decision["policy_target_mttm_seconds"],
            "escalation_level": decision["policy_escalation_level"],
            "reasons": decision["policy_reasons"],
        },
        "smo_governance": {
            "non_rt_policy_intent": decision["smo_non_rt_policy_intent"],
            "model_lifecycle_action": decision["smo_model_lifecycle_action"],
            "active_model": decision["smo_active_model"],
            "candidate_model": decision["smo_candidate_model"],
            "rollback_target": decision["smo_rollback_target"],
            "retraining_dataset_action": decision["smo_retraining_dataset_action"],
            "approval_gate": decision["smo_approval_gate"],
            "governance_state": decision["smo_governance_state"],
            "audit_class": decision["smo_audit_class"],
            "reasons": decision["smo_governance_reasons"],
        },
        "digital_twin_network": {
            "readiness_score": decision["dtn_readiness_score"],
            "state": decision["dtn_state"],
            "twin_sync_quality": decision["dtn_twin_sync_quality"],
            "ai_service_chain": decision["dtn_ai_service_chain"],
            "orchestration_mode": decision["dtn_orchestration_mode"],
            "next_best_capability": decision["dtn_next_best_capability"],
            "reasons": decision["dtn_reasons"],
        },
        "security": {
            "ai_trust_score": decision["ai_trust_score"],
            "aml_threat_level": decision["aml_threat_level"],
            "aml_threat_type": decision["aml_threat_type"],
            "guard_action": decision["security_guard_action"],
            "reasons": decision["security_guard_reasons"],
        },
        "ric_control": decision["ric_control"],
    }


if __name__ == "__main__":
    main()
