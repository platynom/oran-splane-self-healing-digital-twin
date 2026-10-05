# Software-only objective checkpoint — 2026-09-13

## Budget checkpoint

The initial shared primary-window reading for this continuation was 80% remaining. The user requested a conservative proxy of no more than half of that allowance because exact session-token accounting is unavailable. The current primary window is 21% remaining, so no new substantive stage was started. This is a checkpoint, not a final scientific completion claim.

## Finite software acceptance checklist

| # | Software-only objective | Status | Evidence or remaining work |
|---|---|---|---|
| 1 | Isolated, pinned, free-running software testbed with provenance | Complete for V2/V3 pilot | LinuxPTP 3.1.1, namespace/veth isolation, manifests, process logs, and structural validators. Shared-host software clocks remain a material limitation. |
| 2 | Causal PTP packet parser/event handling | Complete for tested mechanics | Malformed lengths, versions, timestamps, sequence reuse, context isolation, source-silence events, and bounded non-overlapping blocks have focused tests. |
| 3 | Frozen prospective empirical feasibility measurement | Complete, limited pilot | V3: 20 structurally complete runs, 220 rehashed manifest inputs, 5/5 configured-netem and 0/10 baseline/no-action controls for the frozen observation. See `V3_NONOVERLAPPING_EVALUATION.json`. |
| 4 | Scientifically defensible detector performance | Unsupported | A single `n=5` isolated pilot with provisional parameters and wide intervals is not deployment/generalization evidence. No further tuning may use the V3 evaluation set. |
| 5 | Broader independent prospective validation | Remaining | Freeze a separate protocol before new runs. Include justified benign network variations and controls, preserve failures, and report run-level uncertainty without reusing V3 for parameter selection. |
| 6 | Live software detection mechanism | Remaining | Establish read-only stream/capture ingestion and timestamp/ack feasibility in the isolated namespace before any experiment. It must use no filenames/scenario labels or future packets. |
| 7 | Detector-triggered, supported software action loop | Remaining | Requires a separate frozen action protocol, action acknowledgments, randomized paired action/no-action controls, and measured packet/protocol outcomes. Scheduled removal of netem or stopping a master is not sufficient evidence of autonomous recovery. |
| 8 | Clock-recovery/physical-health objective | External architecture blocker | Shared-host `free_running 1` endpoints cannot establish independent-clock recovery, GNSS/SyncE/oscillator health, or physical timing benefit. This boundary does not block packet/network-loop work. |
| 9 | Empirical row-level spreadsheet export | Remaining | Create only after the next experiment stage has final run data. It must separate condition, observed impact, event, proposed action, executed action, outcome, missing/invalid state, and provenance. Original/frozen data remain unchanged. |
| 10 | Reproducible package and beginner material | Partly complete | Protocols, evaluators, run manifests, tests, and concise reports exist. The final software package and teaching/export workbook await the remaining stages. |

## Resumption order

1. Check a fresh shared usage reading and resume only if the budget allows.
2. Read this checkpoint, `CURRENT_ACCEPTANCE_LEDGER.md`, and the V3 protocol/evaluation; preserve all frozen files and raw run directories.
3. Freeze a broader independent validation protocol before creating any runs. Do not retune V3 parameters using its 20 runs.
4. Only after detector validation, implement an isolated live action mechanism with command/ack/state logs and paired no-action controls.
5. Then create the requested spreadsheet export using the spreadsheet workflow and verify it visually and against source manifests.

## Explicit exclusions

No current result establishes maliciousness, receiver selection, service outage, physical timing quality, GNSS/SyncE/oscillator health, or successful recovery. Historical C0-C3 packet observations remain separate from fault/attack semantics.
