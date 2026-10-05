# Fact-check: ORAN_SPlane_PRISM_Review_v4.pptx

**File audited:** `C:\Users\Admin\Downloads\ORAN_SPlane_PRISM_Review_v4.pptx` (609,450 bytes, modified 2026-09-28 15:11, 26 slides)
**Audited:** 2026-09-28
**Method:** every measured figure recounted from the raw per-run files in the live testbed (`/opt/sptb/cap/*__r*`, 168 run directories) rather than from any summary document; every standards figure checked against primary or authoritative secondary sources; deck text audited for internal contradiction by a separate adversarial pass.

---

## Bottom line

The **measured numbers are sound**. I recounted every results figure from the raw run files and all of them reproduce exactly. The deck's disclosure discipline is unusually good — it volunteers its own fabricated-data defects, the post-observation rule revision, the paywalled-citation problem and the platform ceiling.

Three classes of problem remain:

1. **Eight statements are factually wrong** — not the numbers themselves, but claims *about* the numbers, two cross-references, one standards clause, and one capability the testbed does not have. All are fixable by editing text.
2. **The deck is silent on two worklet objectives and all four expected outcomes.** Objectives 2 (fault prediction) and 4 (automated corrective action) are neither claimed nor listed as remaining work; no MTTR / recovery-time / availability figure appears anywhere. A mentor reading against the worklet card will find this.
3. **Roughly twenty precision defects** — metrics without a unit of analysis, one value quoted where two exist, and several standards attributions that are right in substance but imprecise in wording.

Nothing in the deck is fabricated. Nothing in it is unsupported by data we actually hold. The defects are of framing, not of evidence.

---

## TIER 1 — Factually wrong. Fix before presenting.

### 1.1 "A single known failure" is false (slides 19 and 23)

- Slide 19: *"Specificity is 0.783 — not 1.000 — because of a single known failure."*
- Slide 23: *"This one scenario is the entire reason specificity is 0.783 rather than 1.000."*

Recounted from raw runs: the five benign scenarios score `baseline 12/12, B2 12/12, B3_pdv_congestion 11/12, B7 12/12, B_bc_replacement 0/12`. Macro specificity = 0.7833. **Excluding B_bc_replacement it is 0.9792, not 1.000.** B3 congestion contributes a second miss.

There is a further distinction the deck never makes: the B3 miss is an **UNKNOWN verdict on a benign scenario** (`unknown_on_benign = 1`), not a false ATTACK. B_bc_replacement produces **12 false ATTACK calls** (`fp = 12`). Those are materially different failure modes — one is an over-cautious abstention, the other a false alarm that would isolate a healthy node.

**Replacement (slide 19):** "Specificity is 0.783 because of two benign failures: 12 false ATTACK calls on B_bc_replacement, and one UNKNOWN on B3 congestion. Excluding B_bc_replacement, specificity is 0.979."
**Replacement (slide 23):** "This scenario is the dominant cause; excluding it, specificity is 0.979, not 1.000."

### 1.2 "~62%" is not an interpolation (slides 20, 25, 26)

Slide 20: *"reports the approximately 62% boundary as an interpolation."*

The four measured points are near-linear in ratio vs blackhole fraction. Solving for the 0.500 threshold between the 60% point (0.5049) and the 65% points (0.4581, 0.4619) gives **60.5%**. 62.5% is the arithmetic midpoint of the untested 60–65% bracket, which is not an interpolation. Calling it one is a method claim the numbers do not support.

**Replacement:** "The untested bracket is 60–65%; linear interpolation of the observed/declared ratio puts the threshold crossing at ≈60.5%."

### 1.3 SyncE evidence was never captured (slide 3)

Slide 3: *"PROJECT HIT: OPEN FRONTHAUL S-PLANE | PTP / SyncE timing evidence captured on brUP and brDN"*

Verified: **no SyncE/ESMC field exists anywhere** — not in the 56-column deep-extract schema, not in any capture, not in the testbed code or configs. The deck contradicts itself: slide 11 lists no SyncE PHY, slide 15 marks B4 SyncE/EEC as hardware-required, slide 22 states SyncE features are absent, slide 25 lists a SyncE PHY as equipment still needed.

**Replacement:** "PROJECT SCOPE: OPEN FRONTHAUL S-PLANE | PTP timing evidence captured on brUP and brDN". ("PROJECT HIT" is also garbled — read "SCOPE" or "FOCUS".)

