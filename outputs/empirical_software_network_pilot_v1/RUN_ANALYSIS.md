# Empirical Software Network Pilot — Run Analysis Report (v3)

## Executive Summary & Methodological Guidelines

- **Feasibility Evidence**: One run per condition is feasibility evidence, not a statistical comparison.
- **Repeatability Statement**: `n=3 characterises run-to-run spread in this environment and is not population-level performance.`
- **Netem Asymmetry**: `tc netem` impairs `bridge->slave` egress only; the slave's own `Delay_Req` egress is NOT impaired.
- **Servo Statistics**: `ptp4l` `rms`/`max`/`delay` lines are software-timestamp statistics on a shared host clock; NOT clock error. Baseline (rms 822557) is worse than netem (rms 784973), proving servo stats carry no timing signal.
- **Clock Identities**: Clock identities are regenerated per run and not compared across runs.
- **Label Policy**: No run is labelled healthy, attacked, faulty, or recovered.
- **Evidence Layers**: Tagged L1 (planned), L2 (confirmed injection), L3 (observed packet), L4 (observed receiver impact), L8 (measured outcome).

---

## Set 2 Repeatability Table (3 Repetitions per Condition)

### Condition: `baseline`
- **total_frames**: values=[2037, 2020, 2014] | min=2014 | median=2020 | max=2037 | spread=23
- **observed_missing_master_to_slave**: values=[0, 0, 0] | min=0 | median=0 | max=0 | spread=0
- **setup_epoch_offset_s**: values=[2.982, 2.982, 2.964] | min=2.964 | median=2.982 | max=2.982 | spread=0.018

### Condition: `netem`
- **total_frames**: values=[2045, 2058, 2013] | min=2013 | median=2045 | max=2058 | spread=45
- **observed_missing_master_to_slave**: values=[20, 19, 19] | min=19 | median=19 | max=20 | spread=1
- **setup_epoch_offset_s**: values=[2.978, 2.95, 2.982] | min=2.95 | median=2.978 | max=2.982 | spread=0.032
- **qdisc_after_sent_pkts**: values=[1693, 1697, 1674] | min=1674 | median=1693 | max=1697 | spread=23
- **qdisc_after_dropped_pkts**: values=[20, 20, 19] | min=19 | median=20 | max=20 | spread=1

### Condition: `control`
- **total_frames**: values=[2026, 2048, 2017] | min=2017 | median=2026 | max=2048 | spread=31
- **observed_missing_master_to_slave**: values=[0, 0, 0] | min=0 | median=0 | max=0 | spread=0
- **setup_epoch_offset_s**: values=[2.98, 2.97, 2.968] | min=2.968 | median=2.97 | max=2.98 | spread=0.012

### Condition: `intervention`
- **total_frames**: values=[3114, 3244, 3130] | min=3114 | median=3130 | max=3244 | spread=130
- **observed_missing_master_to_slave**: values=[0, 0, 0] | min=0 | median=0 | max=0 | spread=0
- **setup_epoch_offset_s**: values=[3.0, 2.974, 2.982] | min=2.974 | median=2.982 | max=3.0 | spread=0.026
- **delay_req_outage_s**: values=[0.486946, 0.466648, 0.656833] | min=0.466648 | median=0.486946 | max=0.656833 | spread=0.190185
- **announce_loss_to_resumption_s**: values=[1.292393, 1.336006, 1.298468] | min=1.292393 | median=1.298468 | max=1.336006 | spread=0.043613

---

## Detailed Evaluated Runs

### Run `b2` — baseline_control (20260910_calibrated_baseline)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 899
- **Message Breakdown (L3)**: {'Announce': 114, 'Sync': 223, 'Follow_Up': 223, 'Delay_Req': 113, 'Delay_Resp': 226}

#### Announce Analysis by Source (L3)
- **Source MAC**: `12:ff:7a:10:5f:a2`
  - Count: 57
  - First / Last Capture Time (s): 1789017820.590434 / 1789017834.60008
  - Inter-arrival Stats (s): {'min': 0.249999, 'median': 0.250107, 'p95': 0.250427, 'max': 0.251314}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '12ff7afffe105fa2', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `be:99:22:e1:19:0f`
  - Count: 57
  - First / Last Capture Time (s): 1789017820.623122 / 1789017834.631303
  - Inter-arrival Stats (s): {'min': 0.250012, 'median': 0.25009, 'p95': 0.25045, 'max': 0.250648}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'be9922fffee1190f', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `12:ff:7a:10:5f:a2`
  - `Announce`: n=57/57 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=113/113 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=112/112 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=112/112 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `be:99:22:e1:19:0f`
  - `Announce`: n=57/57 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=113/113 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=111/111 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=111/111 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `d2:81:9d:54:92:68`
  - `Delay_Req`: n=113/113 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.962 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `None`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `n2` — netem_delay_jitter_loss (20260910_calibrated_netem)
