# Aborted S15 batch — 2026-09-13T18:07Z to 18:22Z

Preserved in full. Excluded from all estimation. Not deleted, not edited.

Started under `S15_INDEPENDENT_VALIDATION_PROTOCOL_V3.json`. The smoke run passed all nine checks and
seven batch trials completed and verify clean. The eighth trial, `20260913_s15_j200_r2`, was destroyed
mid-execution and the batch loop died with it, because the trial runner script was rewritten in place
while bash was executing it. See D6 in `../PROTOCOL_DEVIATION_REGISTER.md`.

Twenty-two trials never ran. No evaluation was ever run against this data and no agreement,
sensitivity or specificity figure was derived from it.

The seven clean trials, for the record only:

| run | valid windows | first-window dispersion (ns) |
|---|---|---|
| j020_r1 | 5 | 13408 |
| j060_r1 | 4 | 13621 |
| j100_r1 | 4 | 23609 |
| j100_r2 | 4 | 25426 |
| j140_r1 | 4 | 40668 |
| j140_r2 | 4 | 34838 |
| j200_r1 | 4 | 46356 |

These are NOT part of the S15 test set. A decision rule may not be tuned against them, and they are
not pooled with the replacement batch: they were collected under a protocol whose apply-bracket
instrumentation has since been corrected, and their sequence contains a corrupted trial.
