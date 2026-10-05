import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = process.cwd();
const OUT_DIR = path.join(ROOT, "outputs", "dataset_requirements");
const OUT = path.join(OUT_DIR, "O-RAN_Dataset_Requirements_and_Schema.xlsx");

const emailDraft = `Subject: Request for Comprehensive O-RAN / 5G Telemetry Dataset and Lab Support for AI-Native Self-Healing Network Project

Dear [Name/Team],

I hope you are doing well.

We are working on an AI-Native Self-Healing O-RAN Network using a Digital Twin. The goal is to build and validate a closed-loop system that can monitor O-RAN/5G telemetry, detect anomalies, identify root causes, predict faults, and recommend or trigger safe healing actions through a RIC/xApp-style control pipeline.

Our current prototype supports FlexRIC-based lab telemetry ingestion, controlled fault injection, anomaly detection, root-cause analysis, healing recommendation, model benchmarking, and digital twin validation. However, FlexRIC-style lab/emulated telemetry is mainly useful for proving the RIC/KPM/xApp pipeline flow. For stronger research-grade or production-grade validation, we need more authentic, diverse, and well-labelled telemetry.

The reason is that self-healing models do not only need KPI values. They need context, timing, fault truth, service impact, and recovery outcome. Without those, a model may detect that something is abnormal, but it cannot reliably prove why it happened, which service was affected, or whether the healing action actually worked.

We would like to request support for any available real, lab-generated, emulated, or anonymized O-RAN/5G telemetry dataset, along with fault/event labels if available.

We are interested in the following data sources, prioritized by usefulness:

IMPORTANT:
- O-RAN testbed data, if it includes real/lab RAN, Core, RIC, and timestamped fault labels.
- O-CU / O-DU / O-RU telemetry, because it gives architecture-level KPI visibility.
- Operator-style anonymized KPI logs, if available, because these are closest to real production behavior.
- Controlled fault-injection experiment logs, because they provide ground-truth labels for accuracy measurement.

VERY USEFUL:
- OAI or srsRAN gNB/nrUE setup logs, because they provide more realistic RAN-stack behavior than a pure emulator.
- RF simulator or SDR-based setup logs, because they help validate radio/channel behavior and fault repeatability.
- 5G Core telemetry, because some failures originate from AMF/SMF/session behavior rather than RAN.
- UPF / transport / backhaul telemetry, because many degradations are caused by N3/N6/backhaul delay, packet loss, and tunnel issues.
- Public or internal Open RAN experimental datasets, because they improve model credibility and benchmarking coverage.

USEFUL / SUPPORTING:
- FlexRIC / Near-RT RIC setup logs, because they validate E2/KPM/xApp pipeline integration, although FlexRIC-only emulator data is not sufficient for production-grade accuracy claims.
- Kubernetes/O-Cloud infrastructure telemetry, because it is needed when validating cloud-native O-RAN infrastructure faults such as CPU pressure, pod restarts, and edge overload.

Ideally, each telemetry row should represent a timestamped KPI window:
timestamp + site/cell + slice/service + UE or aggregate entity + KPI window

Example:
2026-06-18 10:00:01, site_01, cell_03, slice_eMBB, UE_hash_123, 1-second KPI window

This structure is important because telecom faults are time-dependent. A single KPI snapshot is not enough. We need to observe how metrics change before, during, and after a fault.

The dataset should include basic identifiers and context such as timestamp, site_id, cell_id, sector_id, gNB/CU/DU/RU identifiers, UE hash, slice_id, 5QI/QCI, service_class, scenario_id, experiment_id, mobility_state, and traffic_profile. These fields tell us where and under what condition the KPI was recorded. Without context, the model cannot learn whether a behavior is normal for that environment or actually faulty.

The dataset should cover multiple service classes if possible: eMBB, URLLC, mMTC, FWA, and V2X. This matters because different services have different requirements. URLLC is latency-sensitive, eMBB is throughput-heavy, mMTC is density-heavy, FWA is capacity/coverage-sensitive, and V2X is mobility/safety-sensitive.

We request Radio/PHY/RF metrics such as RSRP, RSRQ, RSSI, SINR, CQI, MCS, BLER, HARQ retransmission, interference power, EVM, beam information, timing offset, sync error, and fronthaul delay. These fields are needed to distinguish radio degradation, interference, RF issues, beam problems, and timing/fronthaul issues from congestion or transport faults.

If available, beamforming-related fields such as beam_index, beam_switch_count, beam_failure_count, SSB/CSI RSRP, precoder_id, PMI, RI, CSI report, and MIMO layer count would be highly useful. These are needed if we want to move beyond generic radio anomaly detection toward beam-level diagnosis and intelligent beam optimization.

We request MAC/RLC/scheduler metrics such as DL/UL PRB utilization, throughput, scheduler delay, grant utilization, RLC buffer size, retransmissions, queue delay, and packet delay. These are needed to identify congestion, scheduler delay, buffer buildup, retransmission issues, and resource allocation problems.

We request PDCP/SDAP/RRC/mobility metrics such as PDCP discard, reordering delay, QoS-flow drop, QFI violation, RRC setup failures, re-establishment, session drops, handover success/failure, handover latency, and mobility ping-pong. These help identify session, QoS, and mobility faults that may not be visible from PHY metrics alone.

We request transport/backhaul/fronthaul metrics such as N3 RTT, N6 RTT, backhaul delay, jitter, packet loss, GTP tunnel loss, fronthaul latency, PTP sync status, and sync drift. Many service degradations are caused outside the radio link, so these fields are required for root-cause separation.

We request 5G Core metrics such as AMF registration failure, AMF paging delay, PDU session setup/failure, SMF session modification failures, UPF CPU/memory, UPF packet drops, UPF throughput, and GTP tunnel count. These fields help identify whether degradation is caused by control-plane, user-plane, or core-session issues.

We request O-Cloud/Kubernetes/infrastructure metrics such as CPU, memory, disk I/O, NIC utilization, pod/container restarts, CPU throttling, node pressure, and edge application latency. In cloud-native O-RAN, faults can come from infrastructure pressure, not just radio or transport.

We request RIC/xApp/policy logs such as RIC indication timestamp, E2 node ID, RAN function ID, service model, report style, xApp ID, xApp decision, policy ID/type, control action, control acknowledgment, and control latency. These fields validate whether the closed-loop RIC behavior actually occurred.

The most important requirement is a timestamped fault/event label table. Each fault event should include start_time, end_time, affected site/cell/slice/service, fault_type, severity, whether it was injected or real, expected symptoms, expected root cause, expected healing action, actual action, recovery success, recovery time, ticket ID if available, label source, and label confidence. This table acts as the answer key. Without it, we can detect anomalies but cannot confidently measure accuracy, RCA quality, or recovery performance.

Fault classes of interest include normal, cell_congestion, backhaul_degradation, packet_loss_degradation, radio_link_degradation, handover_instability, spectrum_interference, timing_drift, fronthaul_degradation, core_session_degradation, upf_user_plane_degradation, edge_overload, o_cloud_resource_pressure, beam_misalignment, antenna_or_rf_degradation, ptp_sync_degradation, and xapp_policy_conflict.

If production fault labels are not available, controlled fault-injection labels are also acceptable. For example: 10:00-10:10 normal, 10:10-10:20 inject 80 ms backhaul delay, 10:20-10:30 normal recovery, 10:30-10:40 inject 5% packet loss. Controlled labels are valuable because they provide clean ground truth.

We also request a healing/action outcome table if mitigation actions were performed. It should include action_id, timestamp, fault_event_id, affected cell/slice, action_type, whether the action was manual or automated, expected effect, actual effect, success status, rollback status, recovery time, and post-action KPI state. Self-healing is not only about detecting faults; we need to know whether the recommended action actually improved the network.

Any amount of data is useful, but for meaningful validation the ideal targets are:
- Minimum useful dataset: 1-2 hours, 1-3 cells, 1-2 service classes, 10k-100k KPI rows, 5-10 labelled fault events.
- Good research-grade dataset: 24-72 hours, 3-10 cells, 3-5 service classes, 1M-10M KPI rows, 50-100 labelled fault events.
- Strong research/industry-grade dataset: 2-4 weeks, 10-50 cells, 5 service classes, 50M-500M KPI rows, 500+ labelled fault events.
- Production-grade validation dataset: 30-90 days, 50+ cells, all service classes, 100M-1B+ KPI rows, 1000+ labelled events.

For each major fault class, we ideally need 50+ labelled events for minimum validation, 200+ labelled events for strong research validation, and 500-1000+ labelled events per class for production-grade claims. This is because telecom faults are rare, imbalanced, and overlapping. A small number of examples can make the model overfit.

Preferred formats are CSV for small exports, Parquet for large KPI datasets, JSONL for logs and decision streams, database dumps such as SQLite/PostgreSQL/ClickHouse where available, and PCAP/raw logs if parsed KPI files are not available. Parquet is preferred for very large telemetry.

We do not need sensitive subscriber or operator information. UE IDs, IMSI/SUPI, site names, cell names, IP addresses, operator identifiers, subscriber identifiers, and location information can be anonymized or hashed. For model training, consistent anonymous IDs are enough.

If real production data is not available, lab/testbed support would also be useful: OAI gNB + nrUE with RF simulator, OAI/srsRAN with SDR, FlexRIC connected to OAI/srsRAN, Colosseum-style Open RAN experiments, controlled fault injection, and logs from gNB, UE, CU, DU, RIC, xApp, UPF, AMF, and transport layers.

The dataset will allow us to validate anomaly detection, root-cause analysis, fault prediction, healing recommendation, service-impact prediction, slice-aware assurance, RIC/xApp decision logic, digital twin validation, and model generalization across cells, services, and fault types.

The key requirement is not just more rows, but better variety, labels, and context. A smaller well-labelled dataset is more useful than a huge unlabelled dataset. Ideally, we need both: large KPI volume and clean timestamped fault labels.

Even partial data is useful. If the complete dataset is not available, we can start with raw KPM logs, cell-level KPI CSVs, UE-level KPI CSVs, RIC/xApp logs, 5G Core logs, UPF/backhaul logs, fault ticket/event records, controlled fault-injection traces, or anonymized historical incident data.

Please let us know what data, logs, or lab access may be available, what format it is in, and whether any restrictions apply. We are flexible and can adapt our parser and training pipeline based on the available telemetry.

Best regards,
[Your Name]`;

