from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "dataset_template_precise"


MAIN_KPI_COLUMNS = [
    "timestamp",
    "window_sec",
    "site_id",
    "cell_id",
    "sector_id",
    "gnb_id",
    "du_id",
    "cu_id",
    "ru_id",
    "ue_id_hash",
    "slice_id",
    "qci_or_5qi",
    "service_class",
    "scenario_id",
    "experiment_id",
    "mobility_state",
    "traffic_profile",
    "rsrp_dbm",
    "rsrq_db",
    "rssi_dbm",
    "sinr_db",
    "cqi",
    "mcs",
    "bler_pct",
    "harq_retx_pct",
    "noise_floor_dbm",
    "interference_power_dbm",
    "evm_pct",
    "antenna_vswr",
    "rf_temperature_c",
    "beam_id",
    "beam_index",
    "beam_switch_count",
    "beam_failure_count",
    "ssb_rsrp_dbm",
    "csi_rsrp_dbm",
    "precoder_id",
    "rank_indicator",
    "pmi",
    "ri",
    "mimo_layer_count",
    "timing_offset_us",
    "sync_error_us",
    "fronthaul_delay_ms",
    "fronthaul_jitter_ms",
    "dl_prb_util_pct",
    "ul_prb_util_pct",
    "dl_throughput_mbps",
    "ul_throughput_mbps",
    "mac_scheduler_delay_ms",
    "scheduler_policy",
    "grant_utilization_pct",
    "rlc_buffer_kbytes",
    "rlc_retx_pct",
    "rlc_sdu_delay_ms",
    "queue_delay_ms",
    "packet_delay_ms",
    "pdcp_discard_rate_pct",
    "pdcp_reordering_delay_ms",
    "pdcp_packet_delay_ms",
    "sdap_qos_flow_drop_pct",
    "qfi_violation_pct",
    "rrc_setup_attempts",
    "rrc_setup_fail_pct",
    "rrc_reestab_rate_pct",
    "rrc_connection_drops",
    "session_drop_rate_pct",
    "handover_attempts",
    "handover_success_pct",
    "handover_fail_pct",
    "handover_latency_ms",
    "mobility_pingpong_pct",
    "n3_rtt_ms",
    "n6_rtt_ms",
    "backhaul_delay_ms",
    "transport_jitter_ms",
    "packet_loss_pct",
    "gtp_tunnel_loss_pct",
    "gtp_retransmission_pct",
    "amf_registration_attempts",
    "amf_registration_fail_pct",
    "amf_paging_delay_ms",
    "pdu_session_setup_ms",
    "pdu_session_fail_pct",
    "smf_session_modification_fail_pct",
    "upf_cpu_util_pct",
    "upf_memory_util_pct",
    "upf_packet_drop_pct",
    "upf_throughput_mbps",
    "gtp_tunnel_count",
    "cpu_util_pct",
    "memory_util_pct",
    "disk_io_pct",
    "nic_util_pct",
    "pod_restart_count",
    "container_restart_count",
    "pod_cpu_throttle_pct",
    "node_pressure_status",
    "edge_app_latency_ms",
    "fault_event_id",
    "fault_active",
    "fault_type",
    "label_source",
]


FAULT_EVENT_COLUMNS = [
    "fault_event_id",
    "start_time",
    "end_time",
    "duration_sec",
    "site_id",
    "cell_id",
    "sector_id",
    "slice_id",
    "service_class",
    "fault_type",
    "fault_severity",
    "fault_source",
    "injection_or_real",
    "expected_symptoms",
    "expected_root_cause",
    "expected_healing_action",
    "actual_healing_action",
    "recovery_success",
    "recovery_time_sec",
    "operator_ticket_id",
    "label_source",
    "label_confidence",
    "notes",
]


HEALING_ACTION_COLUMNS = [
    "action_id",
    "timestamp",
    "fault_event_id",
    "site_id",
    "cell_id",
    "slice_id",
    "service_class",
    "action_type",
    "action_source",
    "manual_or_automated",
    "expected_effect",
    "actual_effect",
    "success_status",
    "rollback_required",
    "recovery_time_sec",
    "pre_action_kpi_state",
    "post_action_kpi_state",
    "notes",
]


RIC_XAPP_COLUMNS = [
    "timestamp",
    "e2_node_id",
    "ran_function_id",
    "service_model",
    "kpm_report_style",
    "xapp_id",
    "xapp_name",
    "indication_latency_ms",
    "xapp_decision",
    "policy_id",
    "policy_type",
    "control_action",
    "control_ack_status",
    "control_latency_ms",
    "fault_event_id",
    "cell_id",
    "slice_id",
]


INVENTORY_COLUMNS = [
    "site_id",
    "cell_id",
    "sector_id",
    "gnb_id",
    "du_id",
    "cu_id",
    "ru_id",
    "band",
    "arfcn",
    "bandwidth_mhz",
    "du_vendor_or_stack",
    "cu_vendor_or_stack",
    "ru_vendor_or_stack",
    "ric_stack",
    "core_stack",
    "cloud_node_id",
    "notes",
]


