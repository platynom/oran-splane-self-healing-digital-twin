# V5 changelog

**Generator:** `.codex_build/prism_v5/build_v5.mjs`  
**Source deck:** `deliverables/ORAN_SPlane_PRISM_Review_v4.pptx`  
**Output:** `deliverables/ORAN_SPlane_PRISM_Review_v5.pptx`  
**Output SHA-256:** `7d3c8949bb8eb6268f13dcf8b68b5f8fc23d1eb03e653e058d46b443bcaecb37`

V4 and `build_v4.mjs` were not modified. Slide 1 was not edited; its rendered PNG is byte-identical to V4.

## Slide-by-slide edits

### Slide 3 — architecture and evidence boundary

- `PROJECT HIT` → `PROJECT FOCUS`.
- Removed “PTP / SyncE timing evidence captured”; now states that PTP timing evidence was observed and SyncE was outside the software testbed.
- Expanded remaining scope to fault prediction, digital-twin orchestration, automated recovery and outcome measurement.
- Added archive-retention note: extracted CSV/context/decision evidence is retained; PCAPs are not.
- Basis: checks 1 and 30(c).

### Slide 4 — timing requirements and TIMESAFE

- 130 ns is now scoped to 5G FR2 intraband-contiguous CA relative TAE, Timing Category A.
- Added the derived ≈±65 ns/RU interpretation only with the equal-allocation qualification.
- `1.5 µs from O-RU to PRTC` → `±1.5 µs at end-application reference point E relative to a common recognized time standard`.
- TIMESAFE updated to ACM TOPS and DOI `10.1145/3775060`; mechanism is stated as an RU software crash requiring manual reboot under dynamic PTP-port roles, with the other configuration degrading over about 580 s.
- Added the 3GPP-origin/re-expression qualification.
- Basis: checks 33–35.

### Slide 7 — milestone status

- Removed unused `HARDWARE-BLOCKED` legend entry.
- Split duplicate M6 labels into M6a (testing/evaluation) and M6b (paper/IP).
- Cross-reference corrected from slide 20 to slide 21.
- Evaluation wording now says 56 held-out runs from the 168-run campaign.
- Speaker note now preserves M3 and M5 as PARTIAL and discloses unmeasured prediction/outcomes.
- Basis: check 30(a), 30(d), 30(f), 30(g).

### Slide 8 — ML evaluation design

- `IsolationForest ... providing abstention` → `intended to provide abstention (held-out score 0.000)`.
- Basis: checks 19 and 23.

### Slide 9 — retained capture evidence

- Replaced “every PTP frame ... is recorded” with the reproducible distinction: tcpdump was configured, but the corrected archive retains extracts/decisions rather than source PCAPs.
- Basis: checks 1 and 28.

### Slide 10 — configuration provenance

- Replaced the universal runtime-readback claim with a repository-script/standards-consistency statement and explicit missing-runtime-config limitation.
- Destination MAC basis now says it is a permitted forwardable address and the ptp4l global default.
- Replaced the blanket paywall/vendor note with a distinction between official ITU pages and corroborating implementation documentation.
- Basis: checks 28 and 32.

### Slide 11 — platform constraint

- Replaced a generic software-timestamping range with the direct testbed measurement: baseline mean `|offset| = 1,866 ns`.
- Speaker notes include direct sample counts and means for baseline, C1 and C3.
- Basis: checks 25 and 41.

### Slides 13–14 — M5 status and response semantics

- Both M5 headers changed from COMPLETED to PARTIAL, specifying classification/verdict-logic evaluation.
- clockClass 6→7 is limited to a T-GM entering holdover while still within its configured specification.
- ISOLATE and HOLDOVER are labelled recommended outputs, not executed actions.
- Basis: checks 30(b), 37, and the worklet-gap audit.

### Slide 15 — taxonomy, test coverage and ETSI mapping

- Added `TESTED` to A1, A2, A3, A5, A8, B2, B3 and B7; the other eight A/B rows remain unmarked.
- Explicit mapping added: A5→T-SPLANE-01, A1→-02/-03, C1→-04, A4 delay→-05; replay and GNSS classes are disclosed as lacking a clean one-to-one mapping.
- Basis: checks 29 and 36.

### Slide 16 — injection and standards legality

