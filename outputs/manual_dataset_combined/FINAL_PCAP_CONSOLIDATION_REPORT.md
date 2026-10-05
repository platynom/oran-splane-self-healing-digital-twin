# Final PCAP consolidation verification

## Deliverable

`ORAN_All_Current_Datasets_FINAL_PCAP.xlsx` SHA-256: `5b4b7423219f4d60c34c0064ef81458f53fe3238fe844b01864567ae52259803`. It is an append-only copy of the corrected 45-source workbook: 49 inherited worksheets are byte-identical, plus 19 PCAP guide/export sheets (68 total).

The final layout-only patch modified only `PCAP dictionary` and `styles.xml`: all 67 other worksheet parts remained byte-identical. `MessageType` and `Source` now use 135-point, top-aligned wrapped rows; remaining dictionary rows stay wrapped at 90 points.

## Checks

- Rehashed all 45 source files against `detailed_plan.json`: matched.
- Preserved 523,176 rows and 9,590,610 original lexical cells: the prior full CSV-to-workbook reconciliation remains applicable because all 49 inherited worksheet XML parts are byte-identical.
- Rehashed and exported 14 canonical classic-PCAP files. Every record is retained; 267,084 is the largest export, below Excel's 1,048,576-row limit. Non-PTP/unsupported frames remain with explicit parse status.
- ZIP integrity passed; all 68 sheet names are unique; new sheets contain no formulas or Excel error cells.
- Every saved PCAP row passed the 39-cell schema and fixed provenance-position checks. The canonical capture and decoder hashes are columns 38 and 39. Non-PTP uses `NOT_APPLICABLE`; truncated/invalid PTP uses `UNKNOWN_UNAVAILABLE`.
- PCAP index records aliases, origin/disposition and the conflicting Announce-capture quarantine. The production capture `0690...20599` contains 13,565 records and five R-PCAP-01a/b/c domain-scoped advertised identity/attribute-change rows. Those rows are observable header changes only.
- Actual saved-workbook cells were extracted with their literal values, style IDs, widths and row heights, then rendered for the dictionary and production-PCAP header/data samples. The dictionary guide rows use 90-point wrapped rows and headers use 42-point wrapped rows.

## Context checked, not converted to measurements

Targeted full-history check at HEAD `77a47ccb87a8170f1067f7783b12c9ed742ceb6f` found production-PCAP addition/rename in `fb0b60d582710baed897395502c049b74e453689`; it did not establish label generation, receiver source selection, GNSS/SyncE/oscillator health, or recovery execution. The existing author preprint discusses BMCA/testbeds/features on pp. 5-6, 10-11 and 20. The ACM version of record remains unavailable locally (publisher access was 403), so the preprint is narrative context, not an experiment log.

## Remaining evidence limits

Supplied annotations stay separate from packet-derived observations. The workbook does not claim unauthorized takeover, physical timing degradation, GNSS loss, authenticated receiver selection, or successful recovery. The decoder covers classic-PCAP Ethernet, common PTPv2 headers and Announce fields; non-expanded TLVs, VLAN parsing, payload bodies and non-Ethernet link semantics remain in raw PCAP rather than invented columns. Those claims require the missing receiver/topology/configuration, injection/label-generation, timing-reference and recovery-execution records listed in `PCAP evidence gaps`.
