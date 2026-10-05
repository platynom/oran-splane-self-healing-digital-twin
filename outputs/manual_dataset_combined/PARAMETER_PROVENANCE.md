# Active parameter provenance map

Scope: current software pipeline only. This is not a claim that a value in a processed TIMESAFE row was physically measured. The map is based on `ingest/pcap_ingest.py`, `ingest/schema.py`, `telemetry/features.py`, `config/default.yaml`, `healing/loop.py`, and `twin/model.py` as inspected on 2026-09-07.

## How to read this map

WHAT is the field or calculation. WHICH code produces or consumes it. WHERE is its measurement point. WHEN says when it is available. WHY/HOW says what the value may support and the material limit.

| Parameter(s) | What / unit | Produced from | Consumer | Limit that prevents overclaiming |
|---|---|---|---|---|
| `t_s` | Seconds from the first decodable PTP packet in a capture | Calculated from PCAP capture timestamps | Windows, session linkage | Capture-time origin, not UTC or a cross-capture join key. |
| `offset_ns` / `measured_offset_ns` | Calculated PTP offset, nanoseconds | Formula `offset=(t2-t1-correction)-meanPathDelay`; `t2/t3` are capture times, PTP payload supplies `t1/t4` | Timing features, threshold, twin | Not a hardware receiver measurement unless capture timestamps are known hardware timestamps. Schema copies `offset_ns` into `measured_offset_ns` when absent. |
| `path_delay_ns` / `pdv_ns` | Calculated mean path delay and deviation, nanoseconds | End-to-end PTP exchange; `pdv_ns=path_delay_ns-median` if absent | Features, threshold, validity | Can use last-known path delay or 0 while incomplete; marked `holdover`, but it is not a newly observed delay. |
| `offset_valid`, `path_delay_valid`, `telemetry_valid`, `stale_s` | Validity flags and staleness seconds | Parsed live adapter values or schema inference from non-null timing fields | Window validity and fail-closed healing check | Legacy/PCAP rows infer validity from presence of values. This proves only a value exists, not traceable physical calibration. |
| `ptp_seq_id`, `ptp_msg_type`, `msg_rate_hz` | Packet sequence ID, PTP message type, messages in trailing one-second capture interval | Parsed PTP packet fields / capture timestamps | Protocol/rate features | Packet parsing is evidence of packet contents, not sender authorization or clock health. |
| BMCA Announce fields: `grandmaster_identity`, `priority1`, `clock_class`, `clock_accuracy`, `offset_scaled_log_variance`, `priority2`, `steps_removed`, `time_source` | Current Announce dataset values, identifiers/codes | Parsed from most recent Announce; schema defaults when unseen | BMCA-change features | Values are packet-advertised claims. Defaults (`unknown`, 128, 248, 254, 65535, 0, 160) are placeholders and must not be treated as observed network state. |
| `gnss_sync_status`, `satellites_tracked`, `gnss_available`, `holdover` | Receiver synchronization state, satellite count, availability and holdover flag | Live `pmc`/O-RU status parser when available; PCAP ingestion infers limited holdover from stale delay/clock class and schema defaults GNSS status to `BOOTING`, satellites to -1 | Timesource and consistency features | PTP PCAP has no receiver GNSS state. `BOOTING`, -1, `True`, and `False` defaults are unavailable/inferred fields, not measurements. |
| `synce_ql` | Project rank 1–4 for parsed SyncE quality level | Live `synce4l` text parser; schema default 1 | `synce_ql_max` | A default rank 1 does not demonstrate SyncE quality in a PCAP. |
| `freq_error_ppb`; oscillator nominal/tolerances | Frequency error and configured oscillator envelope, ppb | Live source/simulator; schema defaults 0, 6, 2, 1.5 | Consistency features | Defaulted values model an envelope; they are not a measured oscillator calibration. |
| `gnss_reference_ns`, `ptp_reference_ns`, `peer_reference_ns`, `source_agreement_tolerance_ns` | Three reference values and a comparison tolerance, ns | Simulator/live multisource telemetry; schema defaults references to 0 and tolerance to 20 | Seven disabled cross-source features | A single-source PCAP cannot reconstruct independent references. With defaults, a zero disagreement is an artifact, not agreement. Cross-source features are disabled by default. |
| `scenario`, `run_id`, `label`, `attack_flag`, `fault_flag` | Bookkeeping / software labels | Simulator inputs, ingestion caller, or source annotation projection | Dataset splitting/training/reporting | Not physical observations. TIMESAFE projected H0/H1 sessions are gated out unless future traceable evidence validates measured clock-health semantics. |

