# V2 control-flag diagnosis

This is a read-only trace of the frozen V2 rule, not a post-hoc validation or a change to V2. Its machine-readable counterpart is [V2_CONTROL_FLAG_DIAGNOSIS.json](V2_CONTROL_FLAG_DIAGNOSIS.json).

The rule emitted 52, 56, and 57 trailing-dispersion observations in the three configured-netem captures. It also emitted eight in baseline `20260913_v2_b1`, one in no-action control `20260913_v2_c2_retry`, and eight in `20260913_v2_c3`; it emitted six in authorised termination `20260913_v2_s1_retry`.

The first flagged baseline window contains one 1.270 ms Sync–Follow_Up capture-arrival gap; the first flagged no-action `c3` window contains one 2.041 ms gap. The netem windows contain varied microsecond-scale capture-arrival gaps. These exact values and packet ordinals are retained in the JSON trace.

This establishes what the frozen packet parser and rule consumed. It does **not** establish why those gaps occurred: software scheduling, capture timestamping, protocol execution, and configured netem remain possible contributors. It consequently supports neither a timing-health claim nor an attack/recovery conclusion.

## Superseded and replacement prospective revision

The first proposed V3 revision accumulated observations for an entire capture. It was found before any V3 execution to be unbounded and has been preserved as [superseded](V3_PROSPECTIVE_PROTOCOL.json), not used.

[V3_WINDOWED_PROSPECTIVE_PROTOCOL.json](V3_WINDOWED_PROSPECTIVE_PROTOCOL.json) keeps V2 parsing, context scope, malformed-data handling, and trailing window unchanged. Its replacement condition requires four V2 candidate observations for one exact context in a one-second trailing arrival window. Its candidate deque expires only on a later valid packet in that context; invalid/unknown data neither counts nor defaults to healthy. These are provisional engineering parameters for a fresh feasibility study—not V2-fitted performance thresholds—and no repeated tuning is authorized.
