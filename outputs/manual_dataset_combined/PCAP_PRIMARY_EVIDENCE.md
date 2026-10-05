# Production capture: primary evidence recovered from the PCAP (local, not missing)

Date 2026-09-08. Read-only. No dataset file modified.

Source: `dataset/timesafe/s-plane_security_repo/DataCollectionPTP/prod_successful_announce_attack_ptp.pcap`
sha256 `0690ed95ddc3134e0dbec8e0d7a79b65b379c9574542a7792c1ff2f5a1b20599` (matches the hash held in the project brief).
Parsed with a stdlib pcap reader; libpcap little-endian, microsecond, linktype 1 (Ethernet); 13,565 frames, all EtherType 0x88F7 (PTP over Ethernet). Frame count equals the CSV row count exactly.

**Headline: the CSV export kept 7 of ~20 decision-relevant PTP fields. The evidence needed for attack-category, rogue-source-advertisement and takeover-success questions was never missing - it was discarded at CSV export by `pcap_csv_converter.py` and is recoverable locally.**

Announce field offsets are IEEE 1588 standard (priority1 @47, clockClass @48, clockAccuracy @49, priority2 @52, grandmasterIdentity @53-60, stepsRemoved @61-62, timeSource @63). Offsets independently validated: the attacker's frames decode to the exact linuxptp free-running default set, which would not occur under a misaligned read.

## 1. Advertised clock state, per sender

| Sender | Announce n | priority1 | clockClass | clockAccuracy | priority2 | sourceClockIdentity | logAnnounceInterval |
|---|---|---|---|---|---|---|---|
| `c4:5a:b1:3a:1b:46` (incumbent) | 1764 | 128 | 6 / 1 / 135 / 165 (over time) | 0x21, 0xFE | 120 / 128 / 1 | `c45ab1ffff3a1b05` | 253 (= -3, 8/s) |
| `b8:ce:f6:5e:6b:4a` (labelled sender) | 200 | 128 | 248 (all) | 0xFE (all) | 128 (all) | `b8cef6fffe5e6b4a` | 253 (= -3, 8/s) |

The labelled sender advertises priority1=128, clockClass=248, clockAccuracy=0xFE (unknown), timeSource=0xA0 (internal oscillator), stepsRemoved=0 - the linuxptp default free-running grandmaster profile.

## 2. Receiver-side BMCA evidence IS in the capture

The incumbent is a boundary clock: it re-announces the grandmaster it has selected. Its announced state is therefore a direct, on-wire record of its own source-selection decision - the "receiver-side BMCA log" that was assumed missing.

State transitions (t relative to first frame; capture span 0 - 240.786 s):

| t (s) | grandmasterIdentity | clockClass | priority2 | stepsRemoved | timeSource | Reading |
|---|---|---|---|---|---|---|
| 0.008954 | `fcaf6afffe02babe` | 6 | 120 | 1 | 0x20 (GPS) | Healthy: locked to an upstream GNSS-traceable grandmaster |
| 78.385595 | `c45ab1ffff3a1b05` (self) | 1 | 128 | 0 | 0xA0 (internal osc) | Upstream GNSS grandmaster dropped; self-declared, free-running |
| 78.505816 | `b8cef6fffe5e6b4a` (labelled sender) | 1 | 1 | 1 | 0xA0 | **Selected the labelled sender as grandmaster** |
| 79.257649 | `b8cef6fffe5e6b4a` | 1 | 1 | 2 | 0x20 | Still following it; stepsRemoved 1 -> 2 |
| 97.641769 | `c45ab1ffff3a1b05` (self) | 135 | 128 | 0 | 0xA0 | **Ejected it**; holdover, degraded |
| 177.538479 | `c45ab1ffff3a1b05` (self) | 165 | 128 | 0 | 0xA0 | Holdover degrades further; never returns to class 6 |

Labelled-sender Announce window: 78.506815 - 105.308242 s.

## 3. Five consequences that change the analysis

### 3.1 Takeover success is established on-wire, not inferred

The victim boundary clock announced the labelled sender's clockIdentity as its grandmaster for ~19 s. This is observed behaviour of the receiver, independent of the supplied labels.

### 3.2 The capture does not contain the attack onset

The victim selected the labelled sender at t=78.505816, which is 999 us BEFORE the first captured Announce from that sender (78.506815). A decision cannot precede its cause. Therefore at least one triggering Announce is absent from this capture. Consequence: **78.506815 s must not be used as attack start time**, and any window feature anchored on it is anchored on a censored boundary. This is a concrete instance of criterion 5 (distinguishing missing captured packets from real loss).

### 3.3 GNSS loss precedes the takeover by 120 ms

At 78.385595 the victim had already lost `fcaf6afffe02babe` and gone to internal oscillator - before any captured attack frame. Whether the attack caused that loss or an independent upstream/GNSS fault preceded it CANNOT be determined from this capture. This is exactly the benign-fault versus attack ambiguity the project must classify, and here the honest answer is "not separable from this evidence."

### 3.4 The supplied labels are incomplete

The labelled sender also transmitted 392 Sync (type 0) and 392 Follow_Up (type 8), from 78.568 to 105.370 s - a full two-step master message set. It transmitted zero Sync/Follow_Up at any other time in the capture (before the window it sent only Delay_Req, n=1241; the whole capture shows type 0 n=392 and type 8 n=392 for this sender, all inside the window). The label file marks only the 200 Announce as Label=1. **784 frames from the same sender, in the same window, carrying the same role change, are labelled 0.** The label column is therefore "Announce frames from the labelled sender", not "malicious frames".

