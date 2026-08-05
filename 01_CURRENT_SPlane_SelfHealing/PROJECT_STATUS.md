# Project Status

**Project:** AI-Native Self-Healing O-RAN Network using a Digital Twin
**Scope:** Open Fronthaul S-plane timing security
**Status:** software feature work closed; Tier 3 hardware validation next
**Tests:** 39 passing

## Final architecture

The shipped configuration uses **28 features** grouped into timing, protocol, message-rate, BMCA, time-source, and oscillator-consistency channels. Group-wise Isolation Forests allocate a combined novelty budget with weighted Šidák shares. RF-H1 and UNKNOWN decisions use 2-of-3 persistence before the governed loop verifies recovery actions in the digital twin.

Raw grandmaster identity, MAC addresses, and other high-cardinality session fingerprints are excluded from model features.

The multi-source simulator and seven cross-source features remain reproducible research artifacts. `features.cross_source.enabled` defaults to `false`, leaving the shipped model at configuration C. Research-only multi-source attacks and benign disagreement confounders do not enter default training or benchmarks.

## Final results

| Domain | Held-out family | Combined protection | Episodes within 2 s |
|---|---|---:|---:|
| Simulator | Spoof | 93.30% | 100% |
| Simulator | Replay | 80.45% | 100% |
| Simulator | DoS | 88.27% | 100% |
| Simulator | GNSS jam | 91.57% | 100% |
| Simulator | Strict unseen GNSS spoof | 0.00% | 0% |
| TIMESAFE | Announce/BMCA | 99.96% | 100% |
| TIMESAFE | Sync/Follow-Up | 99.66% | 100% |
| TIMESAFE | Single-Step Sync | 99.66% | 100% |

TIMESAFE benign false positives are **2.37%** after 2-of-3 persistence, down from 4.49% at 1-of-1, with no loss against the two-second real-episode deadline.

## Validated contributions

- Relative BMCA transitions raised real unseen Announce protection from 23.9% to approximately 100%.
- Group-wise open set recovered unseen DoS from 0% to approximately 94% in the original ablation and improved replay.
- Persistence suppressed isolated alarms while preserving deadline performance.
- Oscillator consistency raised unseen GNSS jam from 0% to 91.57% and produced perfect closed-set GNSS separation.
- Dataset generation, pcap/PTP parsing, Linux/netem harnessing, capture-isolated real evaluation, digital-twin forecasts, and governed recovery remain reproducible on CPU.

## Negative results

1. Receiver-reported GNSS status is attacker-controlled and reduced unseen-family protection instead of solving spoof discrimination.
2. Oscillator consistency detects out-of-envelope jam behavior but strict unseen healthy-looking GNSS spoof remains 0%.
3. Cross-source features added no incremental protection in the evaluated software experiment and regressed established families before being gated off.

Related GNSS families remained in training during the multi-source experiment, so its configuration-C single-source number is not comparable to the strict unseen-spoof result. Coherent all-source compromise has **0.00 percentage-point cross-source gain**, establishing the bound of relative agreement.

## Evidence quality

| Tier | Status | Evidence |
|---|---|---|
| Tier 1 | Complete | Deterministic simulator, labelled scenarios, classifier, twin, governed loop |
| Tier 2 | Complete | Eight-seed statistics, real pcaps, TIMESAFE sessions, linuxptp/netem, open-set and persistence studies |
| Tier 3 | Not started | Hardware timestamps, physical clocks/receivers, authenticated GNSS, O-DU/O-RU |

## Honest limitations

- TIMESAFE contains no benign planned-GM-change session, making deployment FP optimistic for legitimate re-parenting.
- Announce-trained closed-set RF tested on Sync sessions has 0% recall.
- SyncE QL requires live `synce4l` or O-RU M-plane telemetry.
- Real evaluation has few independent sessions and is not production certification.
- No hardware timing source, authenticated GNSS receiver, hardware timestamp NIC, O-DU, or O-RU has been tested.

## Decision

Further single-source feature engineering has reached diminishing returns. The next defensible research step is Tier 3: test independently trustworthy evidence such as Galileo OSNMA or another authenticated GNSS service, a physically independent clock, and hardware-timestamped cross-checking under controlled authorized attacks.