const sources = [
  ["O-RAN testbed", "IMPORTANT", "Full-system validation", "Most useful if it includes RAN + Core + RIC + labels", "Can validate end-to-end self-healing rather than isolated KPI behavior.", "If only demo/emulator without labels, it becomes integration proof only."],
  ["Operator-style anonymized KPI logs", "IMPORTANT", "Production realism", "Closest to real network behavior", "Best source for real-world traffic diversity, seasonality, mobility, load, and unexpected patterns.", "Needs anonymization and fault/ticket alignment."],
  ["O-CU / O-DU / O-RU telemetry", "IMPORTANT", "Architecture-level O-RAN telemetry", "Direct visibility into where faults occur", "Needed to map AI decisions to actual O-RAN blocks such as RRC, PDCP, SDAP, RLC, MAC, High-PHY, Low-PHY.", "May need vendor/testbed-specific parsers."],
  ["Controlled fault-injection experiment logs", "IMPORTANT", "Ground truth labels", "Best for measuring accuracy", "Gives start/end fault truth so we can measure detection, RCA, healing, and recovery time.", "Synthetic/lab faults still need honest labeling."],
  ["OAI or srsRAN gNB/nrUE setup", "VERY USEFUL", "Lab-realistic RAN stack", "More realistic than pure emulator", "Runs real open-source RAN stack behavior and can be paired with RFsim/SDR and FlexRIC.", "Setup complexity; labels still need injection or tickets."],
  ["RF simulator or SDR-based setup", "VERY USEFUL", "Radio/channel validation", "Useful for repeatable radio experiments", "RFsim supports controlled repeatability; SDR gives closer-to-real RF behavior.", "Hardware/channel conditions must be documented."],
  ["5G Core telemetry", "VERY USEFUL", "Core/session RCA", "Needed for AMF/SMF/session faults", "Prevents misclassifying core/session issues as RAN faults.", "Must align timestamps with RAN telemetry."],
  ["UPF / transport / backhaul telemetry", "VERY USEFUL", "Transport/user-plane RCA", "Needed for backhaul, N3/N6, packet loss, tunnel loss", "Many KPI degradations originate outside radio; this is essential for RCA.", "Requires network/transport logs and time sync."],
  ["Public or internal Open RAN experimental datasets", "VERY USEFUL", "Benchmarking and credibility", "Good for external validation", "Adds realistic variety and avoids overfitting only to our lab.", "Labels may be weak or missing."],
  ["Kubernetes/O-Cloud infrastructure telemetry", "USEFUL", "Cloud-native infrastructure RCA", "Useful when O-RAN workloads run on cloud/K8s", "Needed for CPU pressure, pod restarts, edge overload, and resource placement faults.", "Not essential if project scope excludes O-Cloud faults."],
  ["FlexRIC / Near-RT RIC setup", "USEFUL", "RIC/KPM/xApp integration proof", "Good for pipeline validation", "Proves E2/KPM subscription, RIC-style ingestion, xApp-style decisions.", "FlexRIC-only emulator data is not enough for production-grade model accuracy claims."],
];

