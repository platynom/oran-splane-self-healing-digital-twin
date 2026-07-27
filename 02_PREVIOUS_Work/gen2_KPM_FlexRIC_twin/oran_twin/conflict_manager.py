from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Paths, load_json


@dataclass(frozen=True)
class XAppProposal:
    name: str
    action: str
    control_parameter: str
    objective: str
    priority: int
    confidence: float
    reason: str
    distillation_score: float = 0.0


@dataclass(frozen=True)
class ConflictAssessment:
    conflict_detected: bool
    conflict_type: str
    selected_action: str
    selected_xapp: str
    mitigation_strategy: str
    distillation_state: str
    replay_record: dict[str, object]
    proposals: list[XAppProposal]
    control_loop_latency_ms: float
    cooldown_state: str
    reasons: list[str]


class XAppConflictManager:
    """MVP xApp action arbitration inspired by xApp distillation/conflict mitigation."""

    def __init__(self, policy_path: Path | None = None) -> None:
        policy = load_json(policy_path or (Paths.configs / "xapp_distillation_policy.json"))
        self.teacher_weights: dict[str, float] = {
            str(key): float(value) for key, value in policy["teacher_weights"].items()
        }
        self.objective_weights: dict[str, float] = {
            str(key): float(value) for key, value in policy["objective_weights"].items()
        }
        self.conflict_penalties: dict[str, float] = {
            str(key): float(value) for key, value in policy["conflict_penalties"].items()
        }
        self.control_parameters: dict[str, dict[str, float]] = {
            str(key): {str(inner_key): float(inner_value) for inner_key, inner_value in dict(value).items()}
            for key, value in dict(policy.get("control_parameters", {})).items()
        }
        self.replay_buffer: list[dict[str, object]] = []
        self.last_control_step: dict[tuple[str, str], int] = {}
        self.step = 0

    def propose(
        self,
        *,
        row: dict[str, object],
        root_cause: str,
        primary_action: str,
        profile_priority: int,
        risk_score: float,
    ) -> ConflictAssessment:
        self.step += 1
        proposals = self._teacher_xapp_proposals(row, root_cause, primary_action, profile_priority, risk_score)
        state = self._state_bucket(row=row, risk_score=risk_score, profile_priority=profile_priority)
        base_conflicts = self._detect_conflicts(proposals)
        latency_by_action = {proposal.action: self._estimate_control_latency_ms(proposal, row, risk_score) for proposal in proposals}
        conflicts = self._add_runtime_conflicts(
            proposals=proposals,
            base_conflicts=base_conflicts,
            row=row,
            latency_by_action=latency_by_action,
        )
        distilled = self._score_distilled_policy(proposals, conflicts, state, profile_priority)
        selected = self._select_distilled_action(distilled, conflicts, profile_priority)
        selected_latency = round(latency_by_action.get(selected.action, self._estimate_control_latency_ms(selected, row, risk_score)), 2)
        cooldown_state = self._cooldown_state(selected, row)
        strategy = "no_conflict"
        if conflicts:
            strategy = "teacher_student_distillation"
        self._record_control(selected, row)
        replay_record = self._record_replay(
            state=state,
            selected=selected,
            proposals=distilled,
            conflicts=conflicts,
            risk_score=risk_score,
            control_loop_latency_ms=selected_latency,
            cooldown_state=cooldown_state,
        )
        return ConflictAssessment(
            conflict_detected=bool(conflicts),
            conflict_type="+".join(sorted(set(conflicts))) if conflicts else "none",
            selected_action=selected.action,
            selected_xapp=selected.name,
            mitigation_strategy=strategy,
            distillation_state=state,
            replay_record=replay_record,
            proposals=distilled,
            control_loop_latency_ms=selected_latency,
            cooldown_state=cooldown_state,
            reasons=conflicts or ["single_or_compatible_xapp_action"],
        )

    def _teacher_xapp_proposals(
        self,
        row: dict[str, object],
        root_cause: str,
        primary_action: str,
        profile_priority: int,
        risk_score: float,
    ) -> list[XAppProposal]:
        proposals = [
            XAppProposal(
                name="self_healing_xapp",
                action=primary_action,
                control_parameter=self._control_parameter(primary_action),
                objective="restore_sla",
                priority=90 if profile_priority >= 5 else 70,
                confidence=min(0.98, 0.55 + risk_score * 0.4),
                reason=f"RCA selected {root_cause}.",
            )
        ]
        if primary_action == "no_action" and root_cause == "normal":
            return proposals
        if primary_action == "human_review_guarded_mode":
            return proposals

        prb = float(row["prb_util_pct"])
        throughput = float(row["throughput_mbps"])
        latency = float(row["latency_ms"])
        handover = float(row["handover_fail_pct"])
        sinr = float(row["sinr_db"])
        bler = float(row["bler_pct"])

        if root_cause == "spectrum_interference" or (sinr < 10.5 and bler > 3.2):
            proposals.append(
                XAppProposal(
                    "spectrum_monitor_xapp",
                    "dynamic_spectrum_reassignment",
                    "spectrum_radio_resources",
                    "restore_radio_quality",
                    82,
                    min(0.97, 0.58 + max(0.0, 12 - sinr) / 12 + min(0.18, bler / 40)),
                    "Low SINR and elevated BLER indicate spectrum/access anomaly.",
                )
            )

        if prb > 82:
            proposals.append(
                XAppProposal(
                    "traffic_steering_xapp",
                    "load_balance_neighbor_cell",
                    "cell_user_distribution",
                    "reduce_cell_load",
                    75,
                    min(0.96, 0.5 + (prb - 82) / 30),
                    "High PRB utilization indicates load steering benefit.",
                )
            )
        if throughput < 60 and prb < 70:
            proposals.append(
                XAppProposal(
                    "resource_allocation_xapp",
                    "resource_reallocation",
                    "radio_resource_blocks",
                    "increase_throughput",
                    68,
                    0.72,
                    "Throughput is weak without severe PRB saturation.",
                )
            )
        if handover > 4.5:
            proposals.append(
                XAppProposal(
                    "handover_optimization_xapp",
                    "rrc_mobility_policy_tuning",
                    "rrc_mobility_policy",
                    "reduce_handover_failures",
                    72,
                    min(0.95, 0.55 + handover / 12),
                    "Handover failure rate is elevated.",
                )
            )
        sdap_drop = float(row.get("sdap_qos_flow_drop_pct", 0.0))
        qfi_violation = float(row.get("qfi_violation_pct", 0.0))
        session_drop = float(row.get("session_drop_rate_pct", 0.0))
        upf_cpu = float(row.get("upf_cpu_util_pct", 0.0))
        gtp_loss = float(row.get("gtp_tunnel_loss_pct", 0.0))
        n3_rtt = float(row.get("n3_rtt_ms", 0.0))
        n6_rtt = float(row.get("n6_internet_rtt_ms", 0.0))
        pdu_fail = float(row.get("pdu_session_fail_pct", 0.0))
        amf_delay = float(row.get("amf_paging_delay_ms", 0.0))
        if root_cause == "qos_session_degradation" or sdap_drop > 4 or qfi_violation > 6 or session_drop > 3:
            proposals.append(
                XAppProposal(
                    "qos_assurance_xapp",
                    "qos_flow_remap_and_session_guard",
                    "qos_flow_mapping",
                    "protect_qos_sessions",
                    86 if profile_priority >= 5 else 74,
                    min(0.96, 0.58 + min(0.26, (sdap_drop + qfi_violation + session_drop) / 45)),
                    "O-CU QoS/session indicators show flow or session degradation.",
                )
            )
        if root_cause in {"upf_user_plane_congestion", "transport_path_degradation"} or upf_cpu > 82 or gtp_loss > 2.5 or n3_rtt > 45 or n6_rtt > 90:
            proposals.append(
                XAppProposal(
                    "core_transport_assurance_xapp",
                    "upf_scale_or_traffic_reroute",
                    "upf_user_plane",
                    "protect_core_user_plane",
                    83 if profile_priority >= 5 else 72,
                    min(0.96, 0.56 + min(0.28, (max(0.0, upf_cpu - 75) + gtp_loss * 8 + max(0.0, n3_rtt - 30) * 0.4) / 100)),
                    "UPF, GTP, or transport metrics indicate core user-plane degradation.",
                )
            )
        if root_cause == "core_control_plane_degradation" or pdu_fail > 3 or amf_delay > 80:
            proposals.append(
                XAppProposal(
                    "core_control_assurance_xapp",
                    "amf_pdu_session_recovery_review",
                    "core_control_plane",
                    "protect_core_sessions",
                    88 if profile_priority >= 5 else 78,
                    min(0.96, 0.58 + min(0.28, pdu_fail / 18 + max(0.0, amf_delay - 60) / 260)),
                    "AMF/PDU session indicators show control-plane setup risk.",
                )
            )
        if latency < 25 and prb < 55 and risk_score < 0.35:
            proposals.append(
                XAppProposal(
                    "energy_saving_xapp",
                    "energy_saving_guarded_mode",
                    "cell_power_state",
                    "reduce_energy_cost",
                    45,
                    0.66,
                    "Low-risk state may allow guarded energy saving.",
                )
            )

        return proposals

    @staticmethod
    def _detect_conflicts(proposals: list[XAppProposal]) -> list[str]:
        conflicts: list[str] = []
        by_parameter: dict[str, set[str]] = {}
        by_objective: dict[str, set[str]] = {}
        for proposal in proposals:
            by_parameter.setdefault(proposal.control_parameter, set()).add(proposal.action)
            by_objective.setdefault(proposal.objective, set()).add(proposal.control_parameter)
        if any(len(actions) > 1 for actions in by_parameter.values()):
            conflicts.append("direct_control_conflict")
        if "reduce_energy_cost" in by_objective and any(
            objective in by_objective for objective in {"restore_sla", "increase_throughput", "reduce_cell_load"}
        ):
            conflicts.append("indirect_objective_conflict")
        if len({proposal.control_parameter for proposal in proposals}) > 2 and len(proposals) > 2:
            conflicts.append("multi_xapp_coordination_risk")
        return conflicts

    @staticmethod
    def _select_distilled_action(
        proposals: list[XAppProposal],
        conflicts: list[str],
        profile_priority: int,
    ) -> XAppProposal:
        if not conflicts:
            return max(proposals, key=lambda item: (item.distillation_score, item.priority, item.confidence))
        candidates = proposals
        if profile_priority >= 5:
            candidates = [proposal for proposal in proposals if proposal.objective != "reduce_energy_cost"] or proposals
        return max(candidates, key=lambda item: (item.distillation_score, item.priority, item.confidence))

    def _score_distilled_policy(
        self,
        proposals: list[XAppProposal],
        conflicts: list[str],
        state: str,
        profile_priority: int,
    ) -> list[XAppProposal]:
        conflict_penalty = sum(self.conflict_penalties.get(conflict, 0.0) for conflict in conflicts)
        scored: list[XAppProposal] = []
        for proposal in proposals:
            teacher_weight = self.teacher_weights.get(proposal.name, 0.75)
            objective_weight = self.objective_weights.get(proposal.objective, 0.7)
            priority_score = proposal.priority / 100.0
            critical_bonus = 0.07 if profile_priority >= 5 and proposal.objective != "reduce_energy_cost" else 0.0
            low_risk_penalty = 0.14 if "low_risk" in state and proposal.action != "no_action" else 0.0
            manual_review_bonus = 0.08 if proposal.action == "human_review_guarded_mode" and conflicts else 0.0
            score = (
                proposal.confidence * 0.34
                + priority_score * 0.24
                + teacher_weight * 0.18
                + objective_weight * 0.16
                + critical_bonus
                + manual_review_bonus
                - conflict_penalty
                - low_risk_penalty
            )
            scored.append(
                XAppProposal(
                    name=proposal.name,
                    action=proposal.action,
                    control_parameter=proposal.control_parameter,
                    objective=proposal.objective,
                    priority=proposal.priority,
                    confidence=proposal.confidence,
                    reason=proposal.reason,
                    distillation_score=round(max(0.0, min(1.0, score)), 4),
                )
            )
        return scored

    def _add_runtime_conflicts(
        self,
        *,
        proposals: list[XAppProposal],
        base_conflicts: list[str],
        row: dict[str, object],
        latency_by_action: dict[str, float],
    ) -> list[str]:
        conflicts = list(base_conflicts)
        for proposal in proposals:
            if self._cooldown_state(proposal, row) == "cooldown_active":
                conflicts.append("cooldown_violation_risk")
            max_latency = self.control_parameters.get(proposal.control_parameter, {}).get("max_latency_ms", 1000.0)
            if max_latency and latency_by_action.get(proposal.action, 0.0) > max_latency:
                conflicts.append("control_loop_latency_risk")
        return sorted(set(conflicts))

    def _estimate_control_latency_ms(self, proposal: XAppProposal, row: dict[str, object], risk_score: float) -> float:
        base = 120.0
        if proposal.control_parameter in {"cell_user_distribution", "radio_resource_blocks", "handover_thresholds"}:
            base = 260.0
        elif proposal.control_parameter in {"spectrum_radio_resources", "timing_source"}:
            base = 430.0
        elif proposal.control_parameter in {"qos_flow_mapping", "rrc_mobility_policy"}:
            base = 210.0
        elif proposal.control_parameter in {"upf_user_plane", "core_control_plane"}:
            base = 640.0
        elif proposal.control_parameter in {"edge_workload_placement", "transport_path"}:
            base = 520.0
        proposals_seen = max(1, len(self.replay_buffer[-20:]))
        prb = float(row.get("prb_util_pct", 0.0))
        latency = base + risk_score * 180.0 + max(0.0, prb - 70.0) * 5.0 + min(80.0, proposals_seen * 1.5)
        return round(latency, 2)

    def _cooldown_state(self, proposal: XAppProposal, row: dict[str, object]) -> str:
        cooldown = int(self.control_parameters.get(proposal.control_parameter, {}).get("cooldown_steps", 0.0))
        if cooldown <= 0:
            return "not_applicable"
        key = (str(row.get("cell_id", "unknown")), proposal.control_parameter)
        last_step = self.last_control_step.get(key)
        if last_step is not None and self.step - last_step <= cooldown:
            return "cooldown_active"
        return "cooldown_clear"

    def _record_control(self, selected: XAppProposal, row: dict[str, object]) -> None:
        if selected.control_parameter in {"none", "guarded_manual_review"}:
            return
        key = (str(row.get("cell_id", "unknown")), selected.control_parameter)
        self.last_control_step[key] = self.step

    def _record_replay(
        self,
        *,
        state: str,
        selected: XAppProposal,
        proposals: list[XAppProposal],
        conflicts: list[str],
        risk_score: float,
        control_loop_latency_ms: float,
        cooldown_state: str,
    ) -> dict[str, object]:
        record = {
            "state": state,
            "selected_xapp": selected.name,
            "selected_action": selected.action,
            "selected_score": selected.distillation_score,
            "teacher_count": len(proposals),
            "conflict_count": len(conflicts),
            "risk_score": round(risk_score, 4),
            "control_loop_latency_ms": control_loop_latency_ms,
            "cooldown_state": cooldown_state,
        }
        self.replay_buffer.append(record)
        self.replay_buffer = self.replay_buffer[-500:]
        return record

    @staticmethod
    def _state_bucket(*, row: dict[str, object], risk_score: float, profile_priority: int) -> str:
        prb = float(row["prb_util_pct"])
        throughput = float(row["throughput_mbps"])
        handover = float(row["handover_fail_pct"])
        sinr = float(row["sinr_db"])
        risk = "high_risk" if risk_score >= 0.62 else "mid_risk" if risk_score >= 0.35 else "low_risk"
        priority = "critical_slice" if profile_priority >= 5 else "standard_slice"
        radio = "radio_stressed" if prb > 82 or sinr < 10.5 else "radio_normal"
        mobility = "mobility_stressed" if handover > 4.5 else "mobility_normal"
        capacity = "capacity_stressed" if throughput < 60 else "capacity_normal"
        return f"{risk}:{priority}:{radio}:{mobility}:{capacity}"

    @staticmethod
    def _control_parameter(action: str) -> str:
        mapping = {
            "load_balance_neighbor_cell": "cell_user_distribution",
            "prioritize_slice_and_traffic_steer": "cell_user_distribution",
            "resource_reallocation": "radio_resource_blocks",
            "handover_parameter_tuning": "handover_thresholds",
            "rrc_mobility_policy_tuning": "rrc_mobility_policy",
            "qos_flow_remap_and_session_guard": "qos_flow_mapping",
            "amf_pdu_session_recovery_review": "core_control_plane",
            "upf_scale_or_traffic_reroute": "upf_user_plane",
            "reroute_transport_path": "transport_path",
            "mec_failover_or_scale": "edge_workload_placement",
            "switch_timing_source": "timing_source",
            "rebalance_spectrum_and_interference_watch": "spectrum_radio_resources",
            "dynamic_spectrum_reassignment": "spectrum_radio_resources",
            "no_action": "none",
        }
        return mapping.get(action, "guarded_manual_review")