### 1.4 Slide 7's notes contradict slide 7's table

Notes: *"Every milestone except the paper/IP draft is now closed."*
The table on the same slide shows **M3 PARTIAL** ("digital twin not in this campaign") and **M5 PARTIAL** ("closed-loop healing not validated"). Slides 3 and 25 agree with the table, not the notes.

**Replacement:** "Every milestone is closed except M3 (digital twin), M5 (closed-loop healing) and the M6 paper/IP draft."

### 1.5 Three slide headers claim COMPLETED for milestones the table marks PARTIAL

- Slide 13: *"WORKLET M5: DECISION ENGINE (COMPLETED)"*
- Slide 14: *"WORKLET M5: SAFE ABSTENTION LOGIC (COMPLETED)"*
- Slide 16: *"WORKLET M3: FAULT INJECTION (COMPLETED)"* — while slide 9 reads *"WORKLET M3: FAULT-INJECTION TESTBED (PARTIAL)"*

Same milestone, two statuses in one deck. Use "(PARTIAL — classification evaluated, closed-loop healing not validated)" and "(PARTIAL — injection complete, digital twin not run)".

### 1.6 Wrong IEEE 1588-2019 clause (slide 16)

The deck cites *"IEEE 1588-2019 7.2.4"* for whole-second field abuse (leap61, currentUtcOffset, traceability flags). Clause 7.2 is **"Timescales used in PTP"**. The `timePropertiesDS` members `leap61`, `leap59`, `currentUtcOffset`, `currentUtcOffsetValid` are defined in **8.2.4**, and leap-second handling is **9.4**. Confirmed against IEC 61588 Ed. 3.0:2021 (the identical IEC adoption) and SMPTE ST 2059-2, which cites "subclauses 8.2.4.6 and 9.4 of IEEE Std 1588".

Note: **this error is ours, not the deck-builder's** — it originates in the comment in `run/run_gap.sh` and propagated. Fix it in both places. The normative text is paywalled, so confirm before publication.

### 1.7 Two broken cross-references

- Slide 7: *"…comparison completed on the 168-run campaign (slide 20)."* The AI-vs-rule comparison is **slide 21**. Slide 20 is the interception boundary.
- Slide 18: *"…the one known open failure, B_bc_replacement, explained on slide 22."* It is explained on **slide 23**. Slide 22 is ARM B telemetry constraints.

Also on slide 7: the comparison *trained* on 112 runs (reps 1–8) and *evaluated* on 56 held-out runs (reps 9–12) drawn from the 168 — say "evaluated on 56 held-out runs from the 168-run campaign".

### 1.8 Arithmetic slip in the audit slide (slide 24)

*"36 'replicates' were one capture copied 12 times"* — 36 runs cannot be one capture copied 12 times. It was **three captures (C1, C2, C3) each copied 12 times**.

Same slide, two garbled sentences worth rewriting: *"A script created non-executable returned exit 126"* → "A script was created without the execute bit; the resulting exit 126 was silenced by output redirection." And *"additive-only was 'proven' by comparing two scalars"* → "an additive-only effect was asserted from a two-scalar comparison with no per-run test."

---

## TIER 2 — Silent gaps against the worklet card

The original worklet objectives are: (1) detect anomalies in O-RAN KPIs using AI-based monitoring; (2) **predict faults before they cause major service disruption**; (3) use a digital twin to validate healing actions safely; (4) **automate corrective actions** — parameter tuning, rerouting, recovery workflows; (5) compare the AI-native approach with traditional fault management. Expected outcomes include **faster fault recovery and reduced downtime**, and **measured improvements in availability, recovery time and operational efficiency**.

| Objective | Deck's implied status | Defensible? |
|---|---|---|
| 1 — AI-based anomaly detection | M4 DONE | **Partly.** Detection is delivered by the rule engine. The AI arm scored 0.429 vs 0.357 for a constant-BENIGN predictor, McNemar p = 0.219 — not distinguishable. "Evaluated" is right; "DONE" overstates. |
| 2 — Predict faults before disruption | not mentioned | **No.** The word "predict" appears exactly once in 26 slides, in the phrase "constant predictor". No prediction experiment exists, and the deck does not list it as remaining work. **This is the largest silent gap.** |
| 3 — Digital twin validates healing | M3 PARTIAL | **Yes, where the table is read** — but slide 7's notes and slide 16's header imply closure. |
| 4 — Automate corrective actions | M5 PARTIAL | **No.** Slides 3, 5 and 14 present ISOLATE / TOLERATE-HOLDOVER / ESCALATE as if they are actions. They are verdict labels. No corrective action was executed or measured on this testbed. |
| 5 — Compare AI-native vs traditional | COMPLETED | **Yes.** 56 held-out runs, three arms, a constant-predictor control, a significance test, four combination analyses, and correctly scope-limited on slide 21. This objective is genuinely and rigorously closed. |
| Expected outcomes — recovery time, downtime, availability | not mentioned | **Not measured, and not disclosed as unmeasured.** The strings "MTTR", "recovery time", "availability" and "downtime" appear nowhere in the deck. |

