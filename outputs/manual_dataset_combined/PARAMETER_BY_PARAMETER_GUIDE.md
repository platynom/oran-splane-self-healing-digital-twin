# Reading the O-RAN data one parameter at a time

Start with **S027 TIMESAFE raw captures**, then compare its linked supplied-label representation **S026 TIMESAFE packets**. Both describe the production capture. The raw packet rows are the evidence; our appended columns are interpretations. Do not begin with the simulator or with a model accuracy score.

## Six questions for every parameter

1. **What** does this field actually record: packet contents, a calculation, a default, a scenario name, or a model output?
2. **Which** exact source record and column contain it? Use the workbook's source ID, hash and record ordinal.
3. **Where** was it observed? A capture interface is not automatically the receiver clock being protected.
4. **When** was it observed? Packet time, calculation window and action time are different. Capture-relative seconds do not align separate experiments.
5. **Why** could it matter? Explain a possible mechanism and at least one benign alternative.
6. **How** would we justify a label or action? Specify the extra measurement or experiment record needed; do not fill the gap with a guess.

For the table below, WHICH and WHERE are resolved by the workbook source columns and the producer references in `PARAMETER_PROVENANCE.md`. WHEN is the packet/record time for raw fields, the indicated window for features, and the recorded software run for results. A field can have different provenance in different datasets even when its name is identical.

## Packet fields: begin here

| Which field | What and how to read it | Why it matters; what would justify a stronger label |
|---|---|---|
| `Source`, `Destination` | Packet addresses in raw exports; integer encodings in supplied-label files. Compare only through the verified capture-local encoding map. | Groups traffic by sender/recipient. An address does not establish owner or authorization. Obtain device inventory and experiment logs. |
| `Protocol` | Protocol identified by the packet export. | Use the original PTP filter for raw-to-encoded comparison; excluded non-PTP packets are not automatically packet loss. |
| `Length` | Exported packet length in bytes. | Describes packet structure. Compare within the same message type; length alone is not an attack detector. |
| `SequenceID`, `ptp_seq_id` | Sequence field used for protocol exchanges. | Pair only within the same capture and appropriate sender/message context. Reordering, wraparound and multiple senders can explain changes. |
| `MessageType`, `ptp_msg_type` | What the PTP message does; encoded values require the verified decoder. | Announce, Sync and Follow_Up play different roles. A message type alone does not prove a fault. |
| `Time`, `Time Interval`, `t_s` | Export time, inter-record interval, or capture-derived seconds; check the specific producer. | Supports ordering and rate calculations. Do not join unrelated captures on the same elapsed second. |
| `Label` | Publisher-supplied packet annotation, copied exactly. | Local production label generation is not independently reproduced. Describe annotation patterns; do not rename zero as verified healthy. |

