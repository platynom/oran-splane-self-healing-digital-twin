# Professor-facing evidence summary

## Example 1: why the first three production packets do not become telemetry

- **What:** The production PCAP begins with Delay_Req, Delay_Resp, and Announce packets, but derived timing telemetry begins with packet 4.
- **Which:** Packet indices 1–3 in `timesafe_prod_successful_announce_attack_ptp.pcap`; the read-only alignment trace records their message types and reason.
- **Where:** The PCAP-to-telemetry state machine needs a resolved Sync origin timestamp and capture-arrival timestamp before it can calculate offset.
- **When:** From capture start to 0.008973 seconds.
- **Why:** Offset calculation needs a master timestamp and a receiver/capture timestamp. The first three packets do not provide an already resolved pair.
- **How to verify:** Re-run `audit_production_packet_telemetry.py`. It reports 13,565 PTP packets, 13,562 emissions, and exactly these three no-emission records.

This supports an implementation explanation only. It does not mean the first three packets were lost, malicious, unhealthy, or recovered.

## Example 2: the production supplied positive-packet interval

- **What:** 200 of 13,565 supplied packet annotations are `Label=1`; all are Announce messages from one recorded sender and occur from 78.506815 to 105.308242 seconds.
- **Which:** `timesafe_prod_successful_announce_attack_labeled.csv`, linked row-for-row to the raw packet export by the completed alignment audit.
- **Where:** The fields are packet source address, PTP message type, sequence ID, length, and capture-relative time.
- **When:** The stated capture-relative interval only.
- **Why:** The observations describe what the publisher annotated. The provided local labeling script and attack-time file do not independently reproduce this capture’s annotations.
- **How to verify:** Compare the raw/encoded row fields and replay the supplied script as in `issue01_production_audit.py`.

The descriptive observation is compatible with an Announce takeover scenario, but alternatives include a stale labeling script, unavailable experiment records, or an authorised configuration change. It does not prove the sender was unauthorised, that the receiver clock was unhealthy, or that any recovery action occurred.

## Example 3: the duplicated Announce “sessions”

- **What:** Two files named Announce session 1 and session 2 contain the same 46,998 packet records but disagree on 5,312 labels.
- **Which:** Four PCAP aliases share one SHA-256; their two processed label files are aligned to corresponding raw CSV exports.
- **Where:** `timesafe_multi_raw` and the upstream `DataCollectionPTP` paths.
- **When:** The full shared capture, not two separate trials.
- **Why:** Byte-identical PCAP content is stronger evidence of one capture than filenames. Different labels therefore cannot create two independent experiments.
- **How to verify:** Re-run `issue02_announce_duplicate_audit.py`.

The defensible action is quarantine, not choosing whichever label set produces better model accuracy. No recovery is recorded or measured here.

## Bottom line

The project can honestly demonstrate a reproducible software pipeline, packet parsing, source auditing, and simulated self-healing decisions. It cannot yet claim validated physical O-RAN clock health, authenticated attacks, or effective real-world recovery from the available evidence.

## Current manual workbook and teaching guide

The corrected workbook now includes every original row/column from its 45-source manifest, with appended provenance, eligibility, situation interpretation and proposed-action columns. The source cells remain exact text to preserve precision. Unknown situations/actions remain unknown.

Use `PARAMETER_BY_PARAMETER_GUIDE.md` to work through all 113 original field names and the six questions. It separates parameter observations, calculations, defaults, labels, model reports and conditional action reasoning. The production packet lineage is now checked against the actual ingester through `verify_production_lineage.py` and its hash-bound sidecar, not just a mirrored implementation.