const tableOverview = [
  ["Main_KPI_Table", "One row per timestamped KPI window per cell/slice/UE or aggregate entity", "Primary model-training table", "Mandatory"],
  ["Fault_Event_Table", "One row per fault/incident/injection window", "Ground-truth answer key for detection/RCA/healing evaluation", "Mandatory for accuracy claims"],
  ["Healing_Action_Table", "One row per manual/automated mitigation action", "Measures whether self-healing action worked", "Strongly recommended"],
  ["RIC_xApp_Log_Table", "One row per RIC indication/decision/control event", "Validates closed-loop RIC/xApp behavior", "Strongly recommended"],
  ["Inventory_Context_Table", "One row per site/cell/RU/CU/DU/slice metadata item", "Adds topology/context for generalization", "Recommended"],
];

const mainColumns = [
  ["timestamp", "datetime", "Mandatory", "All", "Event/KPI time", "Aligns metrics, labels, and actions over time.", "2026-06-18 10:00:01"],
  ["window_sec", "number", "Mandatory", "All", "Aggregation window", "Defines row granularity for fair comparisons.", "1"],
  ["site_id", "string", "Mandatory", "Topology", "Site identity", "Needed for site holdout and geography/topology context.", "site_01"],
  ["cell_id", "string", "Mandatory", "RAN", "Cell identity", "Core grouping key for RAN assurance.", "cell_03"],
  ["sector_id", "string", "Recommended", "RAN", "Sector identity", "Separates sector-specific load and radio patterns.", "sector_A"],
  ["gnb_id", "string", "Recommended", "RAN", "gNB identity", "Links telemetry to gNB/RAN node.", "gnb_01"],
  ["du_id", "string", "Recommended", "O-DU", "DU identity", "Maps MAC/RLC/High-PHY metrics to O-DU.", "du_01"],
  ["cu_id", "string", "Recommended", "O-CU", "CU identity", "Maps RRC/PDCP/SDAP metrics to O-CU.", "cu_01"],
  ["ru_id", "string", "Recommended", "O-RU", "RU identity", "Maps RF/Low-PHY metrics to O-RU.", "ru_01"],
  ["ue_id_hash", "string", "Recommended", "UE", "Anonymized UE identity", "Supports UE-level behavior without exposing subscriber data.", "ue_hash_abc"],
  ["slice_id", "string", "Mandatory", "Slice", "Network slice identity", "Required for slice-aware assurance.", "slice_embb"],
  ["qci_or_5qi", "string/number", "Recommended", "QoS", "QoS identifier", "Helps map KPI tolerance to service requirements.", "9"],
  ["service_class", "enum", "Mandatory", "Slice", "eMBB/URLLC/mMTC/FWA/V2X", "Different services have different SLA priorities.", "eMBB"],
  ["scenario_id", "string", "Recommended", "Experiment", "Scenario/experiment name", "Useful for split/holdout evaluation.", "normal_load"],
  ["mobility_state", "enum", "Recommended", "UE/RAN", "stationary/pedestrian/vehicular", "Mobility changes expected KPI behavior.", "vehicular"],
  ["traffic_profile", "string", "Recommended", "Traffic", "Traffic type/load", "Distinguishes load-driven issues from faults.", "udp_downlink"],
  ["rsrp_dbm", "number", "Important", "O-RU/Low-PHY", "Reference signal received power", "Radio coverage/weak signal detection.", "-86"],
  ["rsrq_db", "number", "Important", "O-RU/Low-PHY", "Reference signal received quality", "Radio quality/interference diagnosis.", "-9"],
  ["rssi_dbm", "number", "Recommended", "O-RU/Low-PHY", "Received signal strength", "Supports RF diagnosis.", "-68"],
  ["sinr_db", "number", "Important", "PHY", "Signal-to-interference-plus-noise ratio", "Key radio quality feature.", "18.5"],
  ["cqi", "number", "Important", "High-PHY/MAC", "Channel quality indicator", "Supports link adaptation and radio RCA.", "11"],
  ["mcs", "number", "Recommended", "High-PHY/MAC", "Modulation/coding scheme", "Explains throughput/radio adaptation behavior.", "14"],
  ["bler_pct", "number", "Important", "PHY/MAC", "Block error rate", "Detects radio errors and retransmission pressure.", "1.2"],
  ["harq_retx_pct", "number", "Recommended", "MAC/PHY", "HARQ retransmission percentage", "Identifies radio reliability issues.", "2.1"],
  ["noise_floor_dbm", "number", "Recommended", "O-RU", "RF noise floor", "Useful for interference detection.", "-101"],
  ["interference_power_dbm", "number", "Recommended", "O-RU", "Interference power", "Separates interference from congestion.", "-92"],
  ["evm_pct", "number", "Recommended", "O-RU", "Error vector magnitude", "RF hardware/signal quality indicator.", "3.2"],
  ["beam_id", "string/number", "Optional", "O-RU/Beam", "Active beam ID", "Needed for beam-level diagnosis.", "beam_07"],
  ["beam_quality_score", "number", "Optional", "Beam", "Beam quality score", "Supports beam misalignment detection.", "0.86"],
  ["beam_misalignment_deg", "number", "Optional", "Beam", "Estimated beam misalignment", "Needed for beamforming AI claims.", "4.5"],
  ["beam_failure_count", "number", "Optional", "Beam", "Beam failure events", "Useful for beam recovery modeling.", "2"],
  ["ssb_rsrp", "number", "Optional", "Beam", "SSB RSRP", "Beam measurement support.", "-83"],
  ["csi_rsrp", "number", "Optional", "Beam", "CSI RSRP", "Beam/CSI reporting support.", "-81"],
  ["precoder_id", "string/number", "Optional", "MIMO", "Precoder/codebook ID", "Required for real beamforming/precoder AI.", "12"],
  ["rank_indicator", "number", "Optional", "MIMO", "MIMO rank", "Needed for MIMO layer decisions.", "2"],
  ["pmi", "string/number", "Optional", "MIMO", "Precoding matrix indicator", "Needed for MIMO/beam optimization.", "5"],
  ["timing_offset_us", "number", "Recommended", "Timing/FH", "Timing offset", "Detects sync/timing drift.", "12"],
  ["fronthaul_delay_ms", "number", "Recommended", "Fronthaul", "FH delay", "Separates fronthaul issues from radio/core.", "1.5"],
  ["dl_prb_util_pct", "number", "Important", "MAC", "Downlink PRB utilization", "Detects congestion/resource pressure.", "72"],
  ["ul_prb_util_pct", "number", "Important", "MAC", "Uplink PRB utilization", "Detects uplink congestion/resource pressure.", "48"],
  ["dl_throughput_mbps", "number", "Important", "MAC/PDCP", "Downlink throughput", "Service impact and capacity metric.", "120"],
  ["ul_throughput_mbps", "number", "Recommended", "MAC/PDCP", "Uplink throughput", "Uplink service impact.", "35"],
  ["mac_scheduler_delay_ms", "number", "Recommended", "MAC", "Scheduler delay", "Identifies scheduler bottlenecks.", "4.2"],
  ["scheduler_policy", "string", "Optional", "MAC", "Scheduler policy", "Explains policy-driven behavior.", "PF"],
  ["rlc_buffer_kbytes", "number", "Recommended", "RLC", "RLC buffer size", "Detects buffer buildup/congestion.", "840"],
  ["rlc_retx_pct", "number", "Recommended", "RLC", "RLC retransmission percentage", "Detects reliability/queue issues.", "1.8"],
  ["queue_delay_ms", "number", "Recommended", "RLC/MAC", "Queue delay", "Latency root-cause feature.", "7.5"],
  ["pdcp_discard_rate_pct", "number", "Recommended", "PDCP", "PDCP discard", "Detects session/user-plane degradation.", "0.4"],
  ["pdcp_reordering_delay_ms", "number", "Recommended", "PDCP", "PDCP reordering delay", "Detects packet ordering/session issues.", "3.1"],
  ["sdap_qos_flow_drop_pct", "number", "Recommended", "SDAP", "QoS flow drop", "Detects QoS flow degradation.", "0.2"],
  ["qfi_violation_pct", "number", "Recommended", "SDAP", "QFI violations", "Detects QoS policy mismatch.", "0.1"],
  ["rrc_setup_fail_pct", "number", "Important", "RRC", "RRC setup failures", "Control-plane access fault signal.", "1.5"],
  ["rrc_reestab_rate_pct", "number", "Recommended", "RRC", "RRC re-establishment rate", "Mobility/radio stability signal.", "0.8"],
  ["session_drop_rate_pct", "number", "Recommended", "RRC/Core", "Session drops", "Session stability signal.", "0.5"],
  ["handover_attempts", "number", "Recommended", "RRC/Mobility", "Handover attempts", "Mobility context.", "25"],
  ["handover_success_pct", "number", "Important", "RRC/Mobility", "Handover success", "Mobility performance.", "97"],
  ["handover_fail_pct", "number", "Important", "RRC/Mobility", "Handover failures", "Handover instability detection.", "3"],
  ["mobility_pingpong_pct", "number", "Recommended", "RRC/Mobility", "Ping-pong handover rate", "Detects poor mobility tuning.", "1.1"],
  ["n3_rtt_ms", "number", "Important", "Transport/Core", "N3 RTT", "UPF path delay/root cause.", "18"],
  ["n6_rtt_ms", "number", "Important", "Transport/Core", "N6/internet RTT", "External/core path delay.", "38"],
  ["backhaul_delay_ms", "number", "Important", "Transport", "Backhaul delay", "Backhaul degradation RCA.", "12"],
  ["transport_jitter_ms", "number", "Important", "Transport", "Transport jitter", "Transport instability detection.", "3.5"],
  ["packet_loss_pct", "number", "Important", "Transport/User-plane", "Packet loss", "Packet loss degradation detection.", "0.7"],
  ["gtp_tunnel_loss_pct", "number", "Recommended", "Core/UPF", "GTP tunnel loss", "Tunnel/user-plane RCA.", "0.2"],
  ["amf_registration_fail_pct", "number", "Recommended", "5G Core/AMF", "AMF registration failure", "Core access failure detection.", "0.3"],
  ["amf_paging_delay_ms", "number", "Recommended", "5G Core/AMF", "Paging delay", "Core control-plane delay.", "45"],
  ["pdu_session_setup_ms", "number", "Recommended", "5G Core/SMF", "PDU setup time", "Session setup degradation.", "120"],
  ["pdu_session_fail_pct", "number", "Recommended", "5G Core/SMF", "PDU setup failures", "Session failure signal.", "0.6"],
  ["upf_cpu_util_pct", "number", "Recommended", "UPF", "UPF CPU", "UPF overload RCA.", "68"],
  ["upf_packet_drop_pct", "number", "Recommended", "UPF", "UPF packet drops", "User-plane drop RCA.", "0.4"],
  ["cpu_util_pct", "number", "Optional", "O-Cloud", "Node CPU", "Cloud resource pressure.", "74"],
  ["memory_util_pct", "number", "Optional", "O-Cloud", "Node memory", "Cloud resource pressure.", "62"],
  ["pod_restart_count", "number", "Optional", "O-Cloud/K8s", "Pod restarts", "Cloud-native instability signal.", "0"],
  ["edge_app_latency_ms", "number", "Optional", "Edge", "Edge application latency", "Edge overload/service impact.", "11"],
  ["anomaly_detected", "boolean", "Derived", "AI output", "Anomaly decision", "Model output/evaluation target.", "TRUE"],
  ["predicted_root_cause", "string", "Derived", "AI output", "Predicted RCA", "RCA model output.", "backhaul_degradation"],
  ["predicted_healing_action", "string", "Derived", "AI output", "Recommended action", "Healing model output.", "reroute_transport_path"],
];

