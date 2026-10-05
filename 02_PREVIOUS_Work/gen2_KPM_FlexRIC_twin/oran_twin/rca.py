from __future__ import annotations


class RootCauseAnalyzer:
    def infer(self, row: dict[str, object], twin_reasons: list[str], anomaly_reasons: list[str]) -> tuple[str, str]:
        latency = float(row["latency_ms"])
        jitter = float(row["jitter_ms"])
        prb = float(row["prb_util_pct"])
        handover = float(row["handover_fail_pct"])
        edge = float(row["edge_delay_ms"])
        backhaul = float(row["backhaul_delay_ms"])
        loss = float(row["packet_loss_pct"])
        bler = float(row["bler_pct"])
        rsrp = float(row.get("rsrp_dbm", 0.0))
        rsrq = float(row.get("rsrq_db", 0.0))
        evm = float(row.get("evm_pct", 0.0))
        interference_power = float(row.get("interference_power_dbm", -120.0))
        beam_misalignment = float(row.get("beam_misalignment_deg", 0.0))
        antenna_vswr = float(row.get("antenna_vswr", 1.1))
        rf_temperature = float(row.get("rf_temperature_c", 42.0))
        rrc_setup_fail = float(row.get("rrc_setup_fail_pct", 0.0))
        rrc_reestab = float(row.get("rrc_reestab_rate_pct", 0.0))
        pdcp_discard = float(row.get("pdcp_discard_rate_pct", 0.0))
        pdcp_reorder = float(row.get("pdcp_reordering_delay_ms", 0.0))
        sdap_drop = float(row.get("sdap_qos_flow_drop_pct", 0.0))
        qfi_violation = float(row.get("qfi_violation_pct", 0.0))
        session_drop = float(row.get("session_drop_rate_pct", 0.0))
        mobility_pingpong = float(row.get("mobility_pingpong_pct", 0.0))
        amf_fail = float(row.get("amf_registration_fail_pct", 0.0))
        amf_paging = float(row.get("amf_paging_delay_ms", 0.0))
        pdu_setup = float(row.get("pdu_session_setup_ms", 0.0))
        pdu_fail = float(row.get("pdu_session_fail_pct", 0.0))
        upf_cpu = float(row.get("upf_cpu_util_pct", 0.0))
        upf_drop = float(row.get("upf_packet_drop_pct", 0.0))
        gtp_loss = float(row.get("gtp_tunnel_loss_pct", 0.0))
        n3_rtt = float(row.get("n3_rtt_ms", 0.0))
        n6_rtt = float(row.get("n6_internet_rtt_ms", 0.0))
        transport_jitter = float(row.get("transport_jitter_ms", 0.0))

        if "amf_or_pdu_session_control_plane_pressure" in anomaly_reasons or (
            amf_fail > 3 or amf_paging > 80 or pdu_fail > 3 or pdu_setup > 180
        ):
            return "core_control_plane_degradation", "AMF or PDU session setup metrics indicate 5G core control-plane degradation."
        if "upf_or_gtp_user_plane_pressure" in anomaly_reasons or (
            upf_cpu > 82 or upf_drop > 3 or gtp_loss > 2.5 or n3_rtt > 45
        ):
            return "upf_user_plane_congestion", "UPF, GTP, or N3 metrics indicate 5G core user-plane congestion."
        if "n3_n6_transport_path_pressure" in anomaly_reasons or (
            n6_rtt > 90 or transport_jitter > 18 or (n3_rtt > 35 and gtp_loss > 1.5)
        ):
            return "transport_path_degradation", "N3/N6 RTT, tunnel loss, or transport jitter indicate end-to-end transport path degradation."
        if "signature_ocu_qos_session_degradation" in anomaly_reasons or (
            sdap_drop > 4 or qfi_violation > 6 or session_drop > 3
        ):
            return "qos_session_degradation", "O-CU SDAP/QoS/session indicators show QoS flow or session degradation."
        if "signature_ocu_pdcp_user_plane_degradation" in anomaly_reasons or (pdcp_discard > 4 and pdcp_reorder > 8):
            return "qos_session_degradation", "O-CU PDCP discard and reordering delay indicate user-plane session degradation."
        if "signature_ocu_mobility_control_instability" in anomaly_reasons or (
            mobility_pingpong > 5 or rrc_reestab > 4 or (rrc_setup_fail > 5 and handover > 3)
        ):
            return "handover_instability", "O-CU RRC mobility indicators show ping-pong, re-establishment, or setup failure instability."
        if "signature_oru_rf_chain_degradation" in anomaly_reasons or antenna_vswr > 2.1 or rf_temperature > 78:
            return "radio_quality_degradation", "O-RU RF chain indicators such as VSWR or RF temperature show radio hardware/path degradation."
        if "signature_oru_beam_misalignment" in anomaly_reasons or (beam_misalignment > 18 and rsrp < -105):
            return "spectrum_interference", "Beam quality and RSRP indicate O-RU beam misalignment or blockage."
        if "signature_oru_external_interference" in anomaly_reasons or (interference_power > -78 and rsrq < -15 and evm > 8):
            return "spectrum_interference", "O-RU RF indicators show external or co-channel interference."
        if "signature_radio_link_degradation" in anomaly_reasons or (bler > 6 and loss > 1):
            return "radio_link_degradation", "Low radio quality indicators show link degradation."
        if prb > 88 or (prb > 80 and ("latency_above_target" in twin_reasons or "throughput_below_target" in twin_reasons)):
            return "cell_congestion", "High PRB utilization and latency indicate radio/cell overload."
        if (
            "low_sinr_high_bler_signature" in anomaly_reasons
            or "interference_like_quality_drop" in anomaly_reasons
            or "spectrum_resource_saturation" in anomaly_reasons
        ):
            return "spectrum_interference", "SINR, BLER and resource pressure indicate radio/spectrum abnormality."
        if "signature_packet_loss_degradation" in anomaly_reasons or (loss > 3 and jitter > 6 and backhaul <= 12):
            return "packet_loss_degradation", "Packet loss and jitter are elevated without a stronger backhaul-delay signature."
        if backhaul > 12 and (latency > 10 or loss > 0.2):
            return "backhaul_degradation", "Backhaul delay and packet loss indicate transport degradation."
        if edge > 10 and latency > 8:
            return "edge_overload", "MEC processing delay is above expected range for edge-dependent services."
        if handover > 5:
            return "handover_instability", "Handover failure rate is elevated for the service mobility profile."
        if jitter > 8 and bler > 3:
            return "timing_drift", "Jitter and BLER increase indicate possible timing/synchronization issue."
        if "throughput_below_target" in twin_reasons:
            return "capacity_degradation", "Throughput is below service target without a stronger root-cause signal."
        if anomaly_reasons or twin_reasons:
            return "unknown_anomaly", "Anomaly detector found KPI deviation but RCA confidence is limited."
        return "normal", "No strong fault signature."
