# V2 repeated evaluation — bounded software feasibility

## Status

Completed as a predeclared, isolated-software feasibility evaluation, not a deployment, live-loop, attack-classification, receiver-outage, or clock-recovery result. The protocol was frozen before the listed runs: [V2_REPEATED_EVALUATION_PROTOCOL.json](V2_REPEATED_EVALUATION_PROTOCOL.json). All twelve intended condition attempts have a structurally complete final capture; two earlier partial attempts (`20260913_v2_s1`, `20260913_v2_c2`) remain retained and excluded, with their completed retries named in the machine-readable result.

## Run-level results

The analysis unit is a run, never a packet or an emitted event. Each condition has `n=3`; two-sided Wilson 95% intervals are descriptive and very wide.

| Frozen condition | Impairment-suspect runs | Source-Announce-silence runs | Interpretation |
|---|---:|---:|---|
| Baseline control | 1/3 (33.3%; 6.1–79.2%) | 0/3 (0–56.1%) | A false positive occurred for the predeclared timing-pattern rule. |
| Netem delay/jitter/loss | 3/3 (100%; 43.9–100%) | 0/3 (0–56.1%) | The pattern occurred under the configured software impairment. This is association in a small pilot, not a universal detection rate. |
| Authorised source change, no action | 2/3 (66.7%; 20.8–93.9%) | 0/3 (0–56.1%) | The impairment flag lacks required control specificity. |
| Authorised source termination (“intervention” scenario label) | 1/3 (33.3%; 6.1–79.2%) | 3/3 (100%; 43.9–100%) | The independent per-source observation saw Announce silence after the authorised termination. It does not establish maliciousness, receiver selection, service outage, or recovery. |

The full counts, first observed times relative to capture start, valid-state counts, `UNKNOWN` counts, capture hashes, and exclusions are in [V2_REPEATED_EVALUATION.json](V2_REPEATED_EVALUATION.json). Missing, malformed, unsupported-version, timestamp-regression, and unmatched/reused-sequence observations remain explicit `UNKNOWN`/invalid states; no missing value defaults to healthy.

## Acceptance decision

The causal streaming mechanics and bounded-state tests pass. The current predeclared `CONFIGURED_IMPAIRMENT_SUSPECT` condition is **not accepted as a detector**, because it fires in controls. The source-silence event is a scoped packet-stream observation only. Stage 3 closed-loop action was not started: the protocol requires a separate reviewer decision, and this feasibility result does not justify it. The testbed runs with `free_running 1` and shared host software clocks, so no physical timing, GNSS, SyncE, oscillator, or clock-recovery outcome is measured.

## Reproduction and limits

Run `python outputs/empirical_software_network_pilot_v1/evaluate_v2_repeated.py` from the repository root. The evaluator is replay/serialization analysis of the frozen output; the focused streaming and pilot structural suite is the separate behavioral check. Results are retained with captures and manifests; distinct capture hashes do not make these independent deployment experiments.
