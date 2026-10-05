# S11 and S12 — software packet-path feasibility evidence

**Current statement (2026-09-13).** This supersedes earlier wording that described a
numeric handover interval or a capture suffix as an actual post-takeover interval.
Historical source records remain unchanged.

## Bound evidence

`S11_CLOSED_LOOP_EVALUATION.json` rehashes every evaluator-consumed input listed in
each source manifest: both captures, sealed decision log, receiver log, and the two
used tc files. A manifest missing a required input, malformed line, or duplicate
basename is rejected. Three runs (`act4`, `noact3`, `noact4`) have retained lines
appended after sealing; only their matching sealed decision-log prefixes are decision
evidence. All ten runs were receiver-MASTER eligible; any future MASTER run is retained
but excluded from the frozen primary denominator.

## S11 — commanded port selection

| Arm | eligible runs with port-1 fault then port-2 takeover | Detector triggered |
|---|---:|---:|
| action | 5/5 | 5/5 |
| no_action | 0/5 | 5/5 |

All action commands returned zero. This supports only that, in this isolated software
topology, the externally commanded port-down is associated with the logged port
selection difference relative to a matched no-action control.

The detector/action log uses host monotonic time. The sealed ptp4l printed timestamp
basis was not established from a local pinned source and no cross-clock mapping was
recorded. Thus the log supports ordering *within* `slave.log`, not a numeric
command-to-fault or fault-to-takeover duration.

## S12 — selected-capture suffix comparison

| Arm | selected capture | eligible clean suffixes | persistence observations |
|---|---|---:|---|
| action | segment 2, selected from sealed port-2 takeover evidence | 5/5 | 0 each |
| no_action | segment 1, selected from sealed no-change evidence | 0/5 | 4, 5, 7, 5, 6 |

The split is the detector-recorded capture-packet timestamp. It is a capture-time
suffix comparison, **not** a measured interval after the command or takeover. Each run
has 50–229 valid gap observations after the split (eligibility threshold: 16), with a
12–29 second reported capture window.

## Limits

- Five runs per arm is feasibility evidence, not a deployment performance estimate.
- The netem impairment remained. This is not repair, clock recovery, timing-quality,
  service-restoration, attack response, GNSS/SyncE, or physical O-RAN evidence.
- Endpoints share a host software clock with `free_running 1`.
- The outcome is a packet/protocol observation; it neither measures nor proves a
  receiver clock error or health state.
