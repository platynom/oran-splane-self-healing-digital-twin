# Project Status

**Project:** AI-Native Self-Healing O-RAN Network using a Digital Twin  
**Current focus:** Open Fronthaul S-plane timing security  
**Checkpoint:** Tier 2 realistic software validation

## Goal

Monitor synchronization telemetry, distinguish a benign fault from an attack,
verify candidate recovery actions in a digital twin, and select a governed
response before the approximately two-second failure window.

## Validation tiers

| Tier | Status | Meaning |
|---|---|---|
| Tier 1 | Complete | Deterministic PTP/SyncE simulator and end-to-end healing loop |
| Tier 2 | Complete | Multi-seed statistics, real pcap ingestion, Linux/netem traffic, public-data calibration |
| Tier 3 | Future work | Hardware timestamps, physical clocks, SyncE and O-DU/O-RU validation |

## Data realism

- **Simulator:** synthetic but deterministic timing physics and injected labels.
- **Linux/netem:** real `ptp4l` packets over an emulated impaired link.
- **TIMESAFE:** released testbed captures containing real PTP attack traffic.
- **Hardware:** not yet evaluated.

## Leakage-resistant real-data results

Complete capture sessions are assigned to either train or test, never both.
Confidence intervals and exact counts are available in the calibration report.

| Evaluation | Benign FP | Attack TP |
|---|---:|---:|
| Simulator-trained RF on real captures | 100% | 100% |
| Real-calibrated threshold | 2.0% | 100% |
| Real-trained RF, session holdout | 2.0% | 100% |
| Held-out Announce family | 0% | 23.8% |
| Held-out Sync/Follow_Up family | 0% | 100% |
| Held-out one-step Sync family | 1.9% | 100% |

## Simulated novel-family results

| Held-out attack family | RF-only recall |
|---|---:|
| Spoof | 89.4% |
| Replay | 43.0% |
| DoS/message flooding | 0.0% |

The DoS family is detected at 100% recall on held runs when represented in
training, with 0% false positives on the overlapping benign `traffic_burst`
scenario. A naive rate threshold flags both classes, while leave-one-family-out
DoS recall is 0%; this is now a measured novelty-detection target.

The simulator-trained model is unusable on real data because it flags
everything. Real calibration closes that gap for known families. Generalization
to unseen Announce attacks remains weak and is the primary research limitation.

## Feature coverage

Eleven of the twelve model features vary on real captures. SyncE quality remains
unavailable from pcaps and requires live `synce4l` or O-RU M-plane telemetry.
Announce parsing now exposes clock class and time source, and packet-level
message types make protocol-mix features real. Trailing one-second PTP packet
counts provide real message-rate mean and variance features.

## Next steps

1. Add open-set novelty detection so unseen attack families route to a safe response.
2. Add grandmaster-identity, priority, clock-class-transition and
   steps-removed features to improve unseen Announce detection.
3. Validate live `pmc` and `synce4l` collection on a persistent Linux setup.
4. Integrate hardware-timestamping NICs and representative O-RAN equipment.

This is a validated research prototype, not a production-certified timing
security system.