- **Status**: `UNVERIFIED - qdisc counters were sampled before the traffic window; the impairment was neither confirmed delivered nor shown absent`
- **Note**: Excluded from comparison per audit requirements.

### Run `c2` — authorized_source_change_no_action_control (20260910_calibrated_source_control)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 904
- **Message Breakdown (L3)**: {'Announce': 114, 'Sync': 224, 'Follow_Up': 224, 'Delay_Req': 114, 'Delay_Resp': 228}

#### Announce Analysis by Source (L3)
- **Source MAC**: `c2:22:4c:88:8b:b6`
  - Count: 57
  - First / Last Capture Time (s): 1789017882.544237 / 1789017896.557195
  - Inter-arrival Stats (s): {'min': 0.250029, 'median': 0.250175, 'p95': 0.250514, 'max': 0.252387}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'c2224cfffe888bb6', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `f2:88:62:5f:31:b7`
  - Count: 57
  - First / Last Capture Time (s): 1789017882.586261 / 1789017896.593465
  - Inter-arrival Stats (s): {'min': 0.249997, 'median': 0.250097, 'p95': 0.250329, 'max': 0.250432}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'f28862fffe5f31b7', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `12:ed:06:b0:b7:c6`
  - `Delay_Req`: n=114/114 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `c2:22:4c:88:8b:b6`
  - `Announce`: n=57/57 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=114/114 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=112/112 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=112/112 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `f2:88:62:5f:31:b7`
  - `Announce`: n=57/57 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=114/114 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=112/112 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=112/112 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.96 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `None`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `s4` — authorized_source_change_intervention (20260910_calibrated_source_stop_retry2)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 1334
- **Message Breakdown (L3)**: {'Announce': 162, 'Sync': 320, 'Follow_Up': 320, 'Delay_Req': 210, 'Delay_Resp': 322}

#### Announce Analysis by Source (L3)
- **Source MAC**: `1a:93:5b:fa:92:e7`
  - Count: 105
  - First / Last Capture Time (s): 1789017951.258213 / 1789017977.277034
  - Inter-arrival Stats (s): {'min': 0.249999, 'median': 0.250131, 'p95': 0.250347, 'max': 0.252134}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '1a935bfffefa92e7', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `9a:bf:c1:88:6a:15`
  - Count: 57
  - First / Last Capture Time (s): 1789017951.17102 / 1789017965.179574
  - Inter-arrival Stats (s): {'min': 0.250028, 'median': 0.250123, 'p95': 0.250347, 'max': 0.25043}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '9abfc1fffe886a15', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `1a:93:5b:fa:92:e7`
  - `Announce`: n=105/105 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=210/210 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=207/207 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=207/207 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `9a:bf:c1:88:6a:15`
  - `Announce`: n=57/57 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=112/112 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=113/113 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=113/113 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `d6:89:20:36:04:82`
  - `Delay_Req`: n=210/210 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **t_last_delay_req_before_gap_epoch_s**: 1789017966.042396
