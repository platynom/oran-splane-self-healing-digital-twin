# S7 checkpoint — V4 broader validation complete

Date 2026-09-13.

## Completed step IDs
S1–S6 previously. **S7 finished this stage.**

## What was done
1. Established batch state: all 25 V4 run directories completed 02:39–02:44 UTC; no process writing.
   The missing `validation.json` meant validation was pending, not that runs failed.
2. Verified all four frozen protocol hashes against the files on disk before any replay.
3. Ran the frozen validator over all 25 runs: 25 STRUCTURALLY_COMPLETE, 0 failures, no exclusions,
   no retries, nothing deleted.
4. Wrote `evaluate_v4_broader.py` as a faithful adaptation of `evaluate_v3_nonoverlap.py`
   (same frozen detector, same thresholds, five V4 conditions, v4_runs).
5. Reproduced the evaluation. 280 manifest entries rehashed across 25 runs, all matching.

## Artifacts
- `V4_BROADER_EVALUATION.json`
- `V4_BROADER_EVALUATION_REPORT.md`
- `evaluate_v4_broader.py`
- `v4_runs/*/validation.json` (25 new)

## Result
Dispersion-persistence observation: 5/5 configured impairment; 0/5 baseline; 0/5 benign
delay+jitter without loss; 0/5 authorised source change no action; 0/5 authorised source
termination. Pooled non-loss 0/20, Wilson 95% [0, 0.1611]; impairment [0.5655, 1.0]; non-overlapping.
First observation 5.45–8.88 s. Source-Announce-silence event 5/5 in termination runs only,
independent of the dispersion channel. 5 of 16,976 records rejected as timestamp regressions.

## Limitations recorded
- The impairment and benign conditions differ in three parameters simultaneously (delay, jitter,
  loss). V4 cannot attribute the observation to loss. A single-variable series is required.
- n=5 per condition. Feasibility repetition, not detector accuracy or generalisation.
- Shared-host software clocks, free_running 1. No physical timing, attack, health, outage or
  recovery claim.

## Next step
S8 — evidence-supported classification decision: state exactly which conditions can and cannot be
classified, the observed false-alarm and miss behaviour, and the operating limits. The
three-parameter confound above is the first thing S8 must record.
