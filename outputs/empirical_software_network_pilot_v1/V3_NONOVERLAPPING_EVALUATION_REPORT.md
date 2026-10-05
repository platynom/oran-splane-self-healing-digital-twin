# V3 non-overlapping-block feasibility evaluation

## Scope and integrity

This is one frozen, isolated software-network pilot: five fresh runs each for baseline, configured netem delay/jitter/loss, authorised source change without action, and authorised source termination. All 20 final run directories are structurally complete. Before replay, the evaluator rehashed all 220 listed capture/config/log inputs against their manifests and rejected stale, missing, malformed, or cached-false verification; all matched. The 20 capture hashes are distinct. Distinct captures do not establish independent deployment experiments.

The evaluator verifies the frozen V1 and V3 implementation hashes before replay. Its output is [V3_NONOVERLAPPING_EVALUATION.json](V3_NONOVERLAPPING_EVALUATION.json). The two earlier V3 proposals were superseded before any V3 capture and are retained only for traceability.

## Frozen, run-level result

| Condition | Persistence-observation runs | Wilson 95% interval | Prospective interpretation |
|---|---:|---:|---|
| Baseline control | 0/5 | 0–43.4% | Met the frozen zero-of-controls feasibility gate in this small pilot. |
| Configured netem delay/jitter/loss | 5/5 | 56.6–100% | Met the frozen at-least-four-of-five feasibility gate. This is an association with the configured isolated condition. |
| Authorised source change, no action | 0/5 | 0–43.4% | Met the other frozen control gate. |
| Authorised source termination | 0/5 | 0–43.4% | Descriptive only; it is neither an attack nor a receiver-outage outcome. |

The prospective feasibility gates therefore pass. This is **not detector acceptance**: the sample is small, intervals are wide, parameters are provisional, all endpoints use shared-host free-running software clocks, and the measured quantity is packet-arrival dispersion. There is no finding about maliciousness, clock health, GNSS/SyncE, receiver source selection, timing-service outage, or recovery efficacy.

## Method limits

V2 rolling eight-pair windows overlap, so one outlier can create several candidates. V3 clears each eight-gap block before starting the next and requires two high-dispersion disjoint blocks ending within three seconds, scoped by capture/protocol/domain/source identity. Disjoint blocks prevent a single gap being counted twice; they are still not independent disturbances. The evaluation retains per-run validity/reason counters and separate packet-stream events (including five deduplicated Announce-silence observations across the 20 runs), rather than collapsing either into a normal or healthy class. Unknown, malformed, unmatched, reused-sequence, unsupported, and timestamp-regression inputs do not create a gap or become healthy defaults.

No rule revision, recovery action, or further experiment was run after seeing these results. Any follow-on must treat this as a limited feasibility result and use an independently reviewed protocol.
