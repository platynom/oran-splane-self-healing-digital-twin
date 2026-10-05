# Superseded by streaming protocol v2

The former zero-silence conclusion was a V1 event-composition bug: a silence classification was overwritten by later per-message classifications. Do not use this report for source-silence conclusions; see `STREAMING_PROTOCOL_V2.json` and the regenerated evaluation JSON.

# Causal streaming protocol v1 — fresh pilot result

The frozen causal engine was tested on four fresh, structurally validated captures collected after its configuration was written. It processes capture order only, has no EOF feature, and keys state by capture/protocol/domain/source identity.

| Fresh condition | Packets | `CONFIGURED_IMPAIRMENT_SUSPECT` | First suspect | Interpretation |
|---|---:|---:|---:|---|
| Baseline | 864 | 0 | — | No frozen-rule suspect in this one run. |
| Netem delay/jitter/loss | 840 | 96 | 2.914 s | Configured-impairment observation only. |
| Source-change no-action control | 874 | 0 | — | No frozen-rule suspect in this one run. |
| Authorised source stop | 1,334 | 0 | — | No impairment-rule suspect; this does not establish service continuity or recovery. |

The preceding source-stop statement is superseded. V2 emits one deduplicated, arrival-driven source-silence observation at 14.892 s in the saved V1 source-stop capture. It remains an advertisement observation only, not receiver outage or recovery evidence.

This is a **one-run-per-condition feasibility check** using a threshold selected after Set2/3 development inspection. It is not an accuracy estimate, confidence interval, permutation test, independent deployment result, attack detector, clock-health measurement, or action trigger. Closed-loop action is therefore not authorized by this evidence.

Evidence details, capture hashes, state counts, and first-state times are in [STREAMING_PROTOCOL_V1_FRESH_EVALUATION.json](STREAMING_PROTOCOL_V1_FRESH_EVALUATION.json).