Primary context: TIMESAFE §6.2 describes using experiment logs, attack timing and machine identities to generate packet labels. That method explains why capture-specific logs are necessary; the paper alone does not validate the conflicting local files. [TIMESAFE paper, §6.2](https://arxiv.org/html/2412.13049v3#S6.SS2)

## Timing, state and window parameters

The meanings below describe the inspected project software, principally `ingest/pcap_ingest.py`, `ingest/schema.py` and `telemetry/features.py`. They are not evidence that a physical sensor measured every field. Exact formulas and configured values are recorded in `PARAMETER_PROVENANCE.md` and `THRESHOLD_AND_RECOVERY_AUDIT.md`.

| Which fields | What / how / when | Why and limits for classification |
|---|---|---|
| `offset_ns`, `measured_offset_ns` | Timing difference in ns. PCAP ingestion calculates it from payload/capture timestamps and estimated delay; schema may copy one field into the other. | Large calculated offset suggests something to investigate. It cannot distinguish attack, path asymmetry or timestamp error by itself. The word measured is not proof of hardware measurement. |
| `path_delay_ns`, `pdv_ns` | Calculated path delay and its variation; incomplete exchanges may reuse previous delay or zero. | A changing path can affect timing. Congestion, capture effects and actual disruption are alternatives. Check freshness and exchange completeness first. |
| `offset_valid`, `path_delay_valid`, `telemetry_valid`, `stale_s` | Flags and age of input data. Some legacy flags are inferred from values being present. | Reject invalid/stale inputs for conclusions. A present value is not proof of accuracy; missing data is not healthy zero. |
| `offset_mean`, `offset_std`, `offset_abs_max`, `offset_abs_max_ns` | Mean, population spread or largest absolute offset over a window/report. | Summarizes magnitude, not cause. Window statistics reuse the same underlying observations. |
| `path_delay_mean`, `path_delay_mean_ns`, `pdv_std`, `pdv_std_ns` | Window/report delay average and population delay-variation spread. | Can describe changing timing behavior. The configured 100 ns trigger needs deployment calibration; it is not a universal requirement. |
| `msg_rate_hz`, `msg_rate_mean`, `msg_rate_std` | Packet-rate estimate and its window average/spread. | Can reveal traffic changes; rates depend on protocol settings and capture completeness. |
| `seq_regressions`, `msg_irregularity` | Counts of decreasing sequence values; fraction outside the software's Sync/Announce set. | These are software features, not definitions of malformed or malicious traffic. Normal Follow_Up traffic contributes to this irregularity feature. |
| `grandmaster_identity`, `grandmaster_priority1`, `grandmaster_priority2` | Advertised master identity and priorities, or defaults before an Announce is seen. | Candidate evidence of source selection changes. Check configuration and receiver selection logs before attributing takeover. |
| `grandmaster_clock_class`, `grandmaster_clock_accuracy`, `offset_scaled_log_variance`, `time_source` | Advertised clock-quality/source fields or defaults. | Advertised claims can change without proving actual quality; they are not physical measurements. |
| `steps_removed` | Advertised topology-distance field or default. | Topology changes may explain differences. It is not physical propagation delay. |
| `gm_identity_changes`, `gm_identity_churn`, `clock_class_changes`, `clock_class_improve_jump`, `priority1_changes`, `steps_removed_changes`, `steps_removed_min` | Window transition counts, distinct identities, quality-change feature or minimum. | Describe changing advertised state. Defaults and legitimate failover can produce changes; examine raw Announce and receiver records. |
| `gnss_available`, `gnss_sync_status`, `satellites_tracked`, `holdover` | GNSS/holdover status fields. PCAP processing infers/defaults them; live receiver reports would have different evidence value. | Do not diagnose jamming, antenna failure or actual holdover from PCAP defaults. Satellite -1 means unavailable, not a negative physical count. |
| `gnss_loss_rate`, `gnss_status_changes`, `antenna_fault_rate`, `satellites_drop_max`, `satellites_mean`, `holdover_rate`, `holdover_entry_count` | Window rates, changes, drops and counts derived from the status fields. | Calculating more features from defaults creates no new independent evidence. |
| `synce_ql`, `synce_ql_max` | SyncE quality code and window maximum in the software schema. | Requires actual SyncE status provenance. A schema default cannot establish the frequency reference quality. |
| `freq_error_ppb`, `oscillator_disciplined_tolerance_ppb`, `oscillator_holdover_nominal_ppb`, `oscillator_holdover_tolerance_ppb` | Frequency-error field and configured oscillator assumptions in ppb. | Use calibrated receiver/oscillator measurements before interpreting drift as a physical violation. |
| `drift_vs_declared_state_residual`, `holdover_spec_violation_rate`, `status_behaviour_disagreement`, `offset_step_vs_drift_ratio` | Software comparisons of offset/frequency behavior with state and oscillator assumptions. | A disagreement is relative to those assumptions; it does not independently identify an attack. |
| `gnss_reference_ns`, `ptp_reference_ns`, `peer_reference_ns`, `source_agreement_tolerance_ns` | Reference offsets and configured agreement tolerance. | Require separate, trustworthy reference measurements. Repeated/default zero values are not consensus evidence. |
| `max_pairwise_source_disagreement_ns`, `disagreement_growth_rate`, `n_sources_outside_tolerance`, `minority_source_isolation_score`, `gnss_consensus_residual_ns`, `ptp_consensus_residual_ns`, `peer_consensus_residual_ns` | Cross-reference differences, growth, counts and residual features. | Disabled by default for the single-source setting. Shared bias and correlated reference failures can defeat agreement-based reasoning. |
| `window_start_s`, `window_end_s`, `valid_sample_fraction`, `valid_sample_rate` | Window bounds and usable-input fraction. | A 0.4 s window advanced by 0.2 s shares data with its neighbor. Split experiments before windowing; never count neighboring windows as independent trials. |

External checks support the limits above: linuxptp distinguishes hardware/software timestamps, supports path-asymmetry configuration, uses sequence IDs for matching, and allows different BMCA comparison profiles. Priority fields influence selection, but packet contents alone do not prove receiver state. These settings must match the deployment. [linuxptp ptp4l manual: `-H`, `-S`, `delayAsymmetry`, `check_fup_sync`, `dataset_comparison`, `priority1`](https://www.linuxptp.org/documentation/ptp4l/)

## Labels, decisions and reports

| Which fields | What/how/when | What they can justify |
|---|---|---|
| `label`, `scenario`, `attack_family`, `attack_flag`, `fault_flag`, `is_anomalous` | Scenario assignments, supplied/projected labels or derived software flags, depending on source. | Simulator labels justify simulator evaluation only. Window labels are majority labels; `is_anomalous` uses the software's label convention. None independently proves physical cause. |
| `capture_id`, `run_id`, `pcap` | Source/run references. | Trace evidence, but verify hashes and common capture lineage. Different names do not imply independent experiments. |
| `action`, `reason`, `protective_1of1`, `protective_2of3` | Recorded candidate action, rationale or persistence-based software indicator. | Supports what the software reported. It is not a command execution acknowledgement or measured recovery. |
| `decision_latency_s`, `end_to_end_latency_s`, `within_budget`, `wall_time` | Reported processing time, budget flag or run timestamp. | Software timing only. Preserve timestamp origin and do not turn compute latency into physical recovery duration. |
| `status`, `detail`, `error`, `samples`, `windows` | Run outcome text and source-specific counts. | Helps explain incomplete runs. A successful software status does not establish clock health. |
| `model`, `accuracy`, `precision_macro`, `recall_macro`, `f1_macro`, `roc_auc_h1`, `confusion_matrix` | Historical model/report identifiers and evaluation summaries. | Require known labels, split independence and reproducible evaluation. Preserve historical values without presenting them as freshly validated scores. |

## How to discuss recovery without inventing it

These are conditional engineering proposals based on the current action names in `healing/loop.py`, not observed successful interventions. A row cannot justify them merely because the action exists in code.

| Candidate | Why consider it / when / where | How to justify it before claiming benefit |
|---|---|---|
| `isolate_rogue_master` | Remove an independently established unauthorized timing source at the affected network boundary. | Establish authorization, source identity and a safe remaining timing path. Record command and receiver response. |
| `failover_gnss` | Use an available, trustworthy GNSS reference when the current timing path is compromised. | Obtain receiver status and reference agreement. PCAP-derived GNSS flags are insufficient. |
| `failover_lls_c1`, `failover_lls_c2` | Project candidates for an alternate timing arrangement. | Verify actual topology, supported mode and service timing budget. Names and twin coefficients do not establish hardware availability. |
| `reroute_path` | Consider an alternative path when independent measurements implicate the current path. | Compare delay/asymmetry and a control path; record timing before/after the change. |
| `holdover` | Temporarily rely on a calibrated local oscillator when trustworthy external timing is unavailable. | Bound allowable drift and duration from measurements; verify return to synchronization. |
| `safe_default` | Software fallback when evidence, validity or model confidence is inadequate. | Specify what the deployment actually does. It is not evidence of a physical repair. |

`failover_lls_c3` appears in configuration/model context but is not in the inspected loop's selectable candidate lists. Do not silently treat configured, selectable, executed and effective as the same status.

## One defensible professor exercise

Filter the production supplied-label table for `Label=1`; trace the matching raw records through the existing alignment audit. Count message types and sender addresses. Describe the observed annotation pattern. Explain that this suggests a hypothesis about timing-source behavior, while authorization and receiver impact need independent logs. Do not train a model on the pattern and then call its agreement with the same labels independent validation.

For a fault-versus-benign study, first define the receiver metric and deployment limit, collect a normal-condition comparison and controlled nonmalicious impairments, and preserve independent experiment IDs. For recovery, add command times and receiver measurements before/after plus a control. These are missing-evidence requirements, not fabricated additions to the dataset.
