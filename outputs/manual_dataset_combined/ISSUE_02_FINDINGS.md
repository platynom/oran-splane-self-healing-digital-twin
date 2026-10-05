# Issue 2: duplicate Announce capture with conflicting labels

Result: both named sessions are one underlying capture and are quarantined from validated ground-truth and independent-sample use.

The audit script `issue02_announce_duplicate_audit.py` checks four PCAP aliases, the two raw CSV representations, and both label files without modifying sources. Its JSON output records file sizes, SHA-256 hashes, row counts, and exact comparisons.

The two session PCAP files are byte-identical, as are the matching upstream PCAP aliases. After the original PTP filter, both raw CSVs yield the same 46,998 packet rows. All non-label values in the two labelled files are identical, but 5,312 labels conflict.

The source and message-type pattern exactly describes session 2 (`Source=1`, `MessageType=11`, 9,787 positives). It does not reproduce session 1, which has 4,476 of those positive Announce records plus one Follow_Up record. These patterns were found by comparing saved annotations, so they are descriptions of the annotations, not independent evidence that either sender was an attacker.

For a beginner: an Announce packet is a normal PTP timing-control message. A capture tells us which packet was sent and when; it cannot by itself tell us whether the sender was authorised. That needs the experiment's attack-launch record or an auditable capture-specific labelling procedure.

Safe use: retain this capture once for provenance. Do not count it twice, split its aliases across train and test, or use either label column as validated ground truth. A capture-specific launch log plus the matching labelling-script revision would resolve the conflict.
