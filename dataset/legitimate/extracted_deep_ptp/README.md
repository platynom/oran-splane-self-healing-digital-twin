# extracted_deep_ptp/ — full-surface PTP extraction from the legitimate captures

Produced by `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/tools/ptp_deep_extract.py`
directly from the raw bytes of the pcaps in `dataset/legitimate/`.

**350,794 PTP packets · 56 columns · 14 unique captures.**

## Integrity contract (verified, not asserted)

* Every column is parsed from actual packet bytes.
* A field absent for a given message type is left **EMPTY**, never filled with a placeholder
  constant. Verified: `gm_clock_class`, `gm_priority2`, `steps_removed`, `current_utc_offset`
  are populated in 81,969/81,969 Announce rows and 0/114,574 Sync rows — absent by protocol.
* Fields that a PASSIVE capture cannot recover (the slave's own t2/t3 timestamps) are **not
  emitted at all** rather than approximated. Only t1 (`origin_ts_ns` on Sync/Follow_Up) and
  t4 (`origin_ts_ns` on Delay_Resp) are genuinely on the wire.

This is the fix for integrity findings #3 and #4: the previous derived CSVs padded missing
sensors with constants; these do not.

## What is new here (was not collected before)

L0 full header — all 12 `flag_*` bits, `correction_ns`, `domain_number`, `major/minor_sdo_id`,
`log_message_interval`, `source_clock_identity`, `source_port_number`, `control_field`.
L1 — `gm_clock_accuracy`, `gm_offset_scaled_log_variance`, `time_source`, `tlv_types`,
`has_path_trace`, `gm_identity_equals_source`.
L2 — `current_utc_offset`, leap/traceability bits.
L9 — `eth_src`, `eth_dst`, `vlan_id`, `vlan_pcp`.
Legality (computed against ITU-T G.8275.1 / IEEE 1588-2019, not invented):
`g87251_domain_ok`, `g87251_mcast_ok`, `g87251_priority1_ok`, `g87251_log_sync_ok`,
`g87251_log_announce_ok`, `g87251_log_delayreq_ok`, `clock_class_legal`,
`bmca_fields_all_zero`.

## Deduplication

21 pcaps on disk are only **14 unique files** (`_unique_sources.json` maps md5 -> path).
`announce_session_1.pcap`, `announce_session_2.pcap` and `2024-10-06-announce_attack_UEdata.pcap`
are all byte-identical to `15min_announce_attack.pcap` (md5 `5c6fd791a0...`). Treating them as
separate sessions breaks session-disjoint evaluation.

## Known limitation

`origin_ts_ns` gives t1 and t4 only. True offset and directional path asymmetry are NOT
recoverable from a passive capture and are deliberately absent. They require live `pmc`
telemetry from the slave.
