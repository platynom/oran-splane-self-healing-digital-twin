# Issue 1: linking the production capture to its supplied labels

Date: 2026-09-07. Scope: the production capture only. Original datasets and the combined workbook were not modified.

**Result: packet alignment is verified; label correctness remains unresolved.**

## What was established

- All 13,565 raw packets have corresponding rows in the supplied labeled CSV.
- Sender and receiver address encoding, packet length, sequence ID, message type, and relative packet time match.
- Every full raw record is unique in this file. No row was dropped or duplicated by this alignment.
- The packaged label records equal the local upstream production label records.
- Existing labels contain 13,365 zeros and 200 ones. These are source annotations, not new conclusions.

The source timestamps are reported to microsecond precision. Comparing reconstructed times introduced only approximately 3.47e-18 seconds of floating-point difference, far below that precision. Alignment checks used a 1 ns numerical tolerance, not a network-health threshold.

## The unresolved evidence problem

The available `prodtest_dataset_gen.py` sets Label=1 when the sender is `b8:ce:f6:5e:6a:fa` and the timestamp appears in `announce_attack_only2.csv`. Applying this supplied rule produces zero positives, conflicting with all 200 saved positive labels. The unmodified upstream `label_data` function is also executed by the audit as a cross-check.

The saved positive labels correspond to sender `b8:ce:f6:5e:6b:4a`, not the address in that rule. All 200 are MessageType 11 (Announce), from 78.506815 to 105.308242 seconds. These observations describe the existing annotations; they do not establish which sender was authorized in that experiment.

Three local attack-only CSVs were checked for the saved positive timestamps; none shared those timestamps. The local Git clone is shallow, so it does not provide the full historical labeling trail. Attempts to read the public labeling file through the web tool were unsuccessful. This audit does not establish whether upstream history contains the missing matching version.

Possible explanations include a stale script, an attack-time file from another capture, or different preprocessing/labeling versions. None has been confirmed. Do not change sender addresses or time windows to force agreement.

## Why, when, where, how, what, and which

| Question | Explanation |
|---|---|
| What? | Connect the same packet across the raw and encoded files, and check the source of its label. |
| Which? | The production capture, its labeled CSV, the supplied labeling script, and its referenced attack-time CSV. Source hashes are in the verification JSON. |
| Where? | A recorded packet source address identifies its sender in the capture. It does not establish physical location or authorization by itself. |
| When? | Relative packet timestamps establish correspondence. The saved positive-label range is not independently verified attack start/stop time. |
| How? | Compare every row and field, reconstruct relative time, reproduce address encoding, and replay the original labeling rule. |
| Why? | We need to know that a label belongs to the packet and that the label has a reproducible experimental basis. These are separate checks. |

## Scientific basis and limits

The TIMESAFE paper explains using attack timing logs and machine addresses to label malicious packets. It also separates traffic during an attack from the network's recovery behavior. This supports checking logs and identity rather than declaring attacks solely from a high delay or a message type.

Source: [TIMESAFE, sections 6.2 and 8](https://arxiv.org/html/2412.13049v3).

No delay threshold, fault class, physical recovery, or classifier accuracy was established in this step. Label=0 is the existing non-malicious annotation; it does not prove the clock was healthy. MessageType=11 is a normal PTP message category and alone is not an attack diagnosis.

## Safe use of the result

`issue01_production_linked.jsonl` contains all original raw fields, the corresponding original labeled record, source row numbers, alignment status, and the reproduced-rule comparison. Its label status explicitly says scientific ground truth was not independently verified. This is an audit artifact, not a new training dataset.

To close the label-verification issue, obtain the capture-specific attack record and the matching labeling script/version, then reproduce the saved labels without adjusting the rule to fit them. Until then, retain the labels as supplied annotations and exclude this capture from claims that require independently validated ground truth. Other issues remain open and must be investigated separately.