const faultColumns = [
  ["fault_event_id", "string", "Mandatory", "Unique fault ID", "Links KPI rows, labels, and healing actions.", "fault_001"],
  ["start_time", "datetime", "Mandatory", "Fault start", "Needed to calculate detection latency and labels.", "2026-06-18 10:10:00"],
  ["end_time", "datetime", "Mandatory", "Fault end", "Needed to calculate recovery and affected windows.", "2026-06-18 10:20:00"],
  ["duration_sec", "number", "Mandatory", "Fault duration", "Supports time-window evaluation.", "600"],
  ["site_id", "string", "Mandatory", "Affected site", "Maps event to telemetry.", "site_01"],
  ["cell_id", "string", "Mandatory", "Affected cell", "Maps event to telemetry.", "cell_03"],
  ["slice_id", "string", "Recommended", "Affected slice", "Measures service/slice-specific impact.", "slice_embb"],
  ["service_class", "enum", "Recommended", "Affected service", "Service-aware evaluation.", "eMBB"],
  ["fault_type", "enum", "Mandatory", "Fault class", "Ground-truth target for RCA.", "backhaul_degradation"],
  ["fault_severity", "number/string", "Mandatory", "Severity", "Supports severity-aware models.", "0.8"],
  ["injection_or_real", "enum", "Mandatory", "real/injected/synthetic", "Distinguishes production incidents from lab labels.", "injected"],
  ["expected_root_cause", "string", "Mandatory", "Answer-key RCA", "RCA evaluation ground truth.", "backhaul_degradation"],
  ["expected_healing_action", "string", "Mandatory", "Answer-key healing", "Healing-action evaluation target.", "reroute_transport_path"],
  ["actual_healing_action", "string", "Recommended", "Action actually taken", "Measures real response.", "reroute_transport_path"],
  ["recovery_success", "boolean", "Recommended", "Whether recovery worked", "Measures healing effectiveness.", "TRUE"],
  ["recovery_time_sec", "number", "Recommended", "Time to recovery", "MTTR/recovery KPI.", "120"],
  ["label_source", "string", "Mandatory", "ticket/operator/injection_script", "Trust level of labels.", "injection_script"],
  ["label_confidence", "number", "Recommended", "0-1 label confidence", "Down-weights weak labels.", "1.0"],
];

