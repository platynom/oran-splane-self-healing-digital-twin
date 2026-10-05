# V5 independent verification log

**Audit date:** 2026-09-28  
**Deck audited:** `deliverables/ORAN_SPlane_PRISM_Review_v4.pptx`  
**Method:** independent recomputation from the corrected campaign archive, direct inspection of the ML comparison JSON and its per-run rows, direct parsing of all ptp4l servo logs, inspection of the deck text and speaker notes, code/configuration review, and external checks against primary standards or first-party publications. The prior audit file was deliberately not opened until this log was completed.

## Executive result

| Status | Count |
|---|---:|
| PASS | 26 |
| FAIL | 13 |
| UNVERIFIABLE | 2 |
| **Total checks** | **41** |

The statistical headline results are reproducible. The main corrections are: the evidence archive does not contain the claimed per-run PCAPs; specificity excluding `B_bc_replacement` is 47/48 = 0.979, not 1.000; the measured C1 interpolation crosses 0.500 at 60.54%, not approximately 62%; the C1 axis describes the post-warmup fault window, not the whole observation window; several standards statements need tighter wording; the exact requested companion workbook is absent.

## Evidence identity and scope

- Archive: `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/gap_coverage_2026-09-20/corrected_final/splane_campaign_CORRECTED_2026-09-20.tgz`
- SHA-256: `6149b4fb15940cdac694ba8666d97041b4eb62d5523d2631c1edf96d531e4ed9` — exact match.
- Tar entries: 1,096 — exact match.
- Run directories: 168 = 14 scenarios × 12 replicates.
- Extraction scratch directory: `C:\Users\Admin\AppData\Local\Temp\codex_prism_v5_audit` (outside the repository).
- Deck text and notes extracted to `.codex_build/prism_v5/deck_v4_text_and_notes.md` before any conclusion was formed.

## 41-check verdict table

