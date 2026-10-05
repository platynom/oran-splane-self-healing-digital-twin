# Final verification report — current audited scope

Date: 2026-09-08

## Delivered

`ORAN_All_Current_Datasets_CORRECTED.xlsx` now contains **49 sheets**, including separate detail sheets for all **45 sources** in the manifest. Every original row and column is retained: **523,176 source records and 9,590,610 original cells**. The counts include retained duplicate representations, not independent experiments.

SHA-256: `a970ff9b87c9813d2c592f74ad00b7403e497cd1d8d783db7e91becb20c39038`

The earlier four-sheet orientation file is preserved as `ORAN_Orientation_PRESERVED.xlsx`. The original combined workbook and original source data were not edited during this continuation. All 45 source hashes were rechecked against the prior manifest.

## Checks performed

| Check | Result and evidence |
|---|---|
| Full source preservation | Every exported original cell compared exactly to a fresh CSV reader; all rows, headers, appended metadata and source hashes reconciled. `detailed_reconciliation.json`. |
| Precision and missing values | Original fields stored as exact text, including timestamp strings, long decimals, identifiers and blanks. Convert copies explicitly for numerical analysis; do not silently round the evidence. |
| Workbook structure | ZIP integrity passed. `saved_workbook_bounded_inspection.json` confirms all 49 sheets; every detail sheet has a filter, frozen header, inline raw strings, provenance/status/action fields, and the S001 ISO-8601 timestamp remains literal text. Time, scenario, model, action, and reason columns were widened in the final streamed workbook without changing source strings. No formula/error cells in detail data. Bounded previews are not proof of native Excel performance on 500k rows. |
| Duplicate disposition | Conflicting Announce labels, derived sessions AND raw aliases S041/S042 are quarantined. Exact simulation duplicates remain identified. Netem run relationships are marked unresolved. |
| Gate regressions | Actual modules imported with `C:\Python314\python.exe`; all checks in `test_evidence_gate_regressions.py` passed, including a self-validating evaluated-CSV circularity attempt, partial missing labels, and malformed `run_id`. Results saved in `evidence_gate_regression_results.json`. Mechanical fixtures do not validate scientific claims. |
| Further integration fixes | Removed the real evaluator's remaining call to deleted `_pre_row`; handled no eligible families; rejected missing source maps, malformed metadata, and evidence artifacts matching evaluated inputs. Packet validation now requires hashes for every exact label/PCAP input consumed by `load_capture_sessions` and rejects any of them as circular evidence. Evaluator control flow tested with explicit model stand-ins, not a full training run. |
| Production lineage | Actual `pcap_to_telemetry` output: all 13,562 records matched to exact source packets using verified-unique capture-local keys and capture times. Only packets 1–3 have no emission. Hash-bound sidecar and verification JSON saved. |
| Explanation coverage | `PARAMETER_BY_PARAMETER_GUIDE.md` includes all 113 original field names, six reasoning questions, conditional actions, limitations and primary-source context. Coverage is not independent validation of every field. |
| Code checks | Modified modules compiled and `git diff --check` passed. Ingestion documentation corrected without changing ingestion calculations. |

Reproduction from the workspace root:

1. Bundled Python: `stream_detailed_workbook.py prepare`.
2. Bundled Node: `build_detailed_corrected_workbook.mjs`.
3. Bundled Python: `stream_detailed_workbook.py assemble`, then `verify`.
4. System Python: `test_evidence_gate_regressions.py` and `verify_production_lineage.py`.

All scripts above are under `outputs/manual_dataset_combined`. The streamed pending workbook is verified before replacing the corrected deliverable. Artifact Tool authors the bounded templates; standard-library XML/ZIP streaming preserves full CSV records without materializing millions of cells in the workbook engine.

## What remains unestablished

- Capture-specific launch/authorization records and reliable label-generation versions.
- Receiver hardware timing, reference/oscillator calibration, physical fault versus benign ground truth, and executed recovery outcomes.
- Dynamic use of every historical file and definitive run/overlap relationships for all software-testbed exports.
- Exact historical telemetry/window/decision lineage beyond the audited alignments and the new production-regeneration sidecar.

These require source-specific evidence. Unknown situations remain unknown; proposed physical actions remain unestablished at row level. The workbook is complete for the stated 45-source scope, not every historical file in the repository, and is not a scientifically validated fault/recovery dataset.

---

## 2026-09-08 final PCAP consolidation addendum

`ORAN_All_Current_Datasets_FINAL_PCAP.xlsx` is the current versioned deliverable. SHA-256: `5b4b7423219f4d60c34c0064ef81458f53fe3238fe844b01864567ae52259803`.

It retains all 49 sheets of the corrected workbook byte-for-byte and appends 19 sheets: a start page, an all-field dictionary, capture/alias index, rules and evidence-gap tables, and one complete decoded export for each of 14 canonical classic-PCAP hashes. The 45 source hashes were rechecked. The inherited 49 worksheet XML parts are byte-identical to the prior fully reconciled workbook, preserving the 523,176 original rows and 9,590,610 original lexical cells. ZIP integrity passed; the 68 sheet names are unique; new sheets contain no formulas or error cells.

The largest export has 267,084 records, within Excel's per-sheet row limit. Each export retains every capture record, including non-PTP or unsupported frames with an explicit parse status. Decoder fields are marked derived and include the decoder hash. Alias paths are listed without counting duplicate copies as independent experiments. Supplied annotations are not copied into PCAP rows.

The only new observable pattern rules are R-PCAP-01a/b/c. They distinguish an advertised grandmaster identity change, an advertised clock-attribute change with unchanged identity, and both together. Comparison is restricted to matching PTP transportSpecific, version, domain and sourcePortIdentity. In the production PCAP this yields five rows. These are capture-local advertised-header observations, not proof of receiver selection, unauthorized takeover, GNSS/oscillator state, timing degradation, recovery, or a label-generation mechanism.

The rebuilt export verifies every saved PCAP row: exactly 39 cells, exact headers, no formulas/error cells, and the canonical-capture and decoder hashes at fixed columns 38 and 39. Non-PTP records use `NOT_APPLICABLE`; truncated or invalid PTP uses `UNKNOWN_UNAVAILABLE`. The dictionary now gives field-specific representations, units/encodings, examples, implications, limits and provenance. The index identifies Netem as software-testbed material, the conflicting Announce alias set as quarantined, and associated TIMESAFE captures as externally sourced with local launch linkage unresolved. Decoder limits (classic-PCAP Ethernet focus, non-expanded TLVs/VLANs/payloads) are explicit in `PCAP evidence gaps`.

Targeted full-history review at HEAD `77a47ccb87a8170f1067f7783b12c9ed742ceb6f` found the production PCAP addition/rename in commit `fb0b60d582710baed897395502c049b74e453689`; it did not yield a capture-specific labeler, receiver, configuration, or recovery log. The preserved TIMESAFE author preprint was consulted only for narrative context (pp. 5-6, 10-11, 20). The ACM version of record remains unavailable locally after HTTP 403 and was not represented as inspected evidence.