const actionColumns = [
  ["action_id", "string", "Mandatory", "Unique action ID", "Links action to event and outcome.", "act_001"],
  ["timestamp", "datetime", "Mandatory", "Action time", "Measures reaction time.", "2026-06-18 10:10:05"],
  ["fault_event_id", "string", "Recommended", "Linked fault", "Connects action to incident.", "fault_001"],
  ["cell_id", "string", "Mandatory", "Affected cell", "Action scope.", "cell_03"],
  ["slice_id", "string", "Recommended", "Affected slice", "Slice-aware action scope.", "slice_embb"],
  ["action_type", "enum", "Mandatory", "Healing action", "Target/action label.", "reroute_transport_path"],
  ["manual_or_automated", "enum", "Mandatory", "Action source", "Separates human vs automation.", "automated"],
  ["expected_effect", "string", "Recommended", "Expected KPI improvement", "Explains intent.", "lower backhaul delay"],
  ["actual_effect", "string", "Recommended", "Observed effect", "Measures effectiveness.", "delay reduced"],
  ["success_status", "boolean/string", "Mandatory", "Success/fail/partial", "Learning target for action quality.", "success"],
  ["rollback_required", "boolean", "Recommended", "Rollback status", "Safety evaluation.", "FALSE"],
  ["recovery_time_sec", "number", "Recommended", "Time to recovery", "MTTR calculation.", "120"],
  ["post_action_kpi_state", "string/json", "Recommended", "Post-action state", "Verifies network improved.", "normal"],
];