| # | Status | Independent finding |
|---:|:---:|---|
| 1 | **FAIL** | Hash, 1,096 entries, 168 run directories, `context.json`, `decision.json`, and `decision_v3.json` pass. However, none of the run directories contains files literally named `ptp.pcap` or `ptp.deep.csv`; the archive retains scenario-named downstream deep CSVs and no PCAPs. The archive's own correction report also describes it as deep CSVs plus decisions/scripts, not full packet captures. |
| 2 | **PASS** | Frozen-base and v3 verdict counts were recomputed from every per-run decision JSON; full table is below. |
| 3 | **PASS** | v3 macro sensitivity = mean of eight scenario recalls = 0.989583; macro specificity = mean of five scenario specificities = 0.783333; abstention = 12/12 = 1.000; attribution = 84/96 = 0.875. |
| 4 | **PASS** | `evaluate_v4.py` computes unweighted per-scenario macro means. Pooled Wilson intervals are explicitly labelled run-count-dependent and are not substituted for macro metrics. |
| 5 | **PASS** | All 12 `B_unplanned_failover` runs return `UNKNOWN` via the substantive `fault_hint == "B2?"` path; zero error-path abstentions. |
| 6 | **PASS** | Attribution denominator is all 96 attack runs. With the evaluator's disclosed aliases (`A_intercept→C1`, `A_malformed→C2`, `A_wholesecond→C3`), v3 gets 84/96 and the frozen rule gets 53/96. |
| 7 | **PASS** | Independently recomputed 95% Wilson intervals: 84/96 = [0.794115, 0.927028]; 36/60 = [0.473661, 0.714305]; 72/96 = [0.654902, 0.825860]. |
| 8 | **PASS** | v2 and v3 verdicts are identical on all 168 scored downstream captures. Relative to frozen base, v3 has 35 escalations, all in C1/C2/C3, and zero ATTACK→non-ATTACK regressions. |
| 9 | **FAIL** | Excluding `B_bc_replacement`, benign specificity is **47/48 = 0.979167**, not 1.000, because `B3_pdv_congestion__r4` returns `UNKNOWN`. |
| 10 | **PASS** | B3 miss: replicate 4, `UNKNOWN`, hint `B2?`. `B_bc_replacement`: all 12 are `ATTACK`, hint `A8`, caused by the single expected-BC identity policy. |
| 11 | **PASS** | `random.Random(rep)` gives C1 levels over reps 1–12 as: 75, 75, 70, 65, 75, 75, 70, 75, 70, 65, 75, 60%. Distribution: 60%×1, 65%×2, 70%×3, 75%×6. |
| 12 | **PASS** | No 55% C1 run exists in the 12-replicate campaign. |
| 13 | **PASS** | Recomputed directly from every C1 deep CSV using `decision_rule_v3.py`'s all-row capture span and frames/span logic. Sync ratios by level: 60%=0.504889; 65%=0.459859 median; 70%=0.413656 median; 75%=0.366530 median. |
| 14 | **PASS** | C1 replicate counts are exactly n=1,2,3,6 at 60,65,70,75%. Decisions: 60% 0/1 caught; 65% 2/2; 70% 3/3; 75% 6/6. |
| 15 | **PASS** | D1 threshold is exactly `RATE_STARVE_FRACTION = 0.5`; firing requires observed rate `< 0.5 × declared rate`, plus the v3 persistence/minimum-frame guards. |
| 16 | **FAIL** | Linear interpolation between the recomputed adjacent medians (60%, 0.504889) and (65%, 0.459859) crosses 0.500 at **60.54%**. Calling that “approximately 62%” is not a linear interpolation; 62.5% is merely the midpoint of the tested bracket. |
| 17 | **PASS** | `campaign_v3.sh` calls C1 with duration 44 s. `run_gap.sh` uses 8 s warm-up and 36 s post-warm-up; at 55%, `DOWN=floor(36×0.55)=19`, tail=17, so 25/44 of the full run remains available (=0.568 before edge effects). That predicts a miss against the 0.5 rate threshold. |
| 18 | **FAIL** | The deck's axis “Fraction of the observation window blackholed” is wrong. `c1_down_pct` is the fraction of the **post-warm-up fault window** blackholed; the observed/declared rate is measured over the full captured span. |
| 19 | **PASS** | ML arithmetic: 168 run directories; 48 missing `pmc.jsonl`; 36 context-replicate mismatches; parser 1,008 attempted files, 672 parsed, 13,512 rows; 6,250 windows total; 3,847 train-known; 2,081 test-all; 1,923 test-known. Split reps 1–8 vs 9–12, no overlap. |
| 20 | **PASS** | Paired exact two-sided McNemar recomputation over the same 56 held-out runs: rule vs ML b/c=31/4, p=3.465×10⁻⁶; rule vs OR=1/0, p=1.000; rule vs rule-first=4/0, p=0.125; rule vs consensus=27/0, p=1.490×10⁻⁸; ML vs always-BENIGN=5/1, p=0.21875. The OR and rule-first point estimates are lower but not distinguishable from the rule at this sample size. |
| 21 | **PASS** | ROC-AUC 0.603792 is a **per-window** closed-set RF metric on 1,923 overlapping known-scenario test windows (0.4 s windows, 0.2 s step), not a per-run AUC. |
| 22 | **PASS** | Exact held-out accuracies: rule 51/56=0.910714; ML 24/56=0.428571; always-BENIGN 20/56=0.357143; OR 50/56=0.892857; rule-first 47/56=0.839286; consensus 24/56=0.428571. |
| 23 | **PASS** | 28 feature columns are configured, but the harness explicitly selects and trains on only six populated columns: offset mean/std/max, path-delay mean, PDV std, and holdover rate. |
| 24 | **PASS** | RF impurity importances: offset_abs_max 0.267588; path_delay_mean 0.261517; offset_std 0.208277; pdv_std 0.138827; offset_mean 0.123790; holdover_rate 0.000000. |
| 25 | **PASS** | Direct parsing of all held-out-source ptp4l logs: baseline 1,056 samples, mean |offset| 1,866.252 ns (88/run); C1 534 samples, mean 1,583.672 ns (44.5/run); C3 336 samples, mean 1,764.598 ns (28/run). |
| 26 | **PASS** | Held-out per-scenario ARM-B verdicts match the JSON. Key checks: A1 0/4; A2 0/4; A3 1/4; A5 1/4; A8 1/4; C1 0/4; C2 1/4; C3 1/4; baseline 4/4; B2 4/4; B3 3/4; B7 4/4; B_bc_replacement 4/4; unplanned failover 0/4. |
| 27 | **PASS** | The 48 missing `pmc.jsonl` runs are 12 each in B3/C1/C2/C3. All 36 C-series contexts record `rep=901`; the ML split correctly uses the directory-name replicate. |
| 28 | **UNVERIFIABLE** | Six daemon launch commands, two bridges, two capture commands, and 56 extracted CSV columns are directly verified. Domain/rate/priority fields are visible in data/code. But the actual `cfg/*.cfg` files referenced by the campaign are not present in the corrected archive, so the complete runtime configuration (including timestamping and dataset-comparison settings) cannot be independently reconstructed from this evidence bundle alone. |
| 29 | **UNVERIFIABLE** | `docs/comparison_notes_and_results.xlsx` does not exist anywhere under the repository root. Its formulas, rounding, and stale netem justification therefore cannot be audited or corrected. |
| 30 | **FAIL** | Deck-level consistency issues exist: slide 7 notes say all milestones except paper/IP are closed while the slide shows M3 and M5 partial; slide 20's ~62% interpolation is wrong; slide 20's axis is wrong; slide 9 implies retained PCAP evidence that the archive does not contain; slide 10 says standards values required secondary sources although current official ITU text is publicly accessible; several standards claims lack direct citations. |
| 31 | **FAIL** | 130 ns is supported by ETSI TS 103 859/O-RAN WG4 for 5G FR2 intraband-contiguous carrier aggregation and is associated with **Timing Category A**. The deck's generic “Category-A relative alignment target between radio units” is too broad and can be confused with O-RU functional Category A. |
| 32 | **FAIL** | ITU-T G.8271.1 supports ±1.5 μs as an end-application/reference-point-E absolute time-error limit relative to a common recognized time standard. “From O-RU to PRTC” is not the recommendation's wording and reverses/muddles the reference model. |
| 33 | **PASS** | TIMESAFE reports a production-ready O-RAN/5G base-station catastrophic failure within 2 seconds of spoofing. It is now published in *ACM Transactions on Privacy and Security*, vol. 29 issue 1, DOI `10.1145/3775060`; it is no longer only an arXiv preprint. |
| 34 | **FAIL** | Current ITU-T G.8275.1 material is accessible from ITU and directly confirms domain 24–43, fixed priority1=128 and ignored for Alternate BTCA, Sync 16/s, Announce 8/s, Ethernet transport, and alternate BTCA. The deck's blanket “paywalled; vendor notes required” statement is outdated/overbroad. |
| 35 | **FAIL** | ETSI TR 104 106 directly covers DoS against a master (T-SPLANE-01), master spoofing (02), rogue PTP instance (03), selective removal (04), and delay manipulation (05). The repository matrix incorrectly maps A4 delay to T-SPLANE-04 rather than 05 and loosely maps replay to 04; therefore the 16-class taxonomy is project-defined and only partially aligned, not a direct ETSI taxonomy. |
| 36 | **PASS** | G.8275.1 supports clockClass 6 for a T-GM locked to a PRTC/GNSS and clockClass 7 for a T-GM in holdover **while within the configured holdover specification**. The transition must be stated with that condition. |
| 37 | **FAIL** | “A coherent GNSS spoof is undetectable” is too absolute. The project's ptp4l-only single-reference telemetry cannot establish it, but published RF-domain, oscillator, multi-antenna, multi-constellation, IMU, or independent-time-source methods can detect classes of spoofing. The defensible claim is that confident detection is not established by this testbed and needs additional trusted/RF evidence. |
| 38 | **FAIL** | In two-step PTP, `twoStepFlag=TRUE` means the receiver uses the associated Follow_Up timestamp and must not use Sync's `originTimestamp`. IEEE/ITU wording does not require that field itself to be zero; zero is common practice, not a universal legality rule. |
| 39 | **FAIL** | G.8275.1's Alternate BTCA ignores priority1 for selection (fixed 128) and treats `controlField` as an ignored field. The v3 detector's `control>5` reason is therefore not a G.8275.1 profile-legality discriminator. C2 still contains independently invalid evidence (`versionPTP=3`, illegal/reserved messageType, short length), so the 12/12 C2 verdict survives but the rationale must be narrowed. |
| 40 | **PASS** | The project's measured baseline mean |offset| is 1.866 μs under software timestamping, which is far above a 130 ns radio-alignment target. External Linux/PTP sources also explain why hardware timestamping removes variable NIC/software-path latency. This supports a testbed-specific realism limit, not a universal claim that all software timestamping is always microsecond-level. |
| 41 | **FAIL** | Several slide text and notes assertions are uncited or point only to broad overview URLs. Citations must be added directly to the relevant standards/result notes, and outdated source-status statements removed. |

