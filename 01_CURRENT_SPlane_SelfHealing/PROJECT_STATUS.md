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

The simulator-trained model is unusable on real data because it flags
everything. Real calibration closes that gap for known families. Generalization
to unseen Announce attacks remains weak and is the primary research limitation.

## Feature coverage

Nine of the ten model features vary on real captures. SyncE quality remains
unavailable from pcaps and requires live `synce4l` or O-RU M-plane telemetry.
Announce parsing now exposes clock class and time source, and packet-level
message types make protocol-mix features real.

## Next steps

1. Add grandmaster-identity, priority, clock-class-transition and
   steps-removed features to improve unseen Announce detection.
2. Validate live `pmc` and `synce4l` collection on a persistent Linux setup.
3. Integrate hardware-timestamping NICs and representative O-RAN equipment.

This is a validated research prototype, not a production-certified timing
security system.
