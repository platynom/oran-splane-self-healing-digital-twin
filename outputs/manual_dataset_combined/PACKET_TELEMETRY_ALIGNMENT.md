# Production packet-to-telemetry alignment

## What and which

The configured production PCAP has 13,565 decodable PTP packets. A read-only trace mirroring `ingest/pcap_ingest.py` produced 13,562 telemetry emissions. The detailed machine-readable trace is `production_packet_telemetry_alignment.json`.

## Where and when

`t_s` is seconds from the first decodable PTP packet in this capture. It is not UTC and must not be used to join another capture. Telemetry starts at packet index 4 (0.008973 s).

## How the difference arises

The first three packets are Delay_Req, Delay_Resp, and Announce. They cannot produce timing telemetry because the state machine has no resolved Sync origin/arrival pair yet. They are the only packets with no eventual emission.

There are 392 two-step Sync packets. Each is initially deferred while awaiting its matching Follow_Up; after the Follow_Up arrives, the state machine emits one Sync observation for the original packet and one for the Follow_Up. Thus “initially skipped” is not “dropped.” There are no unresolved pending Sync exchanges at capture end.

Every emitted telemetry row has exactly one source packet in this trace. No source packet emitted more than one row. Fifty-five Delay_Req sequence IDs remain unmatched by a Delay_Resp at capture end; they still emitted telemetry using the current timing state, so this is a stale/missing-exchange limitation, not a missing telemetry row. There are 118 duplicate emitted `t_s` values, so time alone is not a unique observation key. No message-type/sequence pair was reused in this capture.

## Why it matters

The evidence supports a capture-local packet-to-derived-observation transformation. It does not make the calculated offset a hardware receiver measurement, validate a packet label, or prove health/attack/recovery. A window is many telemetry rows; because 0.4-second windows move by 0.2 seconds, neighboring windows overlap. A decision is downstream model output, not a further source observation.

## Remaining ambiguity

The legacy telemetry schema does not store source packet index/byte offset. A new audit sidecar, `production_telemetry_lineage.csv`, now binds all 13,562 regenerated outputs to the exact PCAP hash and packet index. `verify_production_lineage.py` checks the actual ingester output using capture-specific, verified-unique message-type/sequence keys and exact capture times. `production_lineage_verification.json` records code, output and sidecar hashes. This closes row linkage for that regeneration only; it does not establish linkage to every historical derived CSV, physical accuracy, window lineage or recovery. No unrelated experiments are joined by elapsed time.