## Full campaign verdict counts

Counts are shown as `ATTACK / BENIGN / UNKNOWN` across 12 runs.

| Scenario | Expected | Frozen base | v3 |
|---|---|---:|---:|
| baseline | BENIGN | 0 / 12 / 0 | 0 / 12 / 0 |
| A1_rogue_master | ATTACK | 12 / 0 / 0 | 12 / 0 / 0 |
| A2_sync_spoof | ATTACK | 12 / 0 / 0 | 12 / 0 / 0 |
| A3_replay | ATTACK | 12 / 0 / 0 | 12 / 0 / 0 |
| A5_dos_flood | ATTACK | 12 / 0 / 0 | 12 / 0 / 0 |
| A8_rogue_bc | ATTACK | 12 / 0 / 0 | 12 / 0 / 0 |
| B2_gm_failover | BENIGN | 0 / 12 / 0 | 0 / 12 / 0 |
| B_bc_replacement | BENIGN | 12 / 0 / 0 | 12 / 0 / 0 |
| B3_pdv_congestion | BENIGN | 0 / 11 / 1 | 0 / 11 / 1 |
| B7_topology_change | BENIGN | 0 / 12 / 0 | 0 / 12 / 0 |
| B_unplanned_failover | UNKNOWN | 0 / 0 / 12 | 0 / 0 / 12 |
| C1_removal | ATTACK | 0 / 12 / 0 | 11 / 1 / 0 |
| C2_malformed | ATTACK | 0 / 12 / 0 | 12 / 0 / 0 |
| C3_wholesecond | ATTACK | 0 / 12 / 0 | 12 / 0 / 0 |