Consequences for specific slides:

- **Slide 26: *"WORKLET STATUS: VALIDATED S-PLANE SUB-SCOPE"*** overstates. Three of five objectives were not executed. Suggested: "S-PLANE DETECTION AND CLASSIFICATION EVALUATED; HEALING, DIGITAL TWIN AND PREDICTION NOT YET RUN".
- **Slides 19 and 26 headline 0.990 without qualifying it.** That is the post-observation v3 rule. The pre-frozen base rule scored **0.625** on the same captures, and that figure appears on neither slide. Slide 17's own notes say *"Do not describe v3 as independent pre-registered validation"* — slides 19 and 26 come close to doing exactly that. Add: "(v3 defect-fix rule; pre-frozen base rule 0.625 on the same captures)".
- **Slide 25's remaining-work list omits** closed-loop healing execution, digital-twin orchestration, fault prediction, and MTTR/availability measurement — the four things slide 7 marks PARTIAL for.
- **C1's 11/12 is partly luck of the draw.** `randparams.py` offers five blackhole levels {55, 60, 65, 70, 75}%; reps 1–12 drew 75% six times, 70% three times, 65% twice, 60% once, and **55% never**. Window arithmetic predicts a ratio of ≈0.55 at 55% — comfortably above the 0.500 threshold, so a 55% draw would also have been missed. The detector's miss rate against the designed parameter space is therefore higher than 1/12 implies. Worth stating rather than waiting to be asked.

---

## TIER 3 — Precision and labelling

**Metrics without a unit of analysis**

1. **Slide 21, ROC-AUC 0.604** is a **per-window** figure (n = 1923 windows, known scenarios, window accuracy 0.544). It sits in a sentence otherwise about 56 held-out runs, and slide 8 promises "never by window". Label it.
2. **Slide 19, attribution 0.875** — the denominator is **84 of 96 attack-expected runs**, v3 rule (Wilson [0.794, 0.927], reproduced exactly). Neither the unit nor the rule is stated.
3. **Slide 18, the "95% CI" column** is the **v3** Wilson interval. Retitle "95% CI (v3, Wilson)".
4. **Slide 19, "Results Across 168 Live Runs"** — the three headline figures are macro averages over scenarios. They coincide with pooled values only because every scenario has n = 12.

**Slide 20, the boundary slide**

5. Axis label *"Fraction of the observation window blackholed"* is wrong. The blackhole covers `c1_down_pct` of the **post-8s-warm-up injection window**; the observation window also contains the warm-up and the restore tail. At 75% the link is dark for 27 s of a 44 s capture, giving an up-time fraction of 0.386 and an observed ratio of 0.366 — which is why the ratios are far above the naive `1 − f`. Relabel "configured blackhole fraction of the C1 injection window".
6. The 65% row quotes **0.458** where two runs exist (**0.4581 and 0.4619**). Same at 75% (0.366–0.367, n = 6) and 70% (0.4125–0.4138, n = 3).
7. Replicate counts per level are **6 / 3 / 2 / 1**. The decisive MISSED level rests on **n = 1**. Show the counts.
8. *"a 1 % margin above the threshold"* — the gap is **0.0049 absolute**, ≈0.98% relative. Say which.

**Slides 21–22, the ML arm**

9. Slide 22: *"Only 6 of 28 features were observable"* — ARM B **used** 6 of 28 **configured** features, and one of those (`holdover_rate`) had importance **0.000**, so only five carried signal.
10. Slide 22's explanation — *"Its input is suppressed by the attacks it must detect"* — does not account for the result. ARM B's attack sensitivity is **0.156 across all eight attack scenarios**, including A1/A2/A3/A5/A8 where servo telemetry is intact at ~88 lines per run. Telemetry starvation on C1 and C3 compounds the problem; feature poverty and class overlap are the primary causes.
11. Slide 8: *"IsolationForest open-set layer providing abstention"* vs slide 21: ARM B correct abstention **0.000**. The layer ran; it delivered no usable abstention. Say "intended to provide abstention (scored 0.000)".
12. Slide 17: *"3 rules scored on the same runs"* — true (base, v2 and v3 all scored on all 168), but **v2 appears nowhere else in the deck**, so the reader never sees the false positive that justified v3. Either add a v2 column to slide 18 or say "v2 reported in the workbook".

