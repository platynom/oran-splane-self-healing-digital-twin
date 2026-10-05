# Dataset-Based Problem Localization

## Decision

The data supports a three-stage root-cause workflow: first identify the changed signal group, then separate harmful H1 behavior from legitimate H0 changes, and finally inspect the mapped physical or protocol location. The dataset does **not** justify claiming that every anomaly is an attack.

Analyzed 57 curated files (73.42 MiB) from `dataset_2026-08-30`. The real TIMESAFE derivatives contain 113,311 H1 packet rows and 4,225 H0 packet rows; the simulator contributes 1,789 labelled event windows plus 2,771 scenario-matched healthy controls.

## Provenance finding

57 of 57 curated bundle files are byte-for-byte identical to canonical files already present in this project. Therefore, `dataset.zip` is a consolidated copy of existing project evidence, **not a new independent validation dataset**. It remains useful as a submission/archive package, but its duplicate rows must not be mixed into training or counted as additional experiments.

## Harmful changes and exact first inspection point

| Change | Evidence signals | Inspect first | Response |
|---|---|---|---|
| Forged superior Announce / grandmaster takeover | `offset_abs_max, gm_identity_changes, priority1_changes` | PTP grandmaster election (BMCA) at the O-DU/O-RU S-plane boundary | Quarantine the unexpected GM; verify Announce source and BMCA attributes. |
| Replayed/out-of-order Sync and Follow-Up messages | `seq_regressions, offset_step_vs_drift_ratio, msg_irregularity` | PTP packet stream on the Open Fronthaul transport path | Block the replay source and reset/revalidate sequence continuity. |
| PTP message-rate flood | `msg_rate_mean, msg_rate_std, msg_irregularity` | S-plane ingress/transport link before the O-DU PTP stack | Rate-limit the offending source while preserving trusted timing traffic. |
| GNSS loss/jamming followed by oscillator holdover | `gnss_loss_rate, holdover_rate, holdover_spec_violation_rate` | GNSS receiver, antenna/RF feed, or local timing source | Switch to a trusted clock/LLS-C source and inspect the GNSS RF chain. |
| Manipulated GNSS time reference | `drift_vs_declared_state_residual, status_behaviour_disagreement, offset_step_vs_drift_ratio` | GNSS time source; corroboration is required outside the receiver | Cross-check with authenticated GNSS or an independent physical clock. |

## Legitimate/degraded changes that must not be treated as attacks

| Change | Classification | Inspect first | Rule |
|---|---|---|---|
| Packet-delay variation / congestion | H0 degradation | Fronthaul switches, queues, link scheduling, or competing traffic | Inspect queue occupancy/QoS and reroute or reprioritize timing packets. |
| Legitimate message-rate burst | H0 confounder | Fronthaul traffic source; not a timing attack by itself | Observe unless timing quality also degrades; do not auto-quarantine. |
| Authorized grandmaster re-parenting | H0 confounder | PTP BMCA/grandmaster redundancy plane | Validate the maintenance/failover ticket and continue monitoring. |
| SyncE quality-level degradation | H0 degradation | Ethernet Equipment Clock / SyncE distribution chain | Trace QL advertisements and switch to the best available EEC source. |
| Benign GNSS loss entering specified holdover | H0 degradation | GNSS availability/local oscillator (within declared holdover envelope) | Monitor holdover duration and drift; escalate only on envelope violation. |

## Real-data cross-checks

### TIMESAFE

The bundle contains independent Announce/BMCA, Sync/Follow-Up replay, and Single-Step Sync sessions. Announce captures localize the disturbance to grandmaster election; the Sync families localize it to PTP sequence/timing delivery. Capture identity must remain the holdout boundary during model evaluation because rows inside a session are highly correlated.

### Linux/netem transport experiments

| Scenario | Rows | Density vs baseline | |offset| p95 ns | PDV std ns | Meaning |
|---|---:|---:|---:|---:|---|
| netem_baseline | 2,669 | 1.000 | 10,102.5 | 2,411.5 | Reference transport behavior |
| netem_pdv | 2,589 | 0.981 | 11,164.6 | 3,020.5 | Delay variation/congestion at the fronthaul transport |
| netem_loss | 392 | 0.147 | 12,021.5 | 2,605.2 | Packet loss/sparse timing delivery on the fronthaul link |
| netem_holdover | 15 | 0.007 | 13,509.0 | 0.000 | Timing-source loss/holdover; only a small observable sample exists |

### Missing/stale telemetry safety defect

Before the fail-closed change, all 73 outage windows were labelled `healthy=73` and persisted protection was 0.00%. After the change, labels became `UNKNOWN=47, PENDING=1` and persisted protection was 97.92%. This localizes the original failure to the **telemetry validity/decision gate**, not to the classifier.

## Operational localization rules

1. BMCA fields change with a large offset step: inspect Announce origin and grandmaster election.
2. Sequence regressions or message irregularity without a GM change: inspect Sync/Follow-Up delivery for replay or reordering.
3. Message rate rises alone: compare with the legitimate traffic-burst control before declaring DoS.
4. PDV/path delay rises while PTP identities remain stable: inspect switches, queues, QoS, and link loss.
5. Satellite count/status and holdover change: inspect GNSS antenna/receiver and oscillator behavior.
6. SyncE QL degrades: inspect the Ethernet Equipment Clock chain, not the GNSS receiver.
7. Telemetry is absent, stale, NaN, or provenance-less: bypass ML and route to UNKNOWN/safe-default.

## What is final and what is not

The dataset is sufficient to finalize the software localization matrix above and to validate replay, Announce takeover, transport impairment, GNSS loss/jam, and telemetry-loss paths. It is not sufficient to certify physical O-DU/O-RU hardware behavior or reliably detect a healthy-looking unseen GNSS spoof. That last case requires authenticated GNSS or an independent physical clock (Tier 3).

## Reproducible outputs

- `scenario_localization.csv`: change-to-location decision matrix.
- `feature_changes.csv`: measured healthy-to-event feature deltas.
- `netem_summary.csv`: real transport-impairment summary.
- `timesafe_session_summary.csv`: real capture/segment boundaries and row counts.
- `dataset_inventory.csv`: file sizes and SHA-256 provenance hashes.
- `duplicate_verification.csv`: byte-level comparison with canonical project evidence.
