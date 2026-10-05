# V5 single-variable attribution — evaluation report

Date 2026-09-13. Protocol `v5-single-variable-attribution-protocol-2026-09-13` (`V5_SINGLE_VARIABLE_PROTOCOL.json`).
Results file `V5_SINGLE_VARIABLE_EVALUATION.json`. Evaluator `evaluate_v5_single_variable.py`.

## Batch state

All 25 planned runs completed in interleaved order (a, b, c, d, e across repetitions 1..5).
All 25 runs were validated STRUCTURALLY_COMPLETE with zero errors, then evaluated.

## Frozen-input verification

Frozen hashes match: True.
- v1_engine_sha256: `1c1d7edfbcc38b6e0c950984eff72b58592160c71ad8e797ff719d4aee0b8d0e`
- v3_nonoverlap_engine_sha256: `ee328876367e6547878f85eed60405624f55bd21a03348f4d9527fd302250172`
- isolated_runner_sha256: `d25a8441640f9d6faacbecfc9dba6bb50f7305bb555e5d9c556ab2831e118e79`
- validator_sha256: `5ebc2033e0c243f756ff02f8280c2fd115d43ecbd589697ffdee3cb6887d7e13`
Thresholds: std 0.00016 s, block size 8, high-block count 2, window 3.0 s.
No threshold, arm, or inclusion criterion was changed. V1–V4 captures were excluded.

## Run-level result — persistence observation per arm

| Arm | Description | k / n | proportion | Wilson 95% |
|---|---|---|---|---|
| A_reference_benign | reference benign (delay 100us, jitter 20us, no loss) | 0 / 5 | 0.00 | [0.0000, 0.4345] |
| B_loss_only | loss only (+ 1% loss to reference) | 0 / 5 | 0.00 | [0.0000, 0.4345] |
| C_jitter_only | jitter only (+ 200us jitter to reference) | 3 / 5 | 0.60 | [0.2307, 0.8824] |
| D_delay_only | delay only (+ 1000us delay to reference) | 0 / 5 | 0.00 | [0.0000, 0.4345] |
| E_full_v4_impairment | full V4 impairment (delay 1000us, jitter 200us, loss 1%) | 3 / 5 | 0.60 | [0.2307, 0.8824] |

Integrity: 300 manifest entries rehashed across 25 runs, all matching.

## Pre-specified interpretation branch selection

The data selected branch: **`if_only_C_and_E_positive`**

> **Pre-specified interpretation statement:** the observation is attributable to configured jitter magnitude

### Branch evaluation details
- Arm A (reference benign): 0 / 5 positive
- Arm B (loss only): 0 / 5 positive
- Arm C (jitter only): 3 / 5 positive
- Arm D (delay only): 0 / 5 positive
- Arm E (full V4 impairment): 3 / 5 positive

## First observation times for positive arms

- **A_reference_benign**: 0 runs observed persistence
- **B_loss_only**: 0 runs observed persistence
- **C_jitter_only**: observed in 3 runs, range 5.256 s to 8.257 s (median 7.899 s)
- **D_delay_only**: 0 runs observed persistence
- **E_full_v4_impairment**: observed in 3 runs, range 5.840 s to 7.351 s (median 7.254 s)

## Persistence rule behavior across arms

Single high-dispersion block occurrences by arm: {'A_reference_benign': 0, 'B_loss_only': 0, 'C_jitter_only': 0, 'D_delay_only': 0, 'E_full_v4_impairment': 0}
The persistence rule requires 2 high-dispersion blocks within 3.0 s.

## Independent source-silence channel

`SOURCE_ANNOUNCE_SILENCE_OBSERVED` counts by arm: {'A_reference_benign': 0, 'B_loss_only': 0, 'C_jitter_only': 0, 'D_delay_only': 0, 'E_full_v4_impairment': 0}

## Invalid-data handling

Total packet records processed: 15598.
Total invalid / rejected records: 1 (0.006%).

## Decision boundary and limits

- V5 can attribute the observation to a configured netem parameter under these software conditions only.
- V5 does not establish receiver harm, attack detection, physical timing quality, or recovery.
- Shared-host software networking with free_running 1 means endpoints do not have independent physical clocks.
- Packet-arrival dispersion is not a referenced receiver clock-error measurement.