## Window features (0.4 s window, 0.2 s step by default)

All features below are calculated by `window_features`; they summarize records within a time interval. A window may share source records with adjacent windows, so adjacent rows are not independent samples.

| Feature group | Features | How / consumer | Limit |
|---|---|---|---|
| Timing | `offset_mean`, `offset_std`, `offset_abs_max`, `path_delay_mean`, `pdv_std` | Aggregate of valid timing values; `offset_abs_max` and `pdv_std` are compared to the configured 100 ns detector trigger | Only supports behavior of the calculated capture-derived timing series; no universal service budget follows. Invalid windows carry non-finite timing summaries and route to `safe_default`. |
| Protocol/rate | `seq_regressions`, `msg_irregularity`, `msg_rate_mean`, `msg_rate_std` | Packet order, accepted Sync/Announce proportion, and parsed rate | Association with an attack is not proof of maliciousness; traffic mix and capture loss are alternatives. |
| BMCA | `gm_identity_changes`, `gm_identity_churn`, `clock_class_changes`, `clock_class_improve_jump`, `priority1_changes`, `steps_removed_changes`, `steps_removed_min` | Transitions and minima of parsed Announce fields | Packet-advertised state may be missing/defaulted. It does not establish an authorised master or recovery. |
| Timesource | `gnss_loss_rate`, `holdover_rate`, `gnss_status_changes`, `antenna_fault_rate`, `satellites_drop_max`, `satellites_mean`, `holdover_entry_count` | Counts/rates from live status fields | PCAP defaults make these unavailable or inferred. They cannot support GNSS or antenna conclusions without live status provenance. |
| Consistency | `drift_vs_declared_state_residual`, `holdover_spec_violation_rate`, `status_behaviour_disagreement`, `offset_step_vs_drift_ratio` | Compare frequency/offset behavior to configured oscillator parameters and declared status | These are model/configuration comparisons, not independent calibration or fault diagnosis. |
| Cross-source (disabled) | `max_pairwise_source_disagreement_ns`, `disagreement_growth_rate`, `n_sources_outside_tolerance`, `minority_source_isolation_score`, `gnss_consensus_residual_ns`, `ptp_consensus_residual_ns`, `peer_consensus_residual_ns` | Three-reference calculations, enabled only by `features.cross_source.enabled=true` | Do not enable for a single-source PCAP or default-filled references; it would create false agreement. |

## Decision and recovery parameters

| Parameter | Current code behavior | Evidence status |
|---|---|---|
| `healing.anomaly_threshold_ns=100` | `offset_abs_max > 100` or `pdv_std > 100` enters anomaly handling | Configured detector trigger. It is neither a universal O-RAN requirement nor a calibrated production threshold. |
| `openset.persistence n=2, m=3` | Requires persistence for novel/H1 candidates | Configured decision rule; validate separately on each deployment. |
| `decision_budget_s=1.0`, `failure_window_s=2.0` | Measures software decision time / simulation evaluation window | Software configuration; does not prove physical recovery deadline. |
| `ACTION_EFFECT` coefficients and fidelity | Twin forecasts action decay/floor from hard-coded coefficients; fidelity penalizes PDV, irregularity, and regressions | Modeled forecast only. No recorded execution or before/after control establishes physical effectiveness. |
| Candidate actions | Loop chooses from attack/fault candidate lists; configuration contains an additional `failover_lls_c3` | “Selectable/configured” is not “available on hardware,” “executed,” or “successful.” Invalid telemetry and low fidelity fall back to `safe_default`. |

## Missing evidence needed to promote a claim

For production-grade clock-health, GNSS, SyncE, or recovery claims, retain capture timestamp provenance, receiver-side `pmc`/O-RU M-plane status, oscillator/reference calibration, action command logs, and before/after timing measurements with a control. Without them, the relevant field remains parsed, calculated, inferred, defaulted, or simulated as stated above.

## Executed smoke check

On 2026-09-07, the configured production PCAP passed through `pcap_to_telemetry` without writes. The transform emitted 13,562 rows from the 13,565-packet capture. All emitted rows had timing-present validity, while `gnss_sync_status` was `BOOTING`, `satellites_tracked` was `-1`, and `gnss_reference_ns` was `0.0`. This confirms the documented PCAP/default behavior; it does not validate a live GNSS or reference observation.