- **t_first_delay_req_after_gap_epoch_s**: 1789017966.361461
- **t_last_announce_from_stopped_source_epoch_s**: 1789017965.179574
- **median_delay_req_interval_s**: 0.118531
- **count_of_gaps_exceeding_5x_median**: 0
- **delay_req_outage_s (L4)**: 0.319066 s
- **announce_loss_to_resumption_s (L4)**: 1.181887 s
- **Protocol Detection Floor (L1)**: 0.75 s (`announceReceiptTimeout * 2**logAnnounceInterval`)
- **Statement**: This is a packet-observable outage and resumption. It is NOT the receiver's internal BMCA reselection latency, which the slave log shows as a 2 ms transition and which cannot be measured in the pcap timebase. The mechanism producing the outage duration is not established.
- **Floor Constraint**: The measured announce_loss_to_resumption_s cannot fall below the 0.75 s protocol detection floor.

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.988 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[427.826]: rms 50514 max 140272 freq  +7958 +/- 21040 delay 12475 +/- 1868`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `n3` — netem_delay_jitter_loss (20260911_calibrated_netem_v3)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2020
- **Message Breakdown (L3)**: {'Announce': 255, 'Sync': 505, 'Follow_Up': 505, 'Delay_Req': 254, 'Delay_Resp': 501}

#### Announce Analysis by Source (L3)
- **Source MAC**: `2e:6d:b3:62:cd:83`
  - Count: 127
  - First / Last Capture Time (s): 1789136640.27989 / 1789136672.300884
  - Inter-arrival Stats (s): {'min': 0.249257, 'median': 0.250107, 'p95': 0.250762, 'max': 0.500502}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '2e6db3fffe62cd83', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `ca:80:77:6d:11:8b`
  - Count: 128
  - First / Last Capture Time (s): 1789136640.446975 / 1789136672.219092
  - Inter-arrival Stats (s): {'min': 0.249355, 'median': 0.250158, 'p95': 0.250785, 'max': 0.251038}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'ca8077fffe6d118b', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `2e:6d:b3:62:cd:83`
  - `Announce`: n=127/129 | missing=2 (`missing_fraction`: 0.015504)
  - `Delay_Resp`: n=250/254 | missing=4 (`missing_fraction`: 0.015748)
  - `Follow_Up`: n=254/257 | missing=3 (`missing_fraction`: 0.011673)
  - `Sync`: n=255/257 | missing=2 (`missing_fraction`: 0.007782)
- **Source MAC**: `72:d6:cf:be:42:39`
  - `Delay_Req`: n=254/254 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `ca:80:77:6d:11:8b`
  - `Announce`: n=128/128 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=251/254 | missing=3 (`missing_fraction`: 0.011811)
  - `Follow_Up`: n=251/255 | missing=4 (`missing_fraction`: 0.015686)
  - `Sync`: n=250/254 | missing=4 (`missing_fraction`: 0.015748)
- **Total Master->Slave Missing (L3)**: 22
- **Total Slave->Bridge Missing (L3)**: 0

#### Netem Loss Triangulation & Frame Accounting (L1 / L2 / L3)
- **Configured Loss Fraction (L1)**: 0.01 (1%)
- **Qdisc Counters (L2)**: Sent=1671, Dropped=23
- **Missing Master->Slave (L3)**: 22
- **Missing Slave->Bridge (L3)**: 0
- **Direction Match**: `True`
- **Statement**: The impairment was applied to the bridge->slave egress only. Missing sequence IDs appear only in that direction and none in the reverse direction. This is a direction-matched consistency between a confirmed injection and an observed packet event. It is not proof of receiver timing impact.
- **Frame Reconciliation**: Captured M->S=1766, Qdisc Accounted=1694, Unaccounted=72
- **Frame Explanation**: The 72 frames were captured between tcpdump start and the netem_command_confirmed event, and were not subject to the impairment.

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.984 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[23.022]: rms 784973 max 1260371 freq +73104 +/- 268924 delay 486029 +/- 191236`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `b31` — baseline_control (20260911_set2_baseline_r1)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2037
- **Message Breakdown (L3)**: {'Announce': 258, 'Sync': 513, 'Follow_Up': 513, 'Delay_Req': 251, 'Delay_Resp': 502}

