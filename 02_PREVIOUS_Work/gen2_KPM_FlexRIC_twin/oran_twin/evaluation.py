from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path


def evaluate(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    true_faults = [row for row in rows if _bool(row["fault_active"])]
    normal = [row for row in rows if not _bool(row["fault_active"]) and not _bool(row.get("aml_attack_active", False))]
    predicted_faults = [row for row in rows if _bool(row["anomaly_detected"]) or _bool(row["sla_violation"])]
    true_positive = [row for row in true_faults if row in predicted_faults]
    false_positive = [row for row in normal if row in predicted_faults]
    false_negative = [row for row in true_faults if row not in predicted_faults]

    approved_actions = [row for row in rows if _bool(row["action_approved_by_twin"]) and row["healing_action"] != "no_action"]
    blocked_actions = [row for row in rows if not _bool(row["action_approved_by_twin"]) and row["healing_action"] != "no_action"]
    actionable_faults = [row for row in true_faults if row["root_cause"] not in {"normal", "unknown_anomaly"}]
    correct_rca = [
        row
        for row in actionable_faults
        if str(row["fault_type"]).split("+", 1)[0] == str(row["root_cause"])
        or _compatible_fault(str(row["fault_type"]), str(row["root_cause"]))
    ]
    risk_reductions = [
        max(0.0, float(row["twin_risk_score"]) - float(row["post_action_risk_score"]))
        for row in approved_actions
    ]
    conflicts = [row for row in rows if _bool(row["xapp_conflict_detected"])]
    drifted = [row for row in rows if row["drift_status"] == "drifted"]
    aml_medium_plus = [row for row in rows if row["aml_threat_level"] in {"medium", "high", "critical"}]
    aml_attacks = [row for row in rows if _bool(row.get("aml_attack_active", False))]
    guarded_attacks = [row for row in aml_attacks if row["aml_threat_level"] in {"medium", "high", "critical"}]
    severe_sla = [row for row in rows if row["sla_impact_level"] == "severe"]
    predicted_sla_breaches = [row for row in rows if float(row["sla_breach_probability"]) >= 0.65]
    timing_incidents = [row for row in rows if row["timing_state"] == "timing_security_incident"]
    spectrum_anomalies = [row for row in rows if row["spectrum_state"] == "spectrum_anomaly"]
    control_rows = [row for row in rows if row["healing_action"] != "no_action"]
    baseline_execute = [row for row in control_rows if _bool(row["automation_baseline_would_execute"])]
    guarded_execute = [row for row in control_rows if _bool(row["automation_guarded_would_execute"])]
    unsafe_prevented = [row for row in control_rows if _bool(row["unsafe_action_prevented"])]
    safety_scores = [float(row["automation_safety_score"]) for row in control_rows]
    self_learning_anomalies = [row for row in rows if _bool(row.get("self_learning_anomaly_detected", False))]
    self_learning_scores = [float(row.get("self_learning_anomaly_score", 0.0)) for row in rows]
    learned_rca_rows = [
        row
        for row in actionable_faults
        if str(row.get("self_learning_rca_prediction", "unknown")) not in {"unknown", "normal"}
    ]
    learned_rca_correct = [
        row
        for row in learned_rca_rows
        if str(row["fault_type"]).split("+", 1)[0] == str(row.get("self_learning_rca_prediction"))
        or _compatible_fault(str(row["fault_type"]), str(row.get("self_learning_rca_prediction")))
    ]

    by_service = defaultdict(lambda: {"records": 0, "faults": 0, "detected_faults": 0, "false_positives": 0})
    for row in rows:
        item = by_service[str(row["service_class"])]
        item["records"] += 1
        item["faults"] += int(_bool(row["fault_active"]))
        item["detected_faults"] += int(_bool(row["fault_active"]) and row in predicted_faults)
        item["false_positives"] += int(not _bool(row["fault_active"]) and row in predicted_faults)

    precision = _ratio(len(true_positive), len(predicted_faults))
    recall = _ratio(len(true_positive), len(true_faults))
    return {
        "records": total,
        "fault_detection": {
            "true_positives": len(true_positive),
            "false_positives": len(false_positive),
            "false_negatives": len(false_negative),
            "precision": precision,
            "recall": recall,
            "f1_score": _f1(precision, recall),
            "false_positive_rate": _ratio(len(false_positive), len(normal)),
        },
        "root_cause": {
            "actionable_fault_records": len(actionable_faults),
            "correct_rca_records": len(correct_rca),
            "root_cause_accuracy_on_actionable_faults": _ratio(len(correct_rca), len(actionable_faults)),
            "root_causes": dict(Counter(str(row["root_cause"]) for row in predicted_faults)),
        },
        "healing": {
            "approved_actions": len(approved_actions),
            "blocked_actions": len(blocked_actions),
            "approval_rate_for_recommended_actions": _ratio(len(approved_actions), len(approved_actions) + len(blocked_actions)),
            "mean_predicted_risk_reduction": round(sum(risk_reductions) / max(1, len(risk_reductions)), 4),
            "actions": dict(Counter(str(row["healing_action"]) for row in predicted_faults)),
        },
        "automation_safety": {
            "control_action_records": len(control_rows),
            "baseline_executable_actions": len(baseline_execute),
            "guarded_executable_actions": len(guarded_execute),
            "unsafe_actions_prevented": len(unsafe_prevented),
            "unsafe_prevention_rate_vs_baseline": _ratio(len(unsafe_prevented), len(baseline_execute)),
            "mean_automation_safety_score": round(sum(safety_scores) / max(1, len(safety_scores)), 4),
            "safety_decisions": dict(Counter(str(row["automation_safety_decision"]) for row in rows)),
        },
        "self_learning": {
            "model_type": "online_self_learning_v1",
            "features": 10,
            "anomaly_records": len(self_learning_anomalies),
            "mean_anomaly_score": round(sum(self_learning_scores) / max(1, len(self_learning_scores)), 4),
            "learning_modes": dict(Counter(str(row.get("self_learning_mode", "unknown")) for row in rows)),
            "rca_prediction_records": len(learned_rca_rows),
            "rca_correct_records": len(learned_rca_correct),
            "rca_accuracy_on_prediction_records": _ratio(len(learned_rca_correct), len(learned_rca_rows)),
            "rca_predictions": dict(
                Counter(
                    str(row.get("self_learning_rca_prediction"))
                    for row in rows
                    if str(row.get("self_learning_rca_prediction", "unknown")) not in {"unknown", "normal"}
                )
            ),
        },
        "guards": {
            "drifted_records": len(drifted),
            "aml_medium_plus_records": len(aml_medium_plus),
            "aml_attack_records": len(aml_attacks),
            "aml_attacks_guarded": len(guarded_attacks),
            "aml_attack_guard_rate": _ratio(len(guarded_attacks), len(aml_attacks)),
            "aml_attack_types_injected": dict(Counter(str(row["aml_attack_type"]) for row in aml_attacks)),
            "xapp_conflict_records": len(conflicts),
            "xapp_conflict_types": dict(Counter(str(row["xapp_conflict_type"]) for row in conflicts)),
            "xapp_mitigation_strategies": dict(Counter(str(row["xapp_mitigation_strategy"]) for row in rows)),
            "xapp_selected": dict(Counter(str(row["xapp_selected"]) for row in rows)),
            "security_guard_actions": dict(Counter(str(row["security_guard_action"]) for row in rows)),
            "severe_sla_impact_records": len(severe_sla),
            "predicted_sla_breach_records": len(predicted_sla_breaches),
            "slice_affected_domains": dict(Counter(str(row["slice_affected_domain"]) for row in rows)),
            "recommended_slice_actions": dict(Counter(str(row["recommended_slice_action"]) for row in rows)),
            "timing_security_incidents": len(timing_incidents),
            "timing_sync_states": dict(Counter(str(row["timing_sync_state"]) for row in rows)),
            "timing_stride_test_cases": dict(Counter(str(row["timing_stride_test_case"]) for row in rows)),
            "spectrum_anomaly_records": len(spectrum_anomalies),
            "spectrum_states": dict(Counter(str(row["spectrum_state"]) for row in rows)),
            "spectrum_dsa_policies": dict(Counter(str(row["spectrum_dsa_policy"]) for row in rows)),
            "spectrum_interference_sources": dict(Counter(str(row["spectrum_interference_source"]) for row in rows)),
            "policy_states": dict(Counter(str(row["policy_state"]) for row in rows)),
            "policy_workflow_stages": dict(Counter(str(row["policy_zsm_workflow_stage"]) for row in rows)),
            "policy_escalation_levels": dict(Counter(str(row["policy_escalation_level"]) for row in rows)),
            "dtn_states": dict(Counter(str(row["dtn_state"]) for row in rows)),
            "dtn_orchestration_modes": dict(Counter(str(row["dtn_orchestration_mode"]) for row in rows)),
            "dtn_twin_sync_quality": dict(Counter(str(row["dtn_twin_sync_quality"]) for row in rows)),
        },
        "by_service": dict(by_service),
        "quality_verdict": _verdict(precision, recall, _ratio(len(false_positive), len(normal))),
    }


def write_evaluation_report(metrics: dict[str, object], path: Path) -> None:
    fd = metrics["fault_detection"]
    rca = metrics["root_cause"]
    healing = metrics["healing"]
    automation = metrics["automation_safety"]
    self_learning = metrics["self_learning"]
    guards = metrics["guards"]
    report = f"""# Experiment Evaluation Report

## Verdict

{metrics['quality_verdict']}

## Fault Detection

| Metric | Value |
|---|---:|
| True positives | {fd['true_positives']} |
| False positives | {fd['false_positives']} |
| False negatives | {fd['false_negatives']} |
| Precision | {fd['precision']} |
| Recall | {fd['recall']} |
| F1-score | {fd['f1_score']} |
| False positive rate | {fd['false_positive_rate']} |

## Root Cause Analysis

| Metric | Value |
|---|---:|
| Actionable fault records | {rca['actionable_fault_records']} |
| Correct RCA records | {rca['correct_rca_records']} |
| RCA accuracy on actionable faults | {rca['root_cause_accuracy_on_actionable_faults']} |

## Healing

| Metric | Value |
|---|---:|
| Approved actions | {healing['approved_actions']} |
| Blocked actions | {healing['blocked_actions']} |
| Approval rate for recommended actions | {healing['approval_rate_for_recommended_actions']} |
| Mean predicted risk reduction | {healing['mean_predicted_risk_reduction']} |

## Baseline vs Guarded Automation

| Metric | Value |
|---|---:|
| Control action records | {automation['control_action_records']} |
| Baseline executable actions | {automation['baseline_executable_actions']} |
| Guarded executable actions | {automation['guarded_executable_actions']} |
| Unsafe baseline actions prevented | {automation['unsafe_actions_prevented']} |
| Unsafe prevention rate vs baseline | {automation['unsafe_prevention_rate_vs_baseline']} |
| Mean automation safety score | {automation['mean_automation_safety_score']} |
| Safety decisions | {automation['safety_decisions']} |

## Online Self-Learning Model

| Metric | Value |
|---|---:|
| Model type | {self_learning['model_type']} |
| KPI features used | {self_learning['features']} |
| Self-learning anomaly records | {self_learning['anomaly_records']} |
| Mean self-learning anomaly score | {self_learning['mean_anomaly_score']} |
| Learning modes | {self_learning['learning_modes']} |
| Learned RCA prediction records | {self_learning['rca_prediction_records']} |
| Learned RCA correct records | {self_learning['rca_correct_records']} |
| Learned RCA accuracy on prediction records | {self_learning['rca_accuracy_on_prediction_records']} |
| Learned RCA predictions | {self_learning['rca_predictions']} |

## Safety Guards

| Metric | Value |
|---|---:|
| Drifted records | {guards['drifted_records']} |
| AML medium+ records | {guards['aml_medium_plus_records']} |
| Injected AML attack records | {guards['aml_attack_records']} |
| Injected AML attacks guarded | {guards['aml_attacks_guarded']} |
| AML attack guard rate | {guards['aml_attack_guard_rate']} |
| xApp conflict records | {guards['xapp_conflict_records']} |
| xApp mitigation strategies | {guards['xapp_mitigation_strategies']} |
| Severe SLA impact records | {guards['severe_sla_impact_records']} |
| Predicted SLA breach records | {guards['predicted_sla_breach_records']} |
| Timing security incidents | {guards['timing_security_incidents']} |
| Timing sync states | {guards['timing_sync_states']} |
| Policy workflow stages | {guards['policy_workflow_stages']} |
| DTN states | {guards['dtn_states']} |
| DTN orchestration modes | {guards['dtn_orchestration_modes']} |
| Spectrum anomaly records | {guards['spectrum_anomaly_records']} |
| Spectrum DSA policies | {guards['spectrum_dsa_policies']} |

## Interpretation

This report evaluates the current prototype as a closed-loop self-healing system. High recall means faults are usually detected. Precision and false-positive rate indicate how noisy the detector is. RCA accuracy measures whether the inferred cause matches injected fault labels when a specific cause is available. Healing metrics show how often the system approves recovery and the expected risk reduction after validation. The baseline-vs-guarded section measures the project novelty: how many actions a plain self-healing loop would execute versus how many the guarded O-RAN safety layer allows after checking AML, drift, xApp conflicts, SLA, timing, spectrum, policy, and DTN state.
"""
    path.write_text(report, encoding="utf-8")


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _ratio(num: int, den: int) -> float:
    return round(num / max(1, den), 4)


def _f1(precision: float, recall: float) -> float:
    return round(2 * precision * recall / max(0.0001, precision + recall), 4)


def _compatible_fault(fault_type: str, root_cause: str) -> bool:
    if root_cause == "capacity_degradation" and fault_type in {"cell_congestion", "backhaul_degradation"}:
        return True
    return False


def _verdict(precision: float, recall: float, false_positive_rate: float) -> str:
    if recall >= 0.9 and precision >= 0.75 and false_positive_rate <= 0.08:
        return "Good MVP result: high recall, acceptable precision, and controlled false-positive rate."
    if recall >= 0.85 and false_positive_rate <= 0.12:
        return "Usable prototype result: detection is strong, but precision or false positives need tuning."
    return "Needs tuning before presentation: detection quality or false positives are not stable enough."
