# S11 and S12 — closed-loop trial and measured outcome

> **Superseded wording warning (2026-09-13):** The current, evidence-bounded account is
> [`S11_S12_CURRENT_REPORT.md`](S11_S12_CURRENT_REPORT.md). In particular, this historical
> draft's numeric handover claims and its description of the capture suffix as post-takeover
> are not supported by a recorded cross-clock mapping. It must not be used as current evidence.

Date 2026-09-13. Protocols `S11_CLOSED_LOOP_PROTOCOL.json` (frozen before any trial).
Results `S11_CLOSED_LOOP_EVALUATION.json`, `S12_MEASURED_OUTCOME.json`.
All frozen hashes matched before replay. Ten trials, action and no-action interleaved.

## Design in plain words

Two separate small networks (segments), each with its own timing source. One receiver has a foot in
both: it uses segment 1 and keeps segment 2 in reserve. We add jitter to segment 1 - the parameter
V5 showed the detector actually responds to. A live detector watches segment 1 packet by packet.
In the **action** arm it commands the receiver to stop using segment 1 the moment it sees the
problem. In the **no-action** arm everything is identical and the command is withheld.

## S11 — did the commanded action move the receiver?

| Arm | receiver moved to the clean segment | Wilson 95% | detector triggered |
|---|---|---|---|
| action | **5/5** | [0.5655, 1.0000] | 5/5 |
| no_action | **0/5** | [0.0000, 0.4345] | 5/5 |

Pre-specified branch selected: `action_>=4of5_and_no_action_0of5`
> the commanded action, and not the passage of time or the impairment alone, moves the receiver off the impaired segment under these software conditions

The detector fired in all ten trials, so both arms saw the same condition. Every action-arm command
returned zero; there were no execution failures.

Latencies, action arm:
- detection trigger to command result: 6.0 to 21.7 ms
- impaired port fault to standby port takeover: 22 to 106 ms

On-wire corroboration during the impaired phase, packets leaving the bridge toward the receiver on
segment 1: action arm [103, 53, 470, 51, 134], no-action arm [844, 841, 846, 837, 846]. The receiver stopped drawing traffic from
segment 1 in the action arm and kept drawing it in the control.

## S12 — did it make a measured difference?

Measured on the segment the receiver is **actually using** after the trigger: segment 2 in the
action arm, segment 1 in the no-action arm. The split instant is the packet timestamp recorded in
the decision log, so it comes from the same timebase as the capture.

| Arm | active path clean after trigger | Wilson 95% | persistence events after trigger |
|---|---|---|---|
| action | **5/5** | [0.5655, 1.0000] | 0 in every run |
| no_action | **0/5** | [0.0000, 0.4345] | [4, 5, 7, 5, 6] |

Observation windows after the trigger ranged from about 12 to 29 seconds and are recorded per run.

## What this establishes

A detector-triggered, externally commanded action moved the receiver off a degraded timing segment
within about 0.1 second of the command, in every trial, and the packet observation that triggered it
was absent from the receiver's active path afterwards. A matched control receiving the identical
impairment, with the command withheld, never moved and kept showing the observation.

## What this does NOT establish

- **Nothing was repaired.** The netem impairment stayed on segment 1 for the whole trial. The action
  changes which segment the receiver uses. It is not a fix, and no laboratory impairment was removed.
- The action-arm segment 2 was clean before the action as well as after. The measured quantity is
  "the observation on whatever path the receiver is using", which is the operationally meaningful
  one; the control shows it stays bad without the action.
- No clock-error, timing-quality, holdover or service-restoration measurement was made. Endpoints
  share one host software clock under `free_running 1`.
- No attack was involved. No physical O-RAN behaviour is demonstrated.
- n=5 per arm. Feasibility with a control, not a performance estimate. Detector sensitivity remains
  roughly 13 of 15 from V3-V5; a non-trigger would be a miss, and none occurred here.