DATA_DICTIONARY_ROWS = [
    ["timestamp", "ISO datetime", "All", "Record time; must be timezone-consistent."],
    ["window_sec", "number", "Main KPI", "KPI aggregation interval in seconds."],
    ["service_class", "enum", "Main KPI/Fault/Action", "One of eMBB, URLLC, mMTC, FWA, V2X."],
    ["fault_event_id", "string", "All", "Join key between KPI rows, fault labels, and healing actions."],
    ["fault_active", "boolean", "Main KPI", "TRUE when KPI row falls inside a labelled fault window."],
    ["fault_type", "enum", "Main KPI/Fault", "normal, cell_congestion, backhaul_degradation, packet_loss_degradation, radio_link_degradation, handover_instability, spectrum_interference, timing_drift, fronthaul_degradation, core_session_degradation, upf_user_plane_degradation, edge_overload, o_cloud_resource_pressure, beam_misalignment, antenna_or_rf_degradation."],
    ["label_source", "string", "Main KPI/Fault", "operator_ticket, injection_script, testbed_log, weak_rule, unknown."],
    ["label_confidence", "0-1 number", "Fault", "1.0 for controlled injection; lower for weak/inferred labels."],
    ["expected_root_cause", "string", "Fault", "Answer-key RCA label."],
    ["expected_healing_action", "string", "Fault", "Answer-key healing action."],
    ["recovery_success", "boolean/string", "Fault/Action", "Whether the action restored expected KPI behavior."],
]


def write_csv(path: Path, columns: list[str], rows: list[list[object]] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        if rows:
            writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUT / "01_main_kpi_telemetry_template.csv",
        MAIN_KPI_COLUMNS,
        [[
            "2026-06-18T10:00:01+05:30", 1, "site_01", "cell_03", "sector_A", "gnb_01", "du_01", "cu_01", "ru_01",
            "ue_hash_001", "slice_embb", 9, "eMBB", "normal_load", "exp_001", "stationary", "udp_downlink",
            -86, -9, -68, 18.5, 11, 14, 1.2, 2.1, -101, -92, 3.2, 1.2, 42, "beam_07", 7, 1, 0, -83, -81, 12, 2, 5, 2, 2,
            12, 1.2, 1.5, 0.2, 72, 48, 120, 35, 4.2, "PF", 88, 840, 1.8, 3.5, 7.5, 9.8,
            0.4, 3.1, 4.0, 0.2, 0.1, 120, 1.5, 0.8, 0, 0.5, 25, 97, 3, 25, 1.1,
            18, 38, 12, 3.5, 0.7, 0.2, 0.1, 500, 0.3, 45, 120, 0.6, 0.2, 68, 55, 0.4, 900, 120,
            74, 62, 10, 50, 0, 0, 1.2, "normal", 11, "", "FALSE", "normal", "normal_window",
        ]],
    )
    write_csv(
        OUT / "02_fault_event_label_template.csv",
        FAULT_EVENT_COLUMNS,
        [[
            "fault_001", "2026-06-18T10:10:00+05:30", "2026-06-18T10:20:00+05:30", 600,
            "site_01", "cell_03", "sector_A", "slice_embb", "eMBB", "backhaul_degradation", 0.8,
            "injection_script", "injected", "n3_rtt/backhaul_delay/jitter increase", "backhaul_degradation",
            "reroute_transport_path", "reroute_transport_path", "TRUE", 120, "", "controlled_fault_injection", 1.0, "",
        ]],
    )
    write_csv(
        OUT / "03_healing_action_outcome_template.csv",
        HEALING_ACTION_COLUMNS,
        [[
            "act_001", "2026-06-18T10:10:05+05:30", "fault_001", "site_01", "cell_03", "slice_embb", "eMBB",
            "reroute_transport_path", "xapp_policy", "automated", "reduce backhaul delay", "delay reduced",
            "success", "FALSE", 120, "backhaul_delay_high", "normal", "",
        ]],
    )
    write_csv(
        OUT / "04_ric_xapp_log_template.csv",
        RIC_XAPP_COLUMNS,
        [[
            "2026-06-18T10:10:05+05:30", "e2node_01", 2, "E2SM-KPM", "report_style_1", "xapp_self_healing",
            "ai_self_healing_xapp", 15.2, "allow_with_monitoring", "policy_001", "A1", "reroute_transport_path",
            "ACK", 22.5, "fault_001", "cell_03", "slice_embb",
        ]],
    )
    write_csv(
        OUT / "05_network_inventory_context_template.csv",
        INVENTORY_COLUMNS,
        [["site_01", "cell_03", "sector_A", "gnb_01", "du_01", "cu_01", "ru_01", "n78", 630000, 100, "OAI/srsRAN/vendor", "OAI/srsRAN/vendor", "RU/vendor", "FlexRIC/other", "Open5GS/free5GC/other", "node_01", ""]],
    )
    write_csv(OUT / "06_data_dictionary_minimum.csv", ["column", "type", "table", "meaning"], DATA_DICTIONARY_ROWS)
    (OUT / "00_README_OPEN_FIRST.txt").write_text(
        "Precise dataset template pack.\n\n"
        "Send these CSV templates when asking for data.\n\n"
        "Required files:\n"
        "1. 01_main_kpi_telemetry_template.csv - primary row-wise KPI training table.\n"
        "2. 02_fault_event_label_template.csv - answer-key fault labels with start/end time.\n"
        "3. 03_healing_action_outcome_template.csv - action and recovery result table.\n"
        "4. 04_ric_xapp_log_template.csv - RIC/xApp/control-loop evidence table.\n"
        "5. 05_network_inventory_context_template.csv - topology/context table.\n"
        "6. 06_data_dictionary_minimum.csv - minimum meaning of critical columns.\n\n"
        "The main join key is fault_event_id. Time columns must use one consistent timezone.\n",
        encoding="utf-8",
    )
    print(OUT)


if __name__ == "__main__":
    main()
