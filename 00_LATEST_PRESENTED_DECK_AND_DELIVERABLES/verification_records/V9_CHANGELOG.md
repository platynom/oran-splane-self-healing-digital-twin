# v9 deck changelog

Baseline: the frozen 42-slide `ORAN_SPlane_PRISM_Review_v8.pptx` in commit `600b5ec`, SHA-256 `AFD35BA8ECCCA1A2AAD07591CBF26AA0BD560C9984F5924186310A58C27F53BA`.

The main-folder file named v8 already contained four appended slides and had 46 slides before this task. It was not edited. The committed 42-slide copy was used so the requested v8-to-v9 comparison remained auditable.

## Slide-number mapping

- v8 slides 1–33 retain their numbers.
- Four new slides were inserted as v9 slides 34–37.
- v8 slides 34–42 become v9 slides 38–46.

## Changed and new slides

| v9 | v8 origin | Change |
|---:|---:|---|
| 3 | 3 | Rebuilt reviewer question map for 46 slides. Added the recovery question and Q16 reactive/preventive/predictive. Pointed impact to slide 37, recovery to 34–35, Q16 to 36, applicability to 44 and references to 46. |
| 6 | 6 | Replaced the incorrect `T-FRHAUL-01` LLS-C1 attribution with the exact wording in `ERRATA_V8_2026-11.md` §1. |
| 9 | 9 | Reattributed the first three access factors to TIMESAFE §4 and the Ethernet L1 access path to ETSI `T-FRHAUL-02`, using the exact errata wording. |
| 11 | 11 | Reframed C2 as a project-defined three-variant subset related to ETSI TS 104 105 §24.2.1.2, not a reproduction of its 250,000-iteration O-DU fuzz test. |
| 24 | 24 | Corrected the C2 mapping in speaker notes so the obsolete “maps to” wording is absent from the complete deck package. No visible slide text changed. |
| 26 | 26 | Applied both C2 errata corrections and the C3 `free_running 1` measurement boundary. Corrected the C2 speaker-note attribution. |
| 29 | 29 | Updated one speaker-note sentence that still said closed-loop healing was not validated. No visible slide text changed. |
| 34 | New | Added **Protocol-State Recovery Loop**: detect, localise, decide, act, verify, rollback and escalate; two triggers; bounded actions; safety guard; verification; standards basis. |
| 35 | New | Added **Matched Control and Closed-Loop Results**: 140-run design, A1/C1/C3 control-versus-loop table, containment-only cases, H1/H2/H4 PASS, H3 FAIL with B3 r17 explanation and limits. |
| 36 | New | Added **Reactive, Preventive and Predictive Mechanisms** from `REACTIVE_VS_PROACTIVE.md`, including the stored shortened RFC 7384 §5.9 quotation. |
| 37 | New | Added **Attack Impact: Measured, Referenced and Not Measured**, preserving the evidence boundary for all eight attacks. |
| 42 | 38 | Updated worklet status: M5 done for protocol-state recovery, M6a includes the 140-run evaluation, automated action and recovery outcomes measured, while prediction, digital-twin rehearsal and paper/IP remain open. |
| 43 | 39 | Marked only continuity-based total-service-loss detection as done. Kept the partial-interception sweep, rogue-BC rule fix, richer ML telemetry, classification re-freeze and hardware work open. |
| 45 | 41 | Updated the technical summary with the 140-run recovery result and remaining scope. Retained the ARM B versus constant-predictor conclusion unchanged. |
| 46 | 42 | Added the recovery, Q16, impact and stored-standards sources, including the stored corpus path. Updated the citation-audit date. |

## Global terminology and stale-wording checks

- `notSlave` does not occur in slide text or speaker notes.
- New G.8275.1 wording uses `timeTransmitterOnly` and `notTimeTransmitter`.
- The obsolete phrases identified by the errata and recovery-status brief are absent from slide text and notes.

## Unchanged slides

All v8 slides not listed above are byte-for-byte identical in ordered visible text and speaker-note text after applying the four-slide insertion mapping. The verification script reports zero mismatches.