## C1 boundary recomputation

| Post-warm-up blackhole setting | n | Reps | Median Sync observed/declared | Verdict |
|---:|---:|---|---:|---|
| 60% | 1 | 12 | 0.504889 | missed |
| 65% | 2 | 4, 10 | 0.459859 | 2/2 caught |
| 70% | 3 | 3, 7, 9 | 0.413656 | 3/3 caught |
| 75% | 6 | 1, 2, 5, 6, 8, 11 | 0.366530 | 6/6 caught |

Linear crossing: `60 + (0.504889 - 0.500)/(0.504889 - 0.459859) × 5 = 60.54%`.

## Source-backed standards corrections

- O-RAN/ETSI CUS-plane timing requirements: [ETSI TS 103 859 V7.0.2, section 11.2.5.4 and Tables 11-1/11-2](https://www.etsi.org/deliver/etsi_ts/103800_103899/103859/07.00.02_60/ts_103859v070002p.pdf)
- ITU-T time-error limits: [ITU-T G.8271.1](https://www.itu.int/rec/T-REC-G.8271.1/)
- G.8275.1 domain, message-rate and Alternate-BTCA profile rules: [ITU-T G.8275.1](https://www.itu.int/rec/T-REC-G.8275.1/)
- O-RAN threat identifiers: [ETSI TR 104 106 V3.0.0](https://www.etsi.org/deliver/etsi_tr/104100_104199/104106/03.00.00_60/tr_104106v030000p.pdf)
- TIMESAFE: [ACM DOI 10.1145/3775060](https://doi.org/10.1145/3775060) and [arXiv 2412.13049](https://arxiv.org/abs/2412.13049)
- IEEE 1588 status and amendments: [IEEE 1588 Working Group public documents](https://sagroups.ieee.org/1588/public-documents/). Exact normative text is paywalled; clause-specific interpretations in this audit were cross-checked against accessible ITU profile text and NIST/IEEE working-group material.
- Linux timestamping model: [Linux kernel timestamping documentation](https://docs.kernel.org/networking/timestamping.html)
- GNSS detection evidence: [NIST hardware-oscillator spoofing detection](https://www.nist.gov/publications/detecting-gnss-spoofing-using-network-hardware-oscillators) and [NIST GNSS time traceability discussion](https://tf.nist.gov/general/pdf/3217.pdf)

## Deck corrections required for V5

1. Change the C1 crossing from “~62%” to **60.54% interpolated (tested bracket: 60–65%)** and relabel the axis as the post-warm-up fault window.
2. State specificity without `B_bc_replacement` as **47/48 = 0.979**, not 1.000.
3. Qualify 130 ns as the 5G FR2 intraband-contiguous CA relative-TAE case associated with Timing Category A.
4. Reword 1.5 μs as the end-application/reference-point-E absolute time-error limit relative to a recognized common time standard.
5. State that the retained corrected archive contains deep CSVs and decisions, not PCAPs, even though campaign scripts configured tcpdump on both bridges.
6. Narrow C2 legality wording: `controlField` is ignored by G.8275.1; the detected injected frames remain malformed because of independent invalid fields.
7. Replace the absolute GNSS-undetectability claim with a testbed-scoped claim.
8. Fix slide 7 speaker-note status contradiction and add direct authoritative citations.
9. Preserve ARM-B/always-BENIGN wording: p=0.21875, not distinguishable at n=56; B_bc_replacement is not a unique ML capability.

