# V5 self-check

**Deck:** `deliverables/ORAN_SPlane_PRISM_Review_v5.pptx`  
**Deck SHA-256:** `7d3c8949bb8eb6268f13dcf8b68b5f8fc23d1eb03e653e058d46b443bcaecb37`  
**Validation receipt:** `.codex-finalizer/ORAN_SPlane_PRISM_Review_v5.validation.json`

## V1 — text/notes extraction, slide count and slide 1

- Re-extracted all slide text and speaker notes from the saved V5 package to `.codex_build/prism_v5/deck_v5_text_and_notes.md`.
- Slide count: **27**; first-party re-import also reports 27.
- V4 slide-1 render SHA-256: `8c868645c56881b6ea1e948ec7de8755ce4b68c6d66a9a4cec5910a302147602`.
- V5 slide-1 render SHA-256: `8c868645c56881b6ea1e948ec7de8755ce4b68c6d66a9a4cec5910a302147602`.
- Result: **PASS — byte-identical rendered content.** Slide 1 was not targeted by the generator.

## V2 — required removals and additions

Automated assertions passed for every targeted string. Full machine output is `.codex_build/prism_v5/selfcheck_assertions.json`.

| Assertion group | Result |
|---|:---:|
| Removed `PROJECT HIT` and captured-SyncE claim | PASS |
| Removed `~62%` / “approximately 62%” | PASS |
| Removed single-cause specificity claims | PASS |
| Removed contradictory milestone-completion note and headers | PASS |
| Removed one-capture/12-copies arithmetic | PASS |
| Removed overstated closing status | PASS |
| Added 60.54% crossing and 60–65% bracket | PASS |
| Added 47/48 = 0.979, 12 false ATTACK calls and one UNKNOWN | PASS |
| Added window-level ROC-AUC, n=1,923 | PASS |
| Added four explicit unaddressed objectives/outcomes | PASS |
| Added T-SPLANE-05 and IEEE §8.2.4 / §9.4 | PASS |

## V3 — V4/V5 text and notes diff

- Produced `.codex_build/prism_v5/v4_v5_text_notes.diff.md`.
- Reviewed every changed slide: 3, 4, 7–11, 13–25, old 26→new 27, plus the new slide 26.
- Slides 1, 2, 5, 6 and 12 have no text/notes difference.
- All differences map to a FAIL/UNVERIFIABLE result, a required standards correction, the requested new slide, or a speaker-note citation/evidence clarification.
- Result: **PASS — no unintended text or notes changes found.**

## V4 — previously passing numbers preserved

Automated V4/V5 presence checks passed for the following verified values: `168`, `14`, `12`, `51/56`, `24/56`, `20/56`, `0.911`, `0.429`, `0.357`, `0.969`, `0.156`, `0.800`, `0.950`, `0.893`, `0.839`, `0.268`, `0.262`, `0.208`, `48/168`, `36 C runs`, `0.783`, `1.000` and `0.875`.

The per-scenario slide-18 table remains numerically unchanged. Newly displayed precision (`60.54%`, `0.504889`, `0.413656`, etc.) comes from the same recomputation recorded in `V5_VERIFICATION_LOG.md`.

Result: **PASS.**

## V5 — contradiction scan

- M3 is PARTIAL on slides 9 and 16; M5 is PARTIAL on slides 13 and 14.
- Slide 7 now uses M6a/M6b, has no unused HARDWARE-BLOCKED legend item, and points to slide 21.
- Slide 18 points to slide 23 for B_bc_replacement.
- No claim remains that SyncE evidence was captured.
- “Interpolation” is used only for the computed 60.54% C1 crossing within the untested 60–65% bracket.
- Slides 19 and 27 identify 0.990 as the post-observation v3 rule and display the base value 0.625.
- Slide 21 explicitly says ARM B is not distinguishable from always-BENIGN and that BC-replacement performance is not unique.
- Slide 26 and slide 25 disclose prediction, action, digital-twin and outcome-metric gaps.

Result: **PASS.**

## V6 — package, layout and rendered-slide inspection

- Finalizer package integrity: PASS; 27 slides; zero findings.
- Layout validator: PASS; 13.3333 × 7.5 in; zero findings/warnings.
- Font policy: PASS; only Calibri, Cambria and Courier New.
- First-party Artifact Tool re-import: PASS.
- `slides_test.py`: **Test passed. No overflow detected.**
- Rendered all 27 slides to `.codex_build/prism_v5/rendered_v5` and visually inspected the montage plus enlarged slides 15, 20, 25 and 26.
- Checked all lengthened slides for clipping, overlap, table-row visibility, contrast and readability. No defects found.

Result: **PASS.**

## V7 — number provenance

All numbers added or changed in V5 trace to a specific source inspected during Job 1:

- campaign run counts, per-scenario results, sensitivity/specificity/attribution and C1 values → corrected campaign archive and its per-run JSON/deep CSV files;
- ARM A/B/control, p-value, window-level AUC, feature counts/importances and combinations → `ML_VS_RULE_COMPARISON.json` plus manual discordant-pair arithmetic;
- servo counts/offset means → `ml_comparison_input/extracted_168run_ptp4l_logs`;
- 130 ns / ±1.5 µs / profile rates / ETSI mappings → cited standards sources in the notes and verification log;
- TIMESAFE 2 s / ~580 s and mechanism → ACM TOPS article DOI `10.1145/3775060`;
- archive hash/entry count → direct SHA-256 and tar listing.

No V5 number lacks a source. The derived ≈±65 ns/RU statement is explicitly conditional on equal allocation and is not presented as a normative value.

Result: **PASS.**

## Corrected workbook check

- Output: `ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx`.
- Original workbook SHA-256 remains `15b3168b2253abe46f8be008c6c079d40e88fc83fc99a2295821fd2e3a6cb219`.
- Corrected workbook SHA-256: `73124e4e02776a3e8e24e6ed67aed3b73235d860f0bf3b5cdeaf881c55e13d4a`.
- FAULT KEY E8/F8/E15/E17 inspected after edit; stale netem phrases and the A4→T-SPLANE-04 mapping return zero matches.
- Formula-error scan returned zero matches.
- Rendered `FAULT KEY!A1:F20` and visually inspected it; text remains wrapped, legible and within the existing table.

Result: **PASS.**

## Remaining evidence limitations, not self-check failures

- The corrected archive has no retained source PCAPs and no complete runtime config set.
- The 60.54% C1 crossing is interpolated; the 60% point has n=1 and 55% was never drawn.
- V3 is a post-observation defect-fix rule evaluated on the same captures, not an independent pre-registered validation.
- No digital-twin, executed healing, fault-prediction or recovery-outcome experiment exists in this campaign.
