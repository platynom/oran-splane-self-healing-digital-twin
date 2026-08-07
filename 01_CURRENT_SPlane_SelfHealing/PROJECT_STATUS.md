# Project Status

**Project:** AI-Native Self-Healing O-RAN Network using a Digital Twin
**Scope:** Open Fronthaul S-plane timing security
**Status:** software feature work closed; live Tier-2 validation complete; missing-telemetry fail-open defect fixed and hardened; Tier 3 hardware next
**Tests:** 56 passing after the final regression gate

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
| Tier 2 | Complete | Eight-seed statistics, real pcaps, TIMESAFE sessions, linuxptp/netem (all 4 scenarios ok at 90s duration, 5,665 windows), live pmc recommendation-only loop |
| Tier 3 | Not started | Hardware timestamps, physical clocks/receivers, authenticated GNSS, O-DU/O-RU |

## Live validation checkpoint

- All four live `netem` scenarios (`baseline`, `pdv`, `loss`, `holdover`) now complete cleanly at **90 s duration**, capturing **5,665 real-trace windows** (`baseline`: 2,669, `pdv`: 2,589, `loss`: 392, `holdover`: 15).
- Corrected PDV-aware live run: **600.34 s**, 2,167 valid windows across PDV/loss/holdover; mean latency **0.081 s**, maximum **0.404 s**.
- Live feature coverage: **10/28 nonconstant from pmc** versus **14/28 from pcap**. SyncE QL and physical GNSS/O-RU fields remain unavailable.
- Continuous benign segment achieved **87.60 min**, not the two-hour target. Persisted window FP was **99.993%**, but it was one sustained operator alarm (**0.690 episodes/hour**), exposing a whole-session simulator-to-software-live domain shift.
- Baseline mean latency was **0.176 s**; maximum **1.510 s**; **100%** of measured decisions stayed inside 2 seconds.
- A real two-master planned failover produced **0% H1**. UNKNOWN was already active before the switch, so a hardware-timestamped deployment FP remains unknown.
- Severe-loss holdover exposed a missing-data weakness: zero-valued pmc timing fields bypassed the anomaly threshold and were reported healthy, skipping the open-set layer entirely. **Fixed and hardened** — see below.

## Fail-closed telemetry handling (defect resolved)

The live defect was a fail-**open** gate: absent `pmc` timing became `0.0`, which
`detect()` read as "no anomaly", returning `healthy` *before* the novelty detector,
classifier and persistence ran. It was attacker-inducible (flood the link, silence
the detector). The identical pattern existed in the digital twin, where
`fidelity_score` returned **1.0** — maximum trust — from entirely absent inputs,
disabling the `fidelity < 0.35` conservative fallback.

Missing data is now a first-class state, never a value. Validity flags
(`offset_valid`, `path_delay_valid`, `telemetry_valid`) are carried from ingest
through windowing to the decision gate; absent timing stays `NaN` rather than `0.0`,
so a genuine 0 ns offset stays distinguishable from an unobserved one. The gate
rejects invalid, NaN, non-finite **and provenance-less** windows, routing them to
`UNKNOWN` → `safe_default` on a dedicated `"invalid"` persistence channel.

| Input | Before | After |
|---|---|---|
| All-zero pmc window | `healthy` | `UNKNOWN` + safe_default |
| NaN / non-finite feature | undefined | `UNKNOWN` + safe_default |
| 50% sample loss | `healthy` | `UNKNOWN` + safe_default |
| Window without provenance | `healthy` | `UNKNOWN` + safe_default |
| Genuine healthy traffic | `healthy` | `healthy` (unchanged) |
| Twin fidelity, missing inputs | **1.00** | **0.15** |

Pinned by `tests/test_missing_data_safety.py` (10 tests, written before the fix and
verified failing against the original code). No regression: multi-seed accuracy
**0.991 ± 0.002**, recovery **1.000 ± 0.000**, MTTR **0.933 ± 0.008 s**, twin
Pearson **0.998**. Full design rationale in `docs/FAIL_CLOSED_DESIGN.md`.

**Verified against real linuxptp.** A real `ptp4l` 3.1.1 master/slave pair was run
over veth inside an unprivileged user namespace with `tc netem`. This surfaced a
second, more dangerous manifestation than the original zero-value case: after the
master is killed and the link fully dropped, `pmc` does **not** return zeros or
errors — it keeps serving the *last known* values indefinitely
(`offsetFromMaster 550.0`, `gmPresent true`), with only `portState LISTENING`
telling the truth. A collector trusting the numbers would ingest plausible offsets
throughout a total outage. `live_collect.py` gates on `portState`/GM presence, so
both manifestations are caught. End-to-end on the real captures:

| Real capture | telemetry_valid | Label | Action | Classifier reached |
|---|---|---|---|---|
| Healthy converged slave | `True` | `H0` | `failover_lls_c1` | yes |
| Total loss (stale pmc) | `False` | `UNKNOWN` | `safe_default` | **no** |

The previously recorded residual — "needs a privileged netem re-run to confirm
end-to-end" — is **closed**.

## Honest limitations

- TIMESAFE contains no benign planned-GM-change session. A software two-master test now exists, but its whole-session WSL domain shift prevents a clean hardware-deployment FP estimate.
- Announce-trained closed-set RF tested on Sync sessions has 0% recall.
- SyncE QL requires live `synce4l` or O-RU M-plane telemetry.
- Real evaluation has few independent sessions and is not production certification.
- No hardware timing source, authenticated GNSS receiver, hardware timestamp NIC, O-DU, or O-RU has been tested.
- The two-hour live target was interrupted at 87.60 minutes and is not claimed as complete.

## Decision

Further single-source feature engineering has reached diminishing returns. The next defensible research step is Tier 3: test independently trustworthy evidence such as Galileo OSNMA or another authenticated GNSS service, a physically independent clock, and hardware-timestamped cross-checking under controlled authorized attacks.