#### Announce Analysis by Source (L3)
- **Source MAC**: `32:0c:2a:af:ff:5e`
  - Count: 129
  - First / Last Capture Time (s): 1789137633.034369 / 1789137665.050369
  - Inter-arrival Stats (s): {'min': 0.249833, 'median': 0.25008, 'p95': 0.250356, 'max': 0.250971}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '320c2afffeafff5e', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `f6:c6:a6:c1:5d:12`
  - Count: 129
  - First / Last Capture Time (s): 1789137633.18188 / 1789137665.197846
  - Inter-arrival Stats (s): {'min': 0.249979, 'median': 0.250088, 'p95': 0.250339, 'max': 0.250424}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'f6c6a6fffec15d12', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `32:0c:2a:af:ff:5e`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=251/251 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=257/257 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=257/257 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `e2:fb:fb:d4:ad:e5`
  - `Delay_Req`: n=251/251 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `f6:c6:a6:c1:5d:12`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=251/251 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.982 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[22.725]: rms 7425 max 15747 freq   +512 +/- 4414 delay 13512 +/- 2770`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `n41` — netem_delay_jitter_loss (20260911_set2_netem_r1)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2045
- **Message Breakdown (L3)**: {'Announce': 253, 'Sync': 502, 'Follow_Up': 508, 'Delay_Req': 262, 'Delay_Resp': 520}

#### Announce Analysis by Source (L3)
- **Source MAC**: `9a:78:7f:96:69:f2`
  - Count: 126
  - First / Last Capture Time (s): 1789137667.341407 / 1789137699.10611
  - Inter-arrival Stats (s): {'min': 0.249323, 'median': 0.250098, 'p95': 0.250634, 'max': 0.500414}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '9a787ffffe9669f2', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `fe:37:c9:ae:61:ac`
  - Count: 127
  - First / Last Capture Time (s): 1789137667.277708 / 1789137699.293957
  - Inter-arrival Stats (s): {'min': 0.249108, 'median': 0.250104, 'p95': 0.250661, 'max': 0.500061}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'fe37c9fffeae61ac', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `82:95:b5:99:bc:8a`
  - `Delay_Req`: n=262/262 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `9a:78:7f:96:69:f2`
  - `Announce`: n=126/128 | missing=2 (`missing_fraction`: 0.015625)
  - `Delay_Resp`: n=261/262 | missing=1 (`missing_fraction`: 0.003817)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=250/255 | missing=5 (`missing_fraction`: 0.019608)
- **Source MAC**: `fe:37:c9:ae:61:ac`
  - `Announce`: n=127/129 | missing=2 (`missing_fraction`: 0.015504)
  - `Delay_Resp`: n=259/262 | missing=3 (`missing_fraction`: 0.01145)
  - `Follow_Up`: n=253/256 | missing=3 (`missing_fraction`: 0.011719)
  - `Sync`: n=252/256 | missing=4 (`missing_fraction`: 0.015625)
- **Total Master->Slave Missing (L3)**: 20
- **Total Slave->Bridge Missing (L3)**: 0

#### Netem Loss Triangulation & Frame Accounting (L1 / L2 / L3)
- **Configured Loss Fraction (L1)**: 0.01 (1%)
- **Qdisc Counters (L2)**: Sent=1693, Dropped=20
- **Missing Master->Slave (L3)**: 20
- **Missing Slave->Bridge (L3)**: 0
- **Direction Match**: `True`
- **Statement**: The impairment was applied to the bridge->slave egress only. Missing sequence IDs appear only in that direction and none in the reverse direction. This is a direction-matched consistency between a confirmed injection and an observed packet event. It is not proof of receiver timing impact.
- **Frame Reconciliation**: Captured M->S=1783, Qdisc Accounted=1713, Unaccounted=70
- **Frame Explanation**: The 70 frames were captured between tcpdump start and the netem_command_confirmed event, and were not subject to the impairment.

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.978 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[57.159]: rms 601947 max 794529 freq +68109 +/- 169965 delay 464686 +/- 170741`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `c31` — authorized_source_change_no_action_control (20260911_set2_control_r1)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2026
- **Message Breakdown (L3)**: {'Announce': 257, 'Sync': 511, 'Follow_Up': 511, 'Delay_Req': 249, 'Delay_Resp': 498}

#### Announce Analysis by Source (L3)
- **Source MAC**: `7e:76:e5:0a:6a:6f`
  - Count: 128
  - First / Last Capture Time (s): 1789137701.244357 / 1789137733.012638
  - Inter-arrival Stats (s): {'min': 0.249995, 'median': 0.250099, 'p95': 0.250365, 'max': 0.250684}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '7e76e5fffe0a6a6f', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `be:64:15:d2:0c:c1`
  - Count: 129
  - First / Last Capture Time (s): 1789137701.075353 / 1789137733.093056
  - Inter-arrival Stats (s): {'min': 0.250005, 'median': 0.25011, 'p95': 0.250337, 'max': 0.250449}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'be6415fffed20cc1', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `7e:76:e5:0a:6a:6f`
  - `Announce`: n=128/128 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=249/249 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `ae:29:a8:33:bc:95`
  - `Delay_Req`: n=249/249 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `be:64:15:d2:0c:c1`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=249/249 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.98 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[90.687]: rms 9933 max 24202 freq   -275 +/- 7407 delay 13162 +/- 2687`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `s51` — authorized_source_change_intervention (20260911_set2_intervention_r1)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 3114
- **Message Breakdown (L3)**: {'Announce': 377, 'Sync': 752, 'Follow_Up': 752, 'Delay_Req': 496, 'Delay_Resp': 737}

#### Announce Analysis by Source (L3)
- **Source MAC**: `82:b1:c4:0a:2d:a0`
  - Count: 128
  - First / Last Capture Time (s): 1789137735.057176 / 1789137766.821252
  - Inter-arrival Stats (s): {'min': 0.249804, 'median': 0.250077, 'p95': 0.25031, 'max': 0.250351}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '82b1c4fffe0a2da0', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `fe:ac:bc:30:a6:95`
  - Count: 249
  - First / Last Capture Time (s): 1789137734.77126 / 1789137796.80095
  - Inter-arrival Stats (s): {'min': 0.249986, 'median': 0.250091, 'p95': 0.250305, 'max': 0.25044}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'feacbcfffe30a695', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `82:b1:c4:0a:2d:a0`
  - `Announce`: n=128/128 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=241/241 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `f2:6e:c9:38:27:93`
  - `Delay_Req`: n=496/496 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `fe:ac:bc:30:a6:95`
  - `Announce`: n=249/249 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=496/496 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=497/497 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=497/497 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **t_last_delay_req_before_gap_epoch_s**: 1789137767.626699
- **t_first_delay_req_after_gap_epoch_s**: 1789137768.113646
- **t_last_announce_from_stopped_source_epoch_s**: 1789137766.821252
- **median_delay_req_interval_s**: 0.123321
- **count_of_gaps_exceeding_5x_median**: 0
- **delay_req_outage_s (L4)**: 0.486946 s
- **announce_loss_to_resumption_s (L4)**: 1.292393 s
- **Protocol Detection Floor (L1)**: 0.75 s (`announceReceiptTimeout * 2**logAnnounceInterval`)
- **Statement**: This is a packet-observable outage and resumption. It is NOT the receiver's internal BMCA reselection latency, which the slave log shows as a 2 ms transition and which cannot be measured in the pcap timebase. The mechanism producing the outage duration is not established.
- **Floor Constraint**: The measured announce_loss_to_resumption_s cannot fall below the 0.75 s protocol detection floor.

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 3.0 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[158.873]: rms 6412 max 13598 freq   -100 +/- 4973 delay 14884 +/- 2768`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `b32` — baseline_control (20260911_set2_baseline_r2)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2020
- **Message Breakdown (L3)**: {'Announce': 256, 'Sync': 510, 'Follow_Up': 510, 'Delay_Req': 248, 'Delay_Resp': 496}

