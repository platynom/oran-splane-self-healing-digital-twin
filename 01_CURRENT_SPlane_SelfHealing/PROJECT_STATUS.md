# Project Status

**Project:** AI-Native Self-Healing O-RAN Network using a Digital Twin  
**Scope:** Open Fronthaul S-plane timing security  
**Checkpoint:** Tier 2 realistic software validation, 28 tests passing

## Goal

Detect synchronization anomalies, distinguish benign faults from known attacks,
route novel events to a safe response, verify candidate recovery actions in a
digital twin, and act within the approximately 2.0 s failure window.

## Validation tiers

| Tier | Status | Evidence |
|---|---|---|
| Tier 1 | Complete | Deterministic PTP/SyncE/GNSS simulator and end-to-end governed healing loop |
| Tier 2 | Complete | Multi-seed statistics, pcap ingestion, Linux/netem traffic, TIMESAFE capture-isolated evaluation |
| Tier 3 | Not started | Hardware timestamps, physical clocks, live SyncE and representative O-DU/O-RU validation |

## Current architecture

The discriminator uses **19 features**. Timing, delay/PDV, protocol regularity,
message rate, GNSS/holdover/SyncE state, and relative BMCA/grandmaster transition
features are represented. Raw grandmaster identities and MAC addresses remain
telemetry-only to prevent capture fingerprinting.

Known H0/H1 classification is supplemented by a **group-wise open-set
ensemble**. Timing, protocol, rate, and BMCA Isolation Forests are independently
scaled and fitted; a weighted Šidák budget targets an approximately 2% combined
known-window novelty rate. Novel events route to the conservative safe default.

The live decision wrapper applies **2-of-3 temporal persistence** independently
to UNKNOWN and H1 votes. A 1-of-1 mode reproduces raw model behavior.

## Current results

### Combined protection after 2-of-3 persistence

| Domain | Held-out attack family | Window protection | Attack episodes within 2 s |
|---|---|---:|---:|
| Simulator | Spoof | 83.8% | 91.7% |
| Simulator | Replay | 63.7% | 100% |
| Simulator | DoS/message flooding | 86.0% | 100% |
| TIMESAFE | Announce/BMCA | 99.96% | 100% |
| TIMESAFE | Sync/Follow-Up | 99.66% | 100% |
| TIMESAFE | Single-step Sync | 99.66% | 100% |

All real attack episodes are detected within **0.2 s**. Simulated spoof is the
worst within-window result at **91.7%**; its missed deadline is already present
at 1-of-1 and is not introduced by persistence.

Weighted TIMESAFE benign window FP is **2.37%** at 2-of-3, down from 4.49% at
1-of-1. Persisted-window alarms/hour fall from about 807 to 427. De-duplicating
contiguous positives into operator-facing episodes gives about 570 to 190
episodes/hour. Hourly rates are extrapolated from short held captures.

## Evidence quality

- Simulator scenarios are synthetic, deterministic, and automatically labelled.
- Linux/netem produces real `ptp4l` packets over emulated impaired links.
- TIMESAFE provides public testbed PTP attack captures, evaluated with complete
  capture sessions isolated between train and test.
- BMCA parsing includes clock class, priority, accuracy, grandmaster identity,
  `stepsRemoved`, and time source. Only relative transitions and plausibility
  values enter the model.
- The planned-grandmaster-failover confounder has 0% RF-H1 and novelty FP in the
  held simulated run, but no equivalent benign TIMESAFE session exists.

## Honest limitations

- TIMESAFE has no benign GM-change session, so deployment FP under legitimate
  re-parenting may be higher than measured.
- Closed-set specialization persists: Announce-trained RF tested on Sync
  sessions gives **0% recall**.
- SyncE quality level still requires live `synce4l` or O-RU M-plane telemetry;
  it cannot be recovered from ordinary PTP pcaps.
- Real evaluation has few independent attack episodes. Percentages should not
  be read as production certification.
- No hardware timestamping NIC, physical timing source, O-DU, or O-RU has been
  validated yet.

## Next engineering steps

1. Collect benign planned-GM-change sessions and longer benign captures to
   measure operator alarm rates without short-trace extrapolation.
2. Validate live `pmc` event subscription and `synce4l` quality-level ingestion.
3. Expand capture-isolated testing across independent equipment and topologies.
4. Execute Tier 3 with hardware timestamps, real SyncE/GNSS sources, and
   representative O-RAN equipment.

This is a reproducible and validated research prototype, not a
production-certified timing-security product.
