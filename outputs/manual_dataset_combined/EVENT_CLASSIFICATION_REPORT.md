# Event classification addendum

Versioned workbook: `ORAN_All_Current_Datasets_FINAL_PCAP_v2_CLASSIFIED.xlsx` SHA-256 `30f4c0e33e6ae86b91e667ca7be516382ea09fa9ac43b120c05c94fa99e959ee`.

The `Event classification` sheet contains 359,233 rows: one per packet in 14 canonical PCAP hashes, with no duplicate alias expansion. It contains only deterministic advertised-Announce observations. Supplied labels are not copied or inferred.

| Class / status | Count |
|---|---:|
| C0 / valid comparable Announce | 102,158 |
| C1 / valid comparable Announce | 0 |
| C2 / valid comparable Announce | 2 |
| C3 / valid comparable Announce | 3 |
| No previous observation | 22 |
| Not applicable | 257,048 |
| Unknown insufficient Announce | 0 |

State is separate per capture, transportSpecific, PTP version, domain and sourcePortIdentity. Invalid/truncated Announce messages do not advance state. `Classification guide` retains the class legend, tuple definition, origin/disposition and quarantine-aware counts.

Checks: C0-C3, first observation, non-PTP, malformed/truncated declared-length Announce, unsupported version, invalid-baseline preservation, and context boundaries in `test_event_classification.py`; serialization lockstep in `EVENT_CLASSIFICATION_SAVED_VERIFICATION.json`; independent all-capture raw-byte count comparison in `EVENT_CLASSIFICATION_INDEPENDENT_VERIFICATION.json`; all 68 prior worksheet parts are byte-identical; ZIP integrity and unique ZIP member names passed.

This is not a maliciousness, health/fault, receiver-selection, GNSS, recovery, or action classification.