#### Announce Analysis by Source (L3)
- **Source MAC**: `22:04:70:8e:cb:c8`
  - Count: 128
  - First / Last Capture Time (s): 1789137798.775206 / 1789137830.540378
  - Inter-arrival Stats (s): {'min': 0.250004, 'median': 0.250075, 'p95': 0.250343, 'max': 0.250589}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '220470fffe8ecbc8', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `aa:33:4a:67:e1:e2`
  - Count: 128
  - First / Last Capture Time (s): 1789137798.814079 / 1789137830.577734
  - Inter-arrival Stats (s): {'min': 0.249999, 'median': 0.250079, 'p95': 0.250279, 'max': 0.250517}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'aa334afffe67e1e2', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `22:04:70:8e:cb:c8`
  - `Announce`: n=128/128 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=248/248 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `aa:33:4a:67:e1:e2`
  - `Announce`: n=128/128 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=248/248 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `da:10:fb:9f:3d:31`
  - `Delay_Req`: n=248/248 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.982 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[188.255]: rms 7239 max 17300 freq  +2066 +/- 5340 delay 12698 +/- 2726`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `n42` — netem_delay_jitter_loss (20260911_set2_netem_r2)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2058
- **Message Breakdown (L3)**: {'Announce': 257, 'Sync': 504, 'Follow_Up': 509, 'Delay_Req': 265, 'Delay_Resp': 523}

#### Announce Analysis by Source (L3)
- **Source MAC**: `ba:90:c3:32:13:e0`
  - Count: 129
  - First / Last Capture Time (s): 1789137832.507669 / 1789137864.524434
  - Inter-arrival Stats (s): {'min': 0.249061, 'median': 0.250113, 'p95': 0.250612, 'max': 0.251441}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'ba90c3fffe3213e0', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `fe:97:14:87:59:4b`
  - Count: 128
  - First / Last Capture Time (s): 1789137832.33064 / 1789137864.345578
  - Inter-arrival Stats (s): {'min': 0.249229, 'median': 0.250095, 'p95': 0.250657, 'max': 0.500715}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'fe9714fffe87594b', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `7e:cd:23:9d:2e:3c`
  - `Delay_Req`: n=265/265 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `ba:90:c3:32:13:e0`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=259/265 | missing=6 (`missing_fraction`: 0.022642)
  - `Follow_Up`: n=253/255 | missing=2 (`missing_fraction`: 0.007843)
  - `Sync`: n=251/255 | missing=4 (`missing_fraction`: 0.015686)
- **Source MAC**: `fe:97:14:87:59:4b`
  - `Announce`: n=128/129 | missing=1 (`missing_fraction`: 0.007752)
  - `Delay_Resp`: n=264/265 | missing=1 (`missing_fraction`: 0.003774)
  - `Follow_Up`: n=256/257 | missing=1 (`missing_fraction`: 0.003891)
  - `Sync`: n=253/257 | missing=4 (`missing_fraction`: 0.015564)
- **Total Master->Slave Missing (L3)**: 19
- **Total Slave->Bridge Missing (L3)**: 0

#### Netem Loss Triangulation & Frame Accounting (L1 / L2 / L3)
- **Configured Loss Fraction (L1)**: 0.01 (1%)
- **Qdisc Counters (L2)**: Sent=1697, Dropped=20
- **Missing Master->Slave (L3)**: 19
- **Missing Slave->Bridge (L3)**: 0
- **Direction Match**: `True`
- **Statement**: The impairment was applied to the bridge->slave egress only. Missing sequence IDs appear only in that direction and none in the reverse direction. This is a direction-matched consistency between a confirmed injection and an observed packet event. It is not proof of receiver timing impact.
- **Frame Reconciliation**: Captured M->S=1793, Qdisc Accounted=1717, Unaccounted=76
- **Frame Explanation**: The 76 frames were captured between tcpdump start and the netem_command_confirmed event, and were not subject to the impairment.

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.95 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[222.573]: rms 648693 max 829891 freq +79477 +/- 245422 delay 500751 +/- 177176`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `c32` — authorized_source_change_no_action_control (20260911_set2_control_r2)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2048
- **Message Breakdown (L3)**: {'Announce': 258, 'Sync': 511, 'Follow_Up': 511, 'Delay_Req': 256, 'Delay_Resp': 512}

