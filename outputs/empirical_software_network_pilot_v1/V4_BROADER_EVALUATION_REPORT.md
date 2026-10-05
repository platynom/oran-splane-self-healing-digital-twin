# V4 broader validation — evaluation report

Date 2026-09-13. Protocol `V4_BROADER_VALIDATION_PROTOCOL.json` (frozen before any V4 capture).
Results file `V4_BROADER_EVALUATION.json`. Evaluator `evaluate_v4_broader.py`.

## Batch state

All 25 planned runs completed (02:39–02:44 UTC) and nothing was writing at evaluation time.
No `validation.json` existed at handoff: structural validation had not been run, not that runs failed.
All 25 were validated STRUCTURALLY_COMPLETE with zero errors, then evaluated.

## Frozen-input verification

All four protocol hashes matched the files on disk before replay: v1 engine, v3 non-overlap engine,
isolated runner, validator. Thresholds used are the frozen ones: std 0.00016 s,
block size 8, high-block count 2, window 3.0 s.
No threshold, condition or inclusion criterion was changed. V1–V3 captures were excluded.

## Run-level result — persistence observation per condition

| Condition | k / n | proportion | Wilson 95% |
|---|---|---|---|
| netem_delay_jitter_loss | 5 / 5 | 1.00 | [0.5655, 1.0000] |
| baseline_control | 0 / 5 | 0.00 | [0.0000, 0.4345] |
| benign_delay_jitter_no_loss | 0 / 5 | 0.00 | [0.0000, 0.4345] |
| benign_authorized_source_change_no_action | 0 / 5 | 0.00 | [0.0000, 0.4345] |
| authorized_source_termination_observation | 0 / 5 | 0.00 | [0.0000, 0.4345] |

Pooled non-loss conditions: 0 / 20, Wilson 95% [0.0000, 0.1611].
Configured-impairment interval [0.5655, 1.0000] does not overlap the pooled control interval.

Integrity: 280 manifest entries rehashed across 25 runs, all matching.

## First observation times, configured impairment

Persistence first observed at 5.452 s to 8.885 s after the first captured frame
(median 8.255 s), in all five runs.

## The persistence rule earns its place

Isolated single high-dispersion blocks did occur in non-impaired runs:
{'baseline_control': 1, 'benign_delay_jitter_no_loss': 1, 'benign_authorized_source_change_no_action': 1}.
None reached the frozen 2-blocks-within-3-s persistence condition. A single-block rule would have
produced false observations in those runs; the persistence requirement suppressed all of them.

## Source silence is a separate channel

`SOURCE_ANNOUNCE_SILENCE_OBSERVED` counts by condition: {'baseline_control': 0, 'netem_delay_jitter_loss': 0, 'benign_delay_jitter_no_loss': 0, 'benign_authorized_source_change_no_action': 0, 'authorized_source_termination_observation': 5}.
It fired once in each authorised-termination run and nowhere else, while those same runs produced
zero dispersion-persistence observations. Impairment and source loss are reported independently and
neither is an attack, outage, or clock-health label.

## Invalid-data handling

16976 packet records processed. 5 were rejected as `TIMESTAMP_REGRESSION:arrival_order_regression`
(0.029%), distributed across baseline, no-action-control and termination runs. They were
excluded from dispersion blocks rather than crashing or silently passing.

## What V4 establishes, and what it does not

Establishes: under these frozen software conditions the packet-arrival dispersion-persistence
observation repeated in every configured-impairment run and in none of the twenty non-loss runs,
including a benign delay-and-jitter condition.

Does NOT establish, and must not be reported as:
- Attribution to packet loss. The impairment condition differs from the benign condition in THREE
  parameters at once: delay 1000us vs 100us, jitter 200us vs 20us, and 1% configured loss vs none.
  V4 cannot say which parameter drives the observation. A single-variable series is required.
- Detector accuracy or generalisation. n=5 per condition; intervals are wide.
- Any attack, receiver-health, selected-source-loss, service-outage or physical-timing claim.
- Any recovery capability. No action was executed in V4.
- Independent clock measurement. Endpoints share a host software clock with free_running 1;
  packet-arrival dispersion is not a referenced receiver clock-error measurement.
