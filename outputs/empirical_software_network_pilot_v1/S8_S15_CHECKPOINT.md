# S8-S15 checkpoint — software work carried to its architectural boundary

Date 2026-09-13.

## Completed this session
S7 (V4 evaluation), S8, S13, S14, S15 complete. S9 ready. S10 returned a negative feasibility result.
V5 frozen and ready to run.

## Artifacts created
- `V4_BROADER_EVALUATION.json`, `V4_BROADER_EVALUATION_REPORT.md`, `evaluate_v4_broader.py`, 25 `validation.json`
- `S7_CHECKPOINT.md`, `S8_CLASSIFICATION_DECISION.md`
- `V5_SINGLE_VARIABLE_PROTOCOL.json`, `run_v5_single_variable_batch.sh`,
  `harness/run_empirical_software_pilot_v5.sh`, `validate_pilot_v5.py`
- `tests/test_live_detection_causality.py` (7 tests)
- `S9_S10_LIVE_AND_RECOVERY_FEASIBILITY.md`
- `build_s13_dataset.py`, `s13_dataset/` (csv, xlsx, reconciliation)
- `S14_REPRODUCIBLE_PACKAGE.md`, `S15_FINAL_ACCEPTANCE_REVIEW.md`
- `CURRENT_ACCEPTANCE_LEDGER.md` rows 9-16

## Preserved
No run directory was created, deleted, moved or renamed. The V4-frozen runner and validator are
byte-identical. All failed and superseded attempts appear in the S13 dataset with their status.

## Exact blockers
1. **No execution capability in the analysis session.** `ptp4l` is absent and the shell is not root,
   so no new capture can be produced here. V5 must be run in the WSL environment.
2. **S11 and S12 are blocked by topology, not by usage.** A closed-loop recovery experiment needs
   either a second slave-facing path (new runner version, new protocol) or a re-scope of the trigger
   to source switching. That is a design decision, not an analysis step.

## Next actions, in order
1. Run `run_v5_single_variable_batch.sh` in WSL, then evaluate it with a V5 evaluator modelled on
   `evaluate_v4_broader.py`. This resolves the loss-versus-delay-versus-jitter confound.
2. Choose between extending the topology and re-scoping the recovery loop, then write a frozen
   protocol for it before any capture.