#### Announce Analysis by Source (L3)
- **Source MAC**: `e2:47:9f:77:b3:f1`
  - Count: 129
  - First / Last Capture Time (s): 1789137866.255447 / 1789137898.275358
  - Inter-arrival Stats (s): {'min': 0.249985, 'median': 0.250106, 'p95': 0.250369, 'max': 0.250444}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'e2479ffffe77b3f1', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `e2:90:00:06:07:c4`
  - Count: 129
  - First / Last Capture Time (s): 1789137866.156032 / 1789137898.17694
  - Inter-arrival Stats (s): {'min': 0.249989, 'median': 0.250118, 'p95': 0.250397, 'max': 0.250483}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'e29000fffe0607c4', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `66:f5:42:00:69:65`
  - `Delay_Req`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `e2:47:9f:77:b3:f1`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `e2:90:00:06:07:c4`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.97 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[255.600]: rms 10229 max 19774 freq     +6 +/- 6598 delay 16205 +/- 3574`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `s52` — authorized_source_change_intervention (20260911_set2_intervention_r2)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 3244
- **Message Breakdown (L3)**: {'Announce': 377, 'Sync': 750, 'Follow_Up': 750, 'Delay_Req': 535, 'Delay_Resp': 832}

#### Announce Analysis by Source (L3)
- **Source MAC**: `56:9a:19:35:52:ef`
  - Count: 249
  - First / Last Capture Time (s): 1789137899.971277 / 1789137962.011615
  - Inter-arrival Stats (s): {'min': 0.249993, 'median': 0.250104, 'p95': 0.250395, 'max': 0.250813}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '569a19fffe3552ef', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `de:8d:9c:19:b8:13`
  - Count: 128
  - First / Last Capture Time (s): 1789137900.071709 / 1789137931.839991
  - Inter-arrival Stats (s): {'min': 0.250007, 'median': 0.25009, 'p95': 0.250405, 'max': 0.250623}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'de8d9cfffe19b813', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `56:9a:19:35:52:ef`
  - `Announce`: n=249/249 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=535/535 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=495/495 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=495/495 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `ae:98:ac:42:90:ad`
  - `Delay_Req`: n=535/535 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `de:8d:9c:19:b8:13`
  - `Announce`: n=128/128 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=297/297 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **t_last_delay_req_before_gap_epoch_s**: 1789137932.709348
- **t_first_delay_req_after_gap_epoch_s**: 1789137933.175997
- **t_last_announce_from_stopped_source_epoch_s**: 1789137931.839991
- **median_delay_req_interval_s**: 0.113304
- **count_of_gaps_exceeding_5x_median**: 0
- **delay_req_outage_s (L4)**: 0.466648 s
- **announce_loss_to_resumption_s (L4)**: 1.336006 s
- **Protocol Detection Floor (L1)**: 0.75 s (`announceReceiptTimeout * 2**logAnnounceInterval`)
- **Statement**: This is a packet-observable outage and resumption. It is NOT the receiver's internal BMCA reselection latency, which the slave log shows as a 2 ms transition and which cannot be measured in the pcap timebase. The mechanism producing the outage duration is not established.
- **Floor Constraint**: The measured announce_loss_to_resumption_s cannot fall below the 0.75 s protocol detection floor.

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.974 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[323.833]: rms 2776 max 5425 freq    -14 +/- 4382 delay 15939 +/- 4836`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `b33` — baseline_control (20260911_set2_baseline_r3)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2014
- **Message Breakdown (L3)**: {'Announce': 258, 'Sync': 512, 'Follow_Up': 512, 'Delay_Req': 244, 'Delay_Resp': 488}