- M3 header changed from COMPLETED to PARTIAL because the digital twin was not run.
- `superior priority2` → `superior dataset under the G.8275.1 alternate BMCA`.
- A2/C2/C3 wording now distinguishes two-step timestamping and independent malformed-frame fields; `controlField` is not used as sole legality evidence.
- Added IEEE 1588-2019 `timePropertiesDS §8.2.4` and leap-second handling `§9.4`; notes identify Follow_Up `preciseOriginTimestamp` as authoritative in two-step mode.
- Basis: checks 30(b), 31, 39 and 40.

### Slide 17 — campaign reproducibility

- Clarified that v2 and v3 were scored on the same captures and yield identical verdicts on all 168 runs.
- Basis: check 8.

### Slide 18 — scenario table

- CI header now reads `95% CI (v3, Wilson)`.
- B_bc_replacement cross-reference corrected to slide 23.
- Footer now distinguishes the dominant false-positive scenario from the B3 UNKNOWN.
- Basis: checks 7, 9, 10 and 30(d).

### Slide 19 — primary results

- `0.990` labelled as the post-observation v3 rule; pre-frozen base `0.625` shown alongside.
- Attribution labelled `84/96 attack runs` and v3.
- Coverage-gain wording states this is post-observation evaluation on the same captures.
- Single-cause specificity statement replaced: B_bc_replacement produces 12 false ATTACK calls; B3 contributes one UNKNOWN; excluding BC replacement gives `47/48 = 0.979`.
- Basis: checks 3, 6, 8–10 and 30(h).

### Slide 20 — C1 boundary

- `~62%` → linear crossing `60.54%`, with tested bracket `60–65%`.
- Axis now identifies the post-warm-up C1 injection window.
- Replicate counts added for all levels; the two 65% ratios are shown separately.
- 60% margin stated as `0.004889` absolute and `0.98%` relative.
- Added that 55% was configured but never drawn and is predicted to produce ratio ≈0.568, also missed.
- Basis: checks 11–18.

### Slides 21–22 — ARM B interpretation

- ROC-AUC labelled window-level, `n=1,923` known-scenario windows.
- `6 of 28 observable` → six of 28 configured features populated and used; `holdover_rate` had zero importance and five features carried signal.
- Telemetry starvation changed from the sole explanation to a contributing factor; feature poverty and class overlap are primary constraints.
- Always-BENIGN comparison and non-distinguishability conclusion retained.
- Basis: checks 19–26.

### Slide 23 — limitations

- Specificity explanation now gives both failure modes and `47/48 = 0.979` excluding BC replacement.
- Absolute GNSS-undetectability claim replaced with a ptp4l-only testbed limitation and examples of additional trusted evidence required.
- Basis: checks 9, 10 and 38.

### Slide 24 — pipeline audit

- `one capture copied 12 times` → `three captures copied 12 times`.
- Rewrote the exit-126 and two-scalar sentences in plain English.
- Added the per-run v2/v3 comparison result.
- Basis: checks 8 and 30(e).

### Slide 25 — remaining work

- `~62%` → `60.54%` crossing.
- Added four explicit gaps: fault prediction, executed corrective action, digital-twin exercise, and MTTR/recovery-time/availability/downtime measurement.
- Basis: checks 16, 30(f), and worklet objectives 2–4/outcomes.

### New slide 26 — objectives not yet addressed

- Added the required disclosure slide before the closing slide.
- States without qualification that prediction was not attempted; no corrective action was executed or measured; the digital twin was not exercised; and no MTTR, recovery-time, availability or downtime figure was measured.

### Slide 27 — closing summary (formerly slide 26)

- `0.990` explicitly tied to post-observation v3 and paired with base `0.625`.
- `~62%` replaced with `60.54%`; archive PCAP-retention limitation added.
- Status line now says detection/classification were evaluated while prediction, digital twin and healing remain unrun.
- Basis: checks 1, 3, 16 and 30(h).

## Non-deck corrections

- Added repository copy `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/run/run_gap.sh` from the supplied campaign source with IEEE 1588-2019 citation corrected from 7.2.4 to `timePropertiesDS §8.2.4; leap-second handling §9.4`. The path did not previously exist outside the archive.
- Created `ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx` without overwriting the original. FAULT KEY cells E8, F8, E15 and E17 now disclose missing `sch_netem`, identify the actual B3 `tbf` mechanism, narrow physical-impact claims, and map A4 delay to T-SPLANE-05.
