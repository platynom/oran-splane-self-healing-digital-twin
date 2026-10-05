# Finish checkpoint — 2026-09-13

## Completed in this continuation

1. Replayed S11 with fail-closed per-file manifest verification. All 220 sealed-manifest entries rehash. `act4`, `noact3`, and `noact4` have post-seal decision-log tails. Their sealed prefixes match the recorded manifest (4, 3, and 3 lines respectively); the appended `stream_ended`/`detector_finished` rows are retained but excluded from decision evidence. No other mismatch is accepted.
2. S11 now rejects absent sealed trigger/arm records, incomplete/ambiguous manifests, and receiver-MASTER outcomes from the primary denominator. It does not assert the printed ptp4l timestamp basis: no sealed cross-clock mapping exists, so numeric command-to-fault/takeover duration is not established.
3. S12 now selects the replay capture from sealed S11 receiver-transition evidence, rather than from the trial arm alone. Every result had at least 50 valid capture-suffix gap observations (minimum eligibility is 16). The observed 5/5 versus 0/5 separation is packet/protocol evidence only, and is not timed as post-takeover.
4. A source-split full-detail S13 export is complete: 171,988 raw packet rows in `s13_dataset/s13_packets.csv`, with all 8,532 receiver-log lines, events, seal-scoped decisions, receiver transitions and outcomes in `S13_empirical_full_detail.xlsx`; reconciliation is in `s13_full_detail_reconciliation.json`. The workbook is not described as containing the full packet table because the bounded Artifact Tool build could not materialize that 171,988-row sheet.
5. Relevant package tests run from the actual module directory: 24 passed, plus 4 focused evaluator-boundary tests. A broad root-level pytest invocation has an unrelated import-path collection error (`faults` module), not treated as a behavioral pass.

## Current evidence disposition

- Accepted: sealed S11 capture/config/log inputs; sealed decision prefixes; S12 eligible packet replays.
- Preserved but not sealed decision evidence: the three decision-log tail appends described above.
- Not established: numeric trigger-to-fault order, physical clock recovery, timing quality, service restoration, maliciousness, or production deployment performance.

## Remaining numbered work

1. Create a new versioned S11 runner for future experiments that drains/waits/syncs writers before sealing. Do not alter the historical frozen runner, whose byte hash is part of S11 eligibility.
2. Keep the source-split packet CSV beside the workbook unless a tested spreadsheet pipeline can materialize the packet sheet without truncation or runtime failure.
3. Complete source-disposition coverage for any newly created future-run files; the prior repository coverage report remains the current historical inventory.
4. Add/execute a separately versioned S11 runner only if further experiment evidence is needed; do not overwrite or reseal historical source manifests.

## Immediate next step

The versioned writer-drain/seal component `seal_owned_writers_v2.sh` passed its bounded WSL FIFO test: it validates direct-child ownership, drains producer→consumer EOF, records normal/failure/timeout exits, excludes its own manifest/FIFO, and does not seal failure directories. `run_s11_closed_loop_v2.sh` is future-run integration scaffolding only; no new trial used it. The frozen historical runner and manifests remain unchanged.

## Historical usage checkpoint — 2026-09-13

This records an earlier limit only; the user later authorized resumption. The full 171,988-row streaming XLSX is now complete. The separately versioned drain/seal runner remains under independent review and is not used to reseal historic trials.
