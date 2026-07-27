from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AutomationSafetyAssessment:
    score: float
    decision: str
    baseline_action: str
    baseline_would_execute: bool
    guarded_would_execute: bool
    improvement: str
    unsafe_action_prevented: bool
    evidence: list[str]


class AutomationSafetyScorer:
    """Unifies guard evidence into one operator-facing automation safety score."""

    def assess(
        self,
        *,
        action: str,
        baseline_approved: bool,
        guarded_approved: bool,
        ai_trust_score: float,
        aml_threat_level: str,
        drift_status: str,
        xapp_conflict_detected: bool,
        sla_breach_probability: float,
        timing_state: str,
        spectrum_state: str,
        policy_state: str,
        dtn_state: str,
    ) -> AutomationSafetyAssessment:
        if action == "no_action":
            return AutomationSafetyAssessment(
                score=1.0,
                decision="monitor_only",
                baseline_action="no_action",
                baseline_would_execute=False,
                guarded_would_execute=False,
                improvement="No control action needed; system remains in monitoring mode.",
                unsafe_action_prevented=False,
                evidence=["healthy_or_no_action_state"],
            )

        score = 0.62 + max(0.0, min(1.0, ai_trust_score)) * 0.22
        evidence: list[str] = [f"ai_trust={ai_trust_score:.2f}"]

        threat_penalty = {"low": 0.0, "medium": 0.12, "high": 0.28, "critical": 0.42}.get(aml_threat_level, 0.2)
        if threat_penalty:
            evidence.append(f"aml_{aml_threat_level}_penalty")
        score -= threat_penalty

        if drift_status == "drifted":
            score -= 0.22
            evidence.append("model_drift_blocks_or_escalates")
        elif drift_status == "warning":
            score -= 0.08
            evidence.append("model_drift_warning")

        if xapp_conflict_detected:
            score -= 0.1
            evidence.append("xapp_conflict_arbitrated")

        if sla_breach_probability >= 0.85:
            score -= 0.14
            evidence.append("severe_sla_breach_probability")
        elif sla_breach_probability >= 0.65:
            score -= 0.07
            evidence.append("elevated_sla_breach_probability")

        if timing_state == "timing_security_incident":
            score -= 0.2
            evidence.append("timing_security_incident")

        if spectrum_state == "spectrum_anomaly":
            score -= 0.04
            evidence.append("spectrum_dsa_required")

        if policy_state in {"policy_security_incident", "policy_quarantine"}:
            score -= 0.28
            evidence.append(policy_state)
        elif policy_state == "policy_model_lifecycle_hold":
            score -= 0.18
            evidence.append("policy_model_lifecycle_hold")
        elif policy_state == "policy_blocked":
            score -= 0.14
            evidence.append("policy_requires_review")

        if dtn_state == "security_hold":
            score -= 0.16
            evidence.append("dtn_security_hold")
        elif dtn_state == "degraded_twin":
            score -= 0.1
            evidence.append("dtn_degraded_twin")

        score = round(max(0.0, min(1.0, score)), 4)
        guarded_would_execute = bool(guarded_approved)
        baseline_would_execute = bool(baseline_approved)
        unsafe_prevented = baseline_would_execute and not guarded_would_execute

        if guarded_would_execute and score >= 0.72:
            decision = "allow_automation"
        elif guarded_would_execute:
            decision = "allow_with_monitoring"
        elif score >= 0.42:
            decision = "require_human_approval"
        else:
            decision = "block_automation"

        if unsafe_prevented:
            improvement = "Guarded loop prevented a baseline automation action that failed safety validation."
        elif guarded_would_execute and baseline_would_execute:
            improvement = "Guarded loop confirms baseline action with safety evidence."
        elif guarded_would_execute and not baseline_would_execute:
            improvement = "Guarded loop enables action after cross-checking safety evidence."
        else:
            improvement = "Both baseline and guarded loop avoid automatic execution."

        return AutomationSafetyAssessment(
            score=score,
            decision=decision,
            baseline_action="execute" if baseline_would_execute else "hold",
            baseline_would_execute=baseline_would_execute,
            guarded_would_execute=guarded_would_execute,
            improvement=improvement,
            unsafe_action_prevented=unsafe_prevented,
            evidence=evidence,
        )