const samples = [
  ["Demo minimum", "1-2 hours", "1-3", "1-2", "10k-100k", "5-10", "Only enough for demo/prototype proof."],
  ["Research grade", "24-72 hours", "3-10", "3-5", "1M-10M", "50-100", "Enough for good academic validation if labels are clean."],
  ["Strong research / industry", "2-4 weeks", "10-50", "5", "50M-500M", "500+", "Supports stronger generalization and holdout validation."],
  ["Production-grade validation", "30-90 days", "50+", "all", "100M-1B+", "1000+", "Needed for serious deployment-level performance claims."],
];

const faultTargets = [
  ["Minimum per fault class", "50+", "Basic validation only."],
  ["Strong research per fault class", "200+", "Better class-level performance estimates."],
  ["Production-grade per fault class", "500-1000+", "Needed because telecom faults are rare and symptoms overlap."],
];

const validation = [
  ["Time split", "Train on earlier time windows, test on later windows", "Prevents leakage from adjacent rows."],
  ["Cell/site holdout", "Hold out entire cells/sites", "Tests whether model generalizes across locations."],
  ["Fault-family holdout", "Hold out a fault class during training", "Tests unknown fault detection ability."],
  ["Service holdout", "Hold out one service class", "Tests service generalization."],
  ["Normal-only false-positive test", "Evaluate on clean normal windows", "Measures alarm noise."],
  ["Recovery validation", "Compare post-action KPIs with pre-action KPIs", "Tests whether healing worked."],
];

