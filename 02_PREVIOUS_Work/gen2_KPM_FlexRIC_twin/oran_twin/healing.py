from __future__ import annotations

from .profiles import ServiceProfile


class HealingEngine:
    def recommend(self, root_cause: str, profile: ServiceProfile) -> tuple[str, str]:
        safety = profile.priority_weight >= 5
        if root_cause == "cell_congestion":
            if safety:
                return "prioritize_slice_and_traffic_steer", "Prioritize critical slice, steer lower-priority traffic to neighbor cells."
            return "load_balance_neighbor_cell", "Shift traffic to neighbor cell and rebalance PRB allocation."
        if root_cause == "backhaul_degradation":
            return "reroute_transport_path", "Use backup transport path and prioritize critical slice queues."
        if root_cause == "packet_loss_degradation":
            return "reroute_transport_path", "Reroute or protect the affected path to reduce packet loss and jitter."
        if root_cause == "edge_overload":
            return "mec_failover_or_scale", "Move workload to alternate MEC node or scale edge resources."
        if root_cause == "handover_instability":
            return "rrc_mobility_policy_tuning", "Tune RRC mobility thresholds, reduce ping-pong, and validate neighbor relation configuration."
        if root_cause == "qos_session_degradation":
            return "qos_flow_remap_and_session_guard", "Remap affected QoS flows, protect critical QFIs, and guard unstable sessions."
        if root_cause == "core_control_plane_degradation":
            return "amf_pdu_session_recovery_review", "Guard new session setup, review AMF/PDU-session pressure, and protect critical registration flows."
        if root_cause == "upf_user_plane_congestion":
            return "upf_scale_or_traffic_reroute", "Scale or reroute UPF user-plane traffic and protect high-priority GTP tunnels."
        if root_cause == "transport_path_degradation":
            return "reroute_transport_path", "Use backup N3/N6 transport path and prioritize affected slice traffic."
        if root_cause == "timing_drift":
            return "switch_timing_source", "Switch to stable timing source and isolate affected timing domain."
        if root_cause == "spectrum_interference":
            return "dynamic_spectrum_reassignment", "Move affected users or slice traffic to cleaner spectrum resources."
        if root_cause == "radio_link_degradation":
            return "dynamic_spectrum_reassignment", "Move affected users to a cleaner radio resource and monitor link quality."
        if root_cause == "capacity_degradation":
            return "resource_reallocation", "Reallocate resources according to service priority and SLA risk."
        if root_cause == "unknown_anomaly":
            return "human_review_guarded_mode", "Hold automation, increase monitoring, and request NOC review."
        return "no_action", "No healing action required."

    def validate(self, row: dict[str, object], root_cause: str, action: str) -> tuple[bool, float, str]:
        risk = float(row["twin_risk_score"])
        prb = float(row["prb_util_pct"])
        service = str(row["service_class"])
        if action == "no_action":
            return True, risk, "No action required."
        if action == "human_review_guarded_mode":
            return False, risk, "Guardrail blocks automatic action because RCA confidence is low."
        if action == "prioritize_slice_and_traffic_steer" and service in {"URLLC", "V2X"}:
            return True, max(0.0, risk - 0.32), "Twin validation predicts improved critical-slice continuity."
        if action == "load_balance_neighbor_cell":
            return True, max(0.0, risk - 0.22), "Twin validation predicts neighbor load balance will reduce congestion."
        if action == "reroute_transport_path":
            return True, max(0.0, risk - 0.27), "Twin validation predicts transport reroute improves delay/loss."
        if action == "mec_failover_or_scale":
            return True, max(0.0, risk - 0.28), "Twin validation predicts MEC failover/scale reduces edge delay."
        if action == "handover_parameter_tuning":
            return True, max(0.0, risk - 0.2), "Twin validation predicts lower handover failure risk."
        if action == "rrc_mobility_policy_tuning":
            return True, max(0.0, risk - 0.22), "Twin validation predicts lower RRC re-establishment and mobility ping-pong risk."
        if action == "qos_flow_remap_and_session_guard":
            return True, max(0.0, risk - 0.23), "Twin validation predicts improved QoS-flow continuity and lower session-drop risk."
        if action == "amf_pdu_session_recovery_review":
            return False, risk, "Core control-plane recovery requires SMO/NOC approval before automation."
        if action == "upf_scale_or_traffic_reroute":
            return True, max(0.0, risk - 0.26), "Twin validation predicts UPF scaling or user-plane reroute reduces packet loss and RTT."
        if action == "switch_timing_source":
            return True, max(0.0, risk - 0.24), "Twin validation predicts jitter and BLER reduction."
        if action in {"rebalance_spectrum_and_interference_watch", "dynamic_spectrum_reassignment"}:
            return True, max(0.0, risk - 0.21), "Twin validation predicts improved radio quality and resource stability."
        if action == "resource_reallocation":
            return True, max(0.0, risk - 0.18), "Twin validation predicts SLA improvement from resource reallocation."
        return False, risk, "Twin validation rejected action due to unsafe or unclear impact."
