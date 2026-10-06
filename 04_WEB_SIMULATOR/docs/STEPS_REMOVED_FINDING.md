# `stepsRemoved` finding

## Conclusion

The apparent `1` versus `2` conflict is a comparison of two different data items, not conflicting packet evidence.

- The Announce field sent by a legitimate GM is `stepsRemoved=0`.
- After selecting the GM, the primary boundary clock has one path to the GM and sends downstream Announce with `stepsRemoved=1`.
- An RU receiving that Announce increments the value when updating its local `currentDS`; its client-side `currentDS.stepsRemoved` is therefore `2`.

Thus the Testbed Configuration Reference's `0→1` and the raw downstream packet value `1` describe the sender-side Announce progression. The `topology.sh` comment saying that RUs see `2` describes the receiving client's parent/current dataset semantics. The frozen `provisioning.json` name `expected_steps_removed_at_ru=1` is ambiguous: the value matches the packet field arriving at the RU, not the RU's post-update `currentDS`. The frozen rule does not use that context field for a value-equality decision; it uses captured Announce values for conformance and relay attribution. No frozen artifact was changed.

## Raw-evidence audit

`04_WEB_SIMULATOR/ingest/audit_steps_removed.py` reads every `up.pcap.gz`, `dn.pcap.gz`, and `observer.jsonl` member directly from:

`03_RECOVERY_LOOP_S-PLANE/results/recovery_eval_runs_r13-r17.tgz`

It uses Ethernet EtherType `0x88f7`, PTP message type `11`, and Announce bytes 61–62 for the two-byte network-order field. Results:

| Evidence | Result |
|---|---:|
| Observer samples inspected | 52,080 |
| Observer samples with `stepsRemoved` populated | 0 |
| Announce packets decoded | 555,335 |
| GM-A Announce with `stepsRemoved=0` | 63,704 |
| GM-B Announce with `stepsRemoved=0` | 68,995 |
| Primary BC (`020000fffe000001`) relaying GM-A with `stepsRemoved=1` | 55,944 |
| Primary BC relaying GM-B with `stepsRemoved=1` | 6,676 |
| Total primary-BC relayed Announce with `stepsRemoved=1` | 62,620 |

Some attack/replacement clocks legitimately produce additional tuples in their respective scenarios; the script prints all sender/grandmaster/value/count combinations so those are not silently discarded.

## Reproduce

From the repository root:

```powershell
python 04_WEB_SIMULATOR/ingest/audit_steps_removed.py 03_RECOVERY_LOOP_S-PLANE/results/recovery_eval_runs_r13-r17.tgz
```

This finding changes only the simulator's explanatory content and audit documentation.
