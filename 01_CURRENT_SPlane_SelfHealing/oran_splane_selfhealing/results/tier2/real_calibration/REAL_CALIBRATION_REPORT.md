# Real-Data Calibration Report

Evaluation unit: complete capture session. No windows from a test capture appear in training. Confidence intervals are 95% Wilson intervals.

All real windows: 379 benign, 7555 attack across 5 sessions.

Session holdout train captures: `announce_session_1, announce_session_2, announce_session_3`.

Session holdout test captures: `sync_followup_session, sync_singlestep_session`.

| method | held out | benign FP count | benign FP rate [95% CI] | attack TP count | attack TP rate [95% CI] |
|---|---|---:|---:|---:|---:|
| baseline_sim_rf | session_holdout | 245/245 | 1.000 [0.985, 1.000] | 596/596 | 1.000 [0.994, 1.000] |
| baseline_flat_threshold | session_holdout | 245/245 | 1.000 [0.985, 1.000] | 596/596 | 1.000 [0.994, 1.000] |
| recalibrated_threshold_26927ns | session_holdout | 5/245 | 0.020 [0.009, 0.047] | 596/596 | 1.000 [0.994, 1.000] |
| real_trained_rf_session_holdout | session_holdout | 0/245 | 0.000 [0.000, 0.015] | 0/596 | 0.000 [0.000, 0.006] |
| real_trained_rf_leave_one_attack_out | announce | 0/134 | 0.000 [0.000, 0.028] | 1656/6959 | 0.238 [0.228, 0.248] |
| real_trained_rf_leave_one_attack_out | sync_follow_up | 0/89 | 0.000 [0.000, 0.041] | 298/298 | 1.000 [0.987, 1.000] |
| real_trained_rf_leave_one_attack_out | sync_single_step | 0/156 | 0.000 [-0.000, 0.024] | 298/298 | 1.000 [0.987, 1.000] |

The session-holdout row is the primary transfer estimate. Leave-one-attack-out rows test family generalization and are omitted when the supplied captures do not leave both classes in train and test.

## BMCA feature importances

Importances come from the capture-isolated session-holdout RF. Raw GM identity is not a model feature.

| relative BMCA feature | importance | overall rank |
|---|---:|---:|
| clock_class_changes | 0.182027 | 1 |
| gm_identity_changes | 0.167388 | 2 |
| steps_removed_changes | 0.161524 | 3 |
| clock_class_improve_jump | 0.068507 | 7 |
| gm_identity_churn | 0.044214 | 8 |
| steps_removed_min | 0.014278 | 12 |
| priority1_changes | 0.000000 | 18 |


**Cross-family caution:** this split trains on Announce sessions and tests on Sync-attack sessions; RF attack recall is 0.0%. The BMCA features make Announce observable but can make a closed-set RF specialize in that family. Interpret this row alongside leave-one-family-out and open-set protective coverage.