#### Announce Analysis by Source (L3)
- **Source MAC**: `0e:b6:74:00:b3:fb`
  - Count: 129
  - First / Last Capture Time (s): 1789137963.681099 / 1789137995.699092
  - Inter-arrival Stats (s): {'min': 0.249976, 'median': 0.250097, 'p95': 0.250335, 'max': 0.250484}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '0eb674fffe00b3fb', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `fe:83:29:92:9b:56`
  - Count: 129
  - First / Last Capture Time (s): 1789137963.672185 / 1789137995.690694
  - Inter-arrival Stats (s): {'min': 0.249994, 'median': 0.250098, 'p95': 0.250388, 'max': 0.250683}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'fe8329fffe929b56', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `0e:b6:74:00:b3:fb`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=244/244 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `3a:9c:72:74:e1:0b`
  - `Delay_Req`: n=244/244 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `fe:83:29:92:9b:56`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=244/244 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.964 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[353.115]: rms 5859 max 14326 freq  +1055 +/- 2761 delay 13458 +/- 2052`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `n43` — netem_delay_jitter_loss (20260911_set2_netem_r3)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2013
- **Message Breakdown (L3)**: {'Announce': 250, 'Sync': 505, 'Follow_Up': 505, 'Delay_Req': 252, 'Delay_Resp': 501}

#### Announce Analysis by Source (L3)
- **Source MAC**: `42:44:ca:21:eb:f6`
  - Count: 125
  - First / Last Capture Time (s): 1789137997.59288 / 1789138029.358952
  - Inter-arrival Stats (s): {'min': 0.249466, 'median': 0.250154, 'p95': 0.250777, 'max': 0.499999}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '4244cafffe21ebf6', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `92:66:92:c8:61:49`
  - Count: 125
  - First / Last Capture Time (s): 1789137997.612705 / 1789138029.379133
  - Inter-arrival Stats (s): {'min': 0.249364, 'median': 0.250117, 'p95': 0.250776, 'max': 0.50058}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '926692fffec86149', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `2e:d7:3c:27:eb:cc`
  - `Delay_Req`: n=252/252 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `42:44:ca:21:eb:f6`
  - `Announce`: n=125/128 | missing=3 (`missing_fraction`: 0.023438)
  - `Delay_Resp`: n=250/252 | missing=2 (`missing_fraction`: 0.007937)
  - `Follow_Up`: n=253/255 | missing=2 (`missing_fraction`: 0.007843)
  - `Sync`: n=251/255 | missing=4 (`missing_fraction`: 0.015686)
- **Source MAC**: `92:66:92:c8:61:49`
  - `Announce`: n=125/128 | missing=3 (`missing_fraction`: 0.023438)
  - `Delay_Resp`: n=251/252 | missing=1 (`missing_fraction`: 0.003968)
  - `Follow_Up`: n=252/255 | missing=3 (`missing_fraction`: 0.011765)
  - `Sync`: n=254/255 | missing=1 (`missing_fraction`: 0.003922)
- **Total Master->Slave Missing (L3)**: 19
- **Total Slave->Bridge Missing (L3)**: 0

#### Netem Loss Triangulation & Frame Accounting (L1 / L2 / L3)
- **Configured Loss Fraction (L1)**: 0.01 (1%)
- **Qdisc Counters (L2)**: Sent=1674, Dropped=19
- **Missing Master->Slave (L3)**: 19
- **Missing Slave->Bridge (L3)**: 0
- **Direction Match**: `True`
- **Statement**: The impairment was applied to the bridge->slave egress only. Missing sequence IDs appear only in that direction and none in the reverse direction. This is a direction-matched consistency between a confirmed injection and an observed packet event. It is not proof of receiver timing impact.
- **Frame Reconciliation**: Captured M->S=1761, Qdisc Accounted=1693, Unaccounted=68
- **Frame Explanation**: The 68 frames were captured between tcpdump start and the netem_command_confirmed event, and were not subject to the impairment.

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.982 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[387.307]: rms 606588 max 1015162 freq +70015 +/- 210823 delay 480645 +/- 180642`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `c33` — authorized_source_change_no_action_control (20260911_set2_control_r3)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 2017
- **Message Breakdown (L3)**: {'Announce': 257, 'Sync': 511, 'Follow_Up': 511, 'Delay_Req': 246, 'Delay_Resp': 492}