### 3.5 The repository attack script did not produce this capture

`Testbed/PipelineTestAttacker/Scripts/Announce_Attack.py` sets priority1=0, priority2=0, grandmasterClockClass=0, and builds sourcePortIdentity clockIdentity with an FF:FF insert. The capture shows 128 / 128 / 248 and a standard FF:FE EUI-64 clockIdentity, plus Sync and Follow_Up that the scapy script never sends. Working hypothesis (NOT established): the production run used a standard `ptp4l` instance in master mode on the attacker host. Note the 0.125 s cadence is NOT evidence for either - logAnnounceInterval=253 (-3) is used by the incumbent too, i.e. it is the profile's 8/s Announce rate, not an attacker signature.

### 3.6 Retained Production Conclusions (WHAT / WHICH / WHERE / WHEN / WHY / HOW)

#### Conclusion A (Criterion 13): On-Wire BMCA Takeover Observed in Victim Announce Stream
- **WHAT**: On-wire BMCA grandmaster takeover observed directly in the victim boundary clock's own transmitted Announce frames.
- **WHICH**: Incumbent boundary clock `c4:5a:b1:3a:1b:46` selecting candidate grandmaster `b8:ce:f6:5e:6b:4a`.
- **WHERE**: Packet capture `dataset/timesafe/s-plane_security_repo/DataCollectionPTP/prod_successful_announce_attack_ptp.pcap`.
- **WHEN**: Selected at t=78.505816 s (following GNSS loss at t=78.385595 s) through ejection at t=97.641769 s, spanning ~19 s.
- **WHY**: The incumbent is a boundary clock that re-announces the grandmaster it has selected; at t=78.505816 s its announced grandmasterIdentity switches to `b8cef6fffe5e6b4a`, providing an on-wire record of its source-selection decision.
- **HOW**: Re-derive from the PCAP by filtering for Announce frames (MessageType 11) emitted by source `c4:5a:b1:3a:1b:46` and tracking the grandmasterIdentity field (offsets 53-60) chronologically.
- **What this does NOT establish**: Does NOT establish that the candidate source was an unauthorized attacker rather than a misconfigured or secondary master, nor does it establish physical receiver clock health or recovery.

#### Conclusion B (Criterion 14): Supplied Labels Omit Same Sender Sync and Follow_Up Frames
- **WHAT**: Supplied binary positive labels mark only Announce frames from the candidate sender, omitting concurrent Sync and Follow_Up frames transmitted by the same sender in the same window.
- **WHICH**: Labelled sender `b8:ce:f6:5e:6b:4a` transmitted 200 Announce frames (labelled 1), but also 392 Sync frames and 392 Follow_Up frames (784 frames, all labelled 0).
- **WHERE**: In `timesafe_prod_successful_announce_attack_labeled.csv` and the aligned PCAP.
- **WHEN**: During the active transmission window (Sync/Follow_Up from 78.568 to 105.370 s; Announce window 78.506815 to 105.308242 s).
- **WHY**: Packet accounting shows the labelled sender transmitted a full two-step master stream (392 Sync, 392 Follow_Up, 200 Announce), yet only the 200 Announce frames are labelled 1; all 784 timing frames in the same window carry Label=0.
- **HOW**: Re-derive from the PCAP or CSV by filtering for frames with source `b8:ce:f6:5e:6b:4a` and tabulating frame counts by MessageType and Label.
- **What this does NOT establish**: Does NOT establish that the unlabelled Sync and Follow_Up frames were benign; it establishes that the label column means "Announce frames from that sender", not "malicious frames".

#### Conclusion C (Criterion 15): Victim Selected Labelled Sender Before First Captured Announce
- **WHAT**: The victim boundary clock selected the labelled sender before the first captured Announce frame arrived from it, establishing that the capture does not contain the attack onset.
- **WHICH**: Incumbent boundary clock `c4:5a:b1:3a:1b:46` re-announcing grandmaster `b8cef6fffe5e6b4a` relative to frames from `b8:ce:f6:5e:6b:4a`.
- **WHERE**: In `prod_successful_announce_attack_ptp.pcap`.
- **WHEN**: Victim announced selection at t=78.505816 s, which is 999 us before the first captured Announce from the labelled sender at t=78.506815 s.
- **WHY**: A selection decision cannot precede the arrival of the message causing it; therefore at least one triggering Announce frame is absent from this capture.
- **HOW**: Re-derive from the PCAP by comparing the capture timestamp of the victim's first Announce advertising `b8cef6fffe5e6b4a` against the capture timestamp of the first Announce emitted by `b8:ce:f6:5e:6b:4a`.
- **What this does NOT establish**: Does NOT establish the true physical attack start time, which occurred prior to the capture boundary.

## 4. Unresolved / do not invent

- **clockClass=1** appears in 39 incumbent Announce frames (78.386 - 97.642 s). IEEE 1588-2019 reserves clockClass 1-5; ITU-T G.8275.1 does not define it. Not explained. Resolution needs the victim device's vendor documentation or its ptp4l/profile configuration.
- **Why the BMCA selected a clockClass-248 free-running source** while the victim announced a numerically better class is not explained by the Announce fields as parsed. Resolution needs the victim's PTP configuration (profile, localPriority, domain, masterOnly/slaveOnly per port) and its ptp4l log.
- The attacker-side start/stop log that `Announce_Attack.py::log_attack_start_end` would have written is genuinely absent: `s-plane_security_repo/logs/` contains only `.gitkeep`.
- No hardware clock-offset measurement, no GNSS receiver record, and no recovery command/acknowledgement exists in this capture. Packet-derived offsets are not receiver measurements.
