# Usage-limit handoff — 2026-09-08

Stopped before new substantive work because the current shared 300-minute window reported 98% used (2% remaining); weekly window reported 29% used. No reset was requested or used.

## Completed and preserved

- `ORAN_All_Current_Datasets_FINAL_PCAP.xlsx` SHA-256 `8ea44ed7d1a1905e3cd57e7e26583201b0e41975722ed199b6db6555d150d5bf` passed all-packet row-width/provenance checks, source-hash checks and ZIP checks.
- Fallback width/state and domain-scoped Announce rule corrections are implemented and regression-tested in `test_final_pcap_export_regressions.py`.
- Originals and inherited 49 sheets remain preserved.

## Remaining focused work (do not broaden)

1. Correct `pcap_definition()` so `PTP originTimestamp ns (derived)` is a PTP message-body timestamp, not a capture-record timestamp. Add a dictionary mapping assertion.
2. Replace generic packet-field definitions for packet ordinal, frame length, EtherType, flags and source port with exact meanings/units. Make `Source`/`Destination` representation caveats source-specific.
3. Replace synthetic `render_pcap_guides.mjs` fixtures with a bounded extraction of actual saved workbook dictionary and production-PCAP header/data cells, retaining their saved widths/styles/row heights; inspect those renders.
4. Update the consolidation report to state only the actual saved-file render result. Rebuild/reconcile only if workbook dictionary content changes.

The final workbook remains a candidate pending those guide/render corrections; do not describe it as scientifically validated.