#### Announce Analysis by Source (L3)
- **Source MAC**: `36:ea:bd:6a:d9:de`
  - Count: 128
  - First / Last Capture Time (s): 1789138031.415837 / 1789138063.182636
  - Inter-arrival Stats (s): {'min': 0.249944, 'median': 0.250084, 'p95': 0.250382, 'max': 0.250472}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '36eabdfffe6ad9de', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `76:43:cb:32:ee:89`
  - Count: 129
  - First / Last Capture Time (s): 1789138031.312306 / 1789138063.327487
  - Inter-arrival Stats (s): {'min': 0.249991, 'median': 0.250071, 'p95': 0.25037, 'max': 0.250477}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '7643cbfffe32ee89', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `36:ea:bd:6a:d9:de`
  - `Announce`: n=128/128 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=246/246 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=255/255 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `76:43:cb:32:ee:89`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=246/246 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `d6:e9:8e:28:ca:82`
  - `Delay_Req`: n=246/246 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **Outage / Resumption**: `null` (Reason: None)
- **Protocol Detection Floor (L1)**: 0.75 s

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.968 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[421.109]: rms 4979 max 11274 freq   -231 +/- 1500 delay 14074 +/- 3189`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---

### Run `s53` — authorized_source_change_intervention (20260911_set2_intervention_r3)
- **Status**: `VERIFIED`
- **Total PTP Packets (L3)**: 3130
- **Message Breakdown (L3)**: {'Announce': 378, 'Sync': 752, 'Follow_Up': 752, 'Delay_Req': 496, 'Delay_Resp': 752}

#### Announce Analysis by Source (L3)
- **Source MAC**: `0a:85:7c:7b:91:a8`
  - Count: 129
  - First / Last Capture Time (s): 1789138065.219373 / 1789138097.23169
  - Inter-arrival Stats (s): {'min': 0.249694, 'median': 0.250083, 'p95': 0.250262, 'max': 0.250493}
  - Attributes: {'priority1': 100, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': '0a857cfffe7b91a8', 'stepsRemoved': 0, 'timeSource': 160}
- **Source MAC**: `c2:c3:34:96:02:5a`
  - Count: 249
  - First / Last Capture Time (s): 1789138065.10201 / 1789138127.133231
  - Inter-arrival Stats (s): {'min': 0.249979, 'median': 0.250078, 'p95': 0.250365, 'max': 0.250609}
  - Attributes: {'priority1': 150, 'clockClass': 248, 'clockAccuracy': 254, 'priority2': 128, 'grandmasterIdentity': 'c2c334fffe96025a', 'stepsRemoved': 0, 'timeSource': 160}

#### Per-Source Sequence Gap Analysis (L3)
- **Source MAC**: `0a:85:7c:7b:91:a8`
  - `Announce`: n=129/129 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=256/256 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `c2:c3:34:96:02:5a`
  - `Announce`: n=249/249 | missing=0 (`missing_fraction`: 0.0)
  - `Delay_Resp`: n=496/496 | missing=0 (`missing_fraction`: 0.0)
  - `Follow_Up`: n=496/496 | missing=0 (`missing_fraction`: 0.0)
  - `Sync`: n=496/496 | missing=0 (`missing_fraction`: 0.0)
- **Source MAC**: `ea:11:50:2e:05:01`
  - `Delay_Req`: n=496/496 | missing=0 (`missing_fraction`: 0.0)
- **Total Master->Slave Missing (L3)**: 0
- **Total Slave->Bridge Missing (L3)**: 0

#### Source Change & Resumption Measurement (L4 / L1)
- **t_last_delay_req_before_gap_epoch_s**: 1789138097.873325
- **t_first_delay_req_after_gap_epoch_s**: 1789138098.530158
- **t_last_announce_from_stopped_source_epoch_s**: 1789138097.23169
- **median_delay_req_interval_s**: 0.115856
- **count_of_gaps_exceeding_5x_median**: 1
- **delay_req_outage_s (L4)**: 0.656833 s
- **announce_loss_to_resumption_s (L4)**: 1.298468 s
- **Protocol Detection Floor (L1)**: 0.75 s (`announceReceiptTimeout * 2**logAnnounceInterval`)
- **Statement**: This is a packet-observable outage and resumption. It is NOT the receiver's internal BMCA reselection latency, which the slave log shows as a 2 ms transition and which cannot be measured in the pcap timebase. The mechanism producing the outage duration is not established.
- **Floor Constraint**: The measured announce_loss_to_resumption_s cannot fall below the 0.75 s protocol detection floor.

#### Setup Epoch Offset Observation
- **Observed Setup Offset**: 2.982 s (`events.log` `monotonic_s` minus `ptp4l` log start time)
- **Note**: not usable for latency arithmetic

#### Software Timestamp Servo Statistic (L4)
- **Raw Log Stat**: `ptp4l[489.199]: rms 25756 max 71950 freq   +167 +/- 17780 delay 12898 +/- 2212`
- **Label**: `software-timestamp statistic on a shared host clock; NOT clock error`

---