**Standards attributions — right in substance, imprecise in wording**

13. **Slide 10, transport row.** `01-1B-19-00-00-00` is the forwardable address and G.8275.1 permits it, but it is **ptp4l's global default**, not the profile's reference value — linuxptp's own `configs/G.8275.1.cfg` sets `01:80:C2:00:00:0E`. Our own config file already documents this correctly; the slide's "basis: G.8275.1 forwardable address" reads as if the profile specified it. Relabel "permitted by G.8275.1 (forwardable); ptp4l default".
14. **Slide 4, 130 ns.** The value, the Category-A label and the "relative between radio units" framing are all correct and O-RAN.WG4.CUS.0 does tabulate them. Worth adding the per-RU implication a reviewer will ask for: 130 ns is the **pairwise** limit between RU clusters, i.e. ≈**±65 ns per RU** against the common reference, and the fronthaul network is allocated only part of that. Both 130 ns and 1.5 µs ultimately derive from 3GPP requirements (TS 38.104/38.133) re-expressed downstream.
15. **Slide 4, 1.5 µs.** Correct value and correct scope (application-level, O-RU to PRTC). A reviewer may ask why the **1100 ns network limit at reference point C** is not cited instead, since the network is the object of study.
16. **Slide 23, GNSS.** *"A coherent GNSS spoof is undetectable ... physical limit ... No software feature engineering removes this"* is **overstated**. Single-receiver detection methods exist — signal-quality monitoring, correlation-peak distortion, C/N0 and AGC monitoring, Doppler/ephemeris consistency, receiver clock-state self-consistency — and those *are* software feature engineering. Scope it: "a coherent spoof is not separable **from S-plane PTP telemetry downstream of the GNSS receiver**; detection needs receiver-level RF observables, multi-antenna geometry, or an independent time anchor — none of which this testbed has."
17. **Slide 16, A2 mechanism.** *"forged Sync with manipulated originTimestamp"* — in two-step mode (ptp4l's default, and normal for G.8275.1) the authoritative field is `preciseOriginTimestamp` in Follow_Up, not Sync's `originTimestamp`. State the step mode.
18. **Slide 16, BMCA.** A rogue wins on *"a superior priority2"* only after clockClass, clockAccuracy, offsetScaledLogVariance and localPriority tie — under the G.8275.1 alternate BMCA, priority2 is not the deciding field.
19. **Slide 16, malformed frames.** `controlField` is **deprecated in IEEE 1588-2019** (transmitted as 0, retained for backward compatibility), so "illegal controlField" is a strong legality signal only against 2008-era implementations. Worth a footnote given the deck cites 1588-2019 as the legality basis.
20. **Slide 15, ETSI mapping.** The hedge "where applicable" carries real weight: **T-SPLANE-04 (selective interception and removal) maps to C1, a C-series scenario, not an A-class**, and T-SPLANE-01…04 has **no counterpart for A3 (replay), A4 (delay), A6/A7 (GNSS)**. State the mapping explicitly.
21. **Slide 15, coverage.** Titled "Fault Taxonomy and **Test Coverage**" but shows no coverage: **8 of 16 classes (A4, A6, A7, B1, B4, B5, B6, B8) were never run**, and C1/C2/C3, baseline, B_bc_replacement and B_unplanned_failover have no taxonomy ID. Add a "tested this campaign" column.
22. **Slide 3, architecture.** Correct as far as it goes. Omissions a reviewer may note: **O1 and O2 interfaces absent**; the Open Fronthaul interface not named; and **E2 terminates at O-CU-CP/O-CU-UP/O-DU/O-eNB, not at the O-RU** — which matters because the project boundary sits exactly where E2 does not reach.
23. **Slide 11, timestamping.** *"microsecond noise floor"* is conservative in our own favour. Software timestamping is typically **10–100 µs**; hardware timestamping ≈30 ns. The gap is 2.5–3.5 orders of magnitude, not one.
24. **Slide 7, housekeeping.** The **HARDWARE-BLOCKED** legend entry is used by no row. Two rows are both labelled **M6** with opposite statuses (DONE / NOT STARTED) — label them M6a (testing) and M6b (paper/IP). Slides 5, 6 and 12 assert M1 sub-items that do not appear in the delivery map.
25. **Slide 10 wording.** *"read back every configuration value ... and traced it to the governing standard"* conflicts with the caveat on the same slide about paywalled recommendations. Add "or, where the normative text is paywalled, to an authoritative secondary source."

---

## What verified clean

Every figure below was recounted from the raw per-run files or checked against primary sources. All reproduce exactly.

**Campaign results (recounted from 168 `cap/*__r*` directories, rep whitelist 1–12)**

| Scenario | Expected | Base | v3 | Wilson 95% CI (v3) |
|---|---|---|---|---|
| A1, A2, A3, A5, A8 | ATTACK | 12/12 each | 12/12 each | 0.757–1.000 |
| C1_removal | ATTACK | 0/12 | 11/12 | 0.646–0.985 |
| C2_malformed | ATTACK | 0/12 | 12/12 | 0.757–1.000 |
| C3_wholesecond | ATTACK | 0/12 | 12/12 | 0.757–1.000 |
| baseline, B2, B7 | BENIGN | 12/12 each | 12/12 each | 0.757–1.000 |
| B3_pdv_congestion | BENIGN | 11/12 | 11/12 | 0.646–0.985 |
| B_bc_replacement | BENIGN | 0/12 | 0/12 | 0.000–0.242 |
| B_unplanned_failover | UNKNOWN | 12/12 | 12/12 | 0.757–1.000 |

- Macro attack sensitivity base **0.625** → v3 **0.9896** (rounds to 0.990); macro specificity **0.7833** both; abstention **1.000**; attribution v3 **0.875** = 84/96 attack runs.
- v2 and v3 verdicts are **identical on all 168 runs** (0 disagreements) — additive-only with 0 regressions, verified per-run, not by scalar comparison.
- C1 blackhole levels and ratios: 75% → 0.366–0.367 (n=6, caught); 70% → 0.4125–0.4138 (n=3, caught); 65% → 0.4581, 0.4619 (n=2, caught); 60% → **0.5049** (n=1, missed, threshold 0.500). Recomputed independently from the r12 deep-extract CSV.

**AI-vs-rule comparison (56 held-out runs, train reps 1–8, test 9–12)**

- ARM A 51/56 = 0.911; ARM B 24/56 = 0.429; always-BENIGN 20/56 = 0.357.
- Attack sensitivity 0.969 (31/32) / 0.156 (5/32) / 0.000. Benign specificity 0.800 (16/20) / 0.950 (19/20) / 1.000. Abstention 1.000 / 0.000 / 0.000. Arithmetic closes in every arm.
- ARM B outputs BENIGN on 47/56; McNemar exact two-sided **p = 0.21875** → 0.219; not distinguishable at α = 0.05; both ARM B and the constant predictor score 4/4 on B_bc_replacement.
- Combinations: OR 0.8929, rule-first-then-ML 0.8393, consensus 0.4286 — all below ARM A. No combination beats the rule arm.
- Feature importances 0.268 / 0.262 / 0.208 / 0.139 / 0.124 / 0.000; 6 of 28 configured features populated.
- Servo lines per run: baseline **88.0**, C1 **44.5**, C3 **28.0** — recounted directly from the shipped log tarball (sha256 `bc20005f…`, verified).

**Testbed and platform (verified live)**

- Six linuxptp **4.0** daemons (gma, gmb, bc, ru1, ru2, ru3); two bridges brUP/brDN; **56**-column deep-extract CSV.
- `/dev/ptp*` absent; `modprobe` absent and `/lib/modules/$(uname -r)` absent; `tc ... netem` → "Specified qdisc kind is unknown"; `tbf` works. Every platform-constraint claim on slide 11 holds.
- Config read back from the running configs: G.8275.1 profile, `domainNumber 24`, `priority1 128`, `logSyncInterval -4` (16/s), `logAnnounceInterval -3` (8/s), `dataset_comparison G.8275.x`, `network_transport L2`, `ptp_dst_mac 01:1B:19:00:00:00`, `time_stamping software`. All nine daemons agree.
- 48 of 168 runs lack `pmc.jsonl` (all 12 each of B3, C1, C2, C3); 36 C-series `context.json` files record `rep=901`. Both disclosed on slide 23 and both exactly right.

**Taxonomy and matrix**

- `ORAN_SPlane_Parameter_Fault_Matrix.xlsx` MATRIX sheet has exactly **144 parameter rows × 16 faults** — slide 7's "144-parameter × 16-fault matrix" is exact.
- Tally: SOFTWARE (fully) **8** = A1 A2 A3 A5 B2 B3 B7 B8; SOFTWARE (detection only) **3** = A4 A8 B5; HARDWARE required **5** = A6 A7 B1 B4 B6. Slides 15, 25 and 26 all match.
- One cross-document inconsistency to fix in the workbook, not the deck: the FAULT KEY sheet still justifies A4, B3 and B5 by "netem can inject asymmetric delay" / "netem delay/jitter is purpose-built for exactly this". **netem is absent from this kernel.** The deck is correct (slide 11 says no netem, slide 16 says B3 uses a tbf bottleneck); the workbook is stale.

**Standards (verified against primary or authoritative secondary sources)**

- G.8275.1: domain 24 range 24–43; priority1 128 fixed and excluded from the alternate BMCA; Sync 16/s; Announce 8/s; `dataset_comparison G.8275.x` not IEEE default — all correct.
- clockClass 6 → 7 on GNSS loss while within holdover specification — correct.
- ETSI TR 104 106 V3.0.0 (2025-06) is the PAS of O-RAN.WG11.Threat-Modeling, and T-SPLANE-01 (DoS on master), -02 (fake ANNOUNCE impersonation), -03 (rogue instance seeking Grand Master), -04 (selective interception and removal) are verbatim correct.
- linuxptp 4.0 released 2023-06-09; ships `configs/G.8275.1.cfg`; supports `dataset_comparison`.
- TIMESAFE: Groen, Di Valerio, Karim, Villa, Zhang, Bonati, Polese, D'Oro, Melodia, Bertino, Cuomo, Chowdhury. Began as arXiv:2412.13049 but is now **peer-reviewed in ACM Transactions on Privacy and Security, DOI 10.1145/3775060** — update the citation. The abstract states a spoofing attack causes a production-ready O-RAN 5G base station "to catastrophically fail within 2 seconds"; the body attributes it to an **RU software crash requiring a manual reboot**, under a switch configuration with PTP ports in "dynamic" role. The deck's caveat — "an observed result from one published study, not a standardised limit" — is accurate. Two conditions worth adding: it is a crash, not a sync-accuracy violation, and the paper's other configuration degrades over ~580 s.

---

## Sources

- TIMESAFE: https://arxiv.org/abs/2412.13049 · https://dl.acm.org/doi/10.1145/3775060
- ETSI TR 104 106 V3.0.0: https://www.etsi.org/deliver/etsi_tr/104100_104199/104106/03.00.00_60/tr_104106v030000p.pdf
- G.8275.1 profile (Cisco): https://www.cisco.com/c/en/us/td/docs/routers/ir8340/software/configuration/b-ir8340-timing-ios-xe-17/m-8275-1-telecom-profile.pdf
- G.8275.1 tutorial (ITU/WSTS): https://wsts.atis.org/wp-content/uploads/2018/11/4-4-Iometrix_Jobert_ITU_G.8275.1.pdf
- G.8271.1 summary (Calnex): https://calnexsolutions.atlassian.net/wiki/spaces/GDW/pages/9470164/
- O-RAN fundamentals / 130 ns and ±65 ns (WSTS): https://wsts.atis.org/wp-content/uploads/2022/05/12-Greg-Armstrong.ORAN-Fundamentals.pdf
- Fronthaul sync categories (WSTS): https://wsts.atis.org/wp-content/uploads/2021/03/Sync-in-Fronthaul-WSTS21-Frost.pdf
- linuxptp: https://linuxptp.nwtime.org/documentation/ptp4l/ · https://raw.githubusercontent.com/richardcochran/linuxptp/master/configs/G.8275.1.cfg
- IEC 61588 Ed. 3.0:2021 (IEEE 1588-2019 adoption, clause structure): https://cdn.standards.iteh.ai/samples/105175/7d475129e6c640f099310130a3fb4c62/IEC-61588-2021.pdf
- SMPTE ST 2059-2 (leap61 clause citation): https://pub.smpte.org/pub/st2059-2/st2059-2-2021.pdf
- GNSS spoofing detection: https://www.mdpi.com/1424-8220/24/13/4210