function matrixWithHeader(headers, rows) {
  return [headers, ...rows];
}

function writeSheet(workbook, name, headers, rows, widths = []) {
  const ws = workbook.worksheets.add(name);
  const data = matrixWithHeader(headers, rows);
  ws.getRangeByIndexes(0, 0, data.length, headers.length).values = data;
  ws.freezePanes.freezeRows(1);
  ws.showGridLines = false;
  const used = ws.getRangeByIndexes(0, 0, data.length, headers.length);
  used.format.wrapText = true;
  used.format.borders = { preset: "all", style: "thin", color: "#CBD5E1" };
  const header = ws.getRangeByIndexes(0, 0, 1, headers.length);
  header.format = {
    fill: "#0F172A",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
  };
  widths.forEach((w, i) => {
    ws.getRangeByIndexes(0, i, 1, 1).format.columnWidthPx = w;
  });
  return ws;
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const workbook = Workbook.create();

  const summary = workbook.worksheets.add("README");
  summary.showGridLines = false;
  summary.getRange("A1:F1").merge();
  summary.getRange("A1").values = [["O-RAN Dataset Requirements Workbook"]];
  summary.getRange("A1").format = { fill: "#0F172A", font: { bold: true, color: "#FFFFFF", size: 16 } };
  summary.getRange("A3:F8").values = [
    ["Purpose", "Exact dataset schema and request package for AI-native self-healing O-RAN validation", "", "", "", ""],
    ["Use first", "Source_Priority, Table_Overview, Main_KPI_Schema, Fault_Event_Schema", "", "", "", ""],
    ["Most important ask", "Timestamped KPI telemetry + timestamped fault labels + healing outcome logs", "", "", "", ""],
    ["Best data", "Operator-style logs, O-RAN testbed data, O-CU/O-DU/O-RU telemetry, controlled fault injection", "", "", "", ""],
    ["FlexRIC note", "Useful for RIC/KPM/xApp integration proof, not sufficient alone for production-grade model accuracy", "", "", "", ""],
    ["Generated for", "AI-Native Self-Healing O-RAN Network using a Digital Twin", "", "", "", ""],
  ];
  summary.getRange("A3:F8").format.wrapText = true;
  summary.getRange("A3:A8").format = { fill: "#E0F2FE", font: { bold: true } };
  summary.getRange("A:F").format.columnWidthPx = 180;

  writeSheet(workbook, "Source_Priority", ["Source", "Priority Mark", "Primary Value", "Usefulness", "Reasoning", "Limitation"], sources, [250, 110, 180, 240, 420, 300]);
  writeSheet(workbook, "Table_Overview", ["Table", "Row Grain", "Purpose", "Requirement Level"], tableOverview, [220, 340, 420, 160]);
  writeSheet(workbook, "Main_KPI_Schema", ["Column", "Data Type", "Required Level", "O-RAN Block/Source", "Meaning", "Why Required", "Example"], mainColumns, [180, 110, 120, 170, 250, 380, 160]);
  writeSheet(workbook, "Fault_Event_Schema", ["Column", "Data Type", "Required Level", "Meaning", "Why Required", "Example"], faultColumns, [180, 120, 120, 260, 380, 180]);
  writeSheet(workbook, "Healing_Action_Schema", ["Column", "Data Type", "Required Level", "Meaning", "Why Required", "Example"], actionColumns, [180, 120, 120, 260, 380, 180]);
  writeSheet(workbook, "Sample_Size_Targets", ["Dataset Tier", "Duration", "Cells", "Service Classes", "KPI Rows", "Labelled Fault Events", "Reasoning"], samples, [190, 140, 100, 140, 150, 170, 420]);
  writeSheet(workbook, "Fault_Class_Targets", ["Target", "Events Per Class", "Reasoning"], faultTargets, [260, 150, 520]);
  writeSheet(workbook, "Validation_Strategy", ["Validation Method", "How To Do It", "Reasoning"], validation, [220, 420, 420]);

  const email = workbook.worksheets.add("Email_Draft");
  email.showGridLines = false;
  email.getRange("A1").values = [["Complete Email Draft"]];
  email.getRange("A1").format = { fill: "#0F172A", font: { bold: true, color: "#FFFFFF", size: 14 } };
  const paragraphs = emailDraft.split("\n").map((line) => [line]);
  email.getRangeByIndexes(2, 0, paragraphs.length, 1).values = paragraphs;
  email.getRangeByIndexes(2, 0, paragraphs.length, 1).format.wrapText = true;
  email.getRange("A:A").format.columnWidthPx = 980;

  const check = await workbook.inspect({
    kind: "sheet,table",
    maxChars: 5000,
    tableMaxRows: 5,
    tableMaxCols: 6,
  });
  await fs.writeFile(path.join(OUT_DIR, "dataset_requirements_inspect.ndjson"), check.ndjson, "utf8");

  for (const sheetName of ["README", "Source_Priority", "Main_KPI_Schema", "Email_Draft"]) {
    const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
    await fs.writeFile(path.join(OUT_DIR, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
  }

  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await xlsx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
