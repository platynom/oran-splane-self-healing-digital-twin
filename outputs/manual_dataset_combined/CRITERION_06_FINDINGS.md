# Criterion 6 Findings: Announce Session 1 vs 2 Audit

This document details the forensic audit of Announce Session 1 and Announce Session 2 captures and label sets, providing beginner-level explanations across WHAT, WHICH, WHERE, WHEN, WHY, and HOW dimensions.

---

## 1. Executive Summary

- **WHAT**: Forensic audit examining whether Announce Session 1 and Session 2 represent independent experimental captures and evaluating the mathematical reproducibility of their respective label sets.
- **WHICH**: Evaluated on `dataset/timesafe/timesafe_multi_raw/announce_session_1.pcap` versus `announce_session_2.pcap`, and `announce_session_1_labels.csv` versus `announce_session_2_labels.csv`.
- **WHERE**: Dataset storage layer under `dataset/timesafe/timesafe_multi_raw/`.
- **WHEN**: Assessed during project dataset reconciliation and criterion audit.
- **WHY**: Using duplicate captures under alternate filenames creates artificial sample inflation and train/test data leakage. Furthermore, conflicting labels across identical captures invalidate supervised evaluation.
- **HOW**: Cryptographic SHA-256 hashing, row-level non-label field equality checks, exhaustive rule evaluation across all `(Source, MessageType)` combinations, and message type inventory analysis.

---

## 2. Detailed Findings

### 2.1 Capture Duplication (One Capture Under Two Names)

- **Finding**: The two capture files `announce_session_1.pcap` and `announce_session_2.pcap` share the identical SHA-256 hash (`d2c91b3e4f09a3ecaffc81b9fb5b45b874adf2946ed88fc3eccaeaf3a631983e`). The boolean indicator `pcaps_identical` evaluated to `True`.
- **Methodological Impact**: The two PCAP files are byte-identical copies of a single packet capture under different filenames. They do not constitute independent repetitions or external corroboration. Treating them as separate sessions in dataset splits results in duplicate counting and severe train/test data leakage.

### 2.2 Row-by-Row Comparison and Non-Label Field Identity

- Both label files contain exactly 46998 rows.
- All non-label columns (`Source`, `Destination`, `Length`, `SequenceID`, `MessageType`, `Time Interval`) match row-for-row without exception (`nonlabel_columns_identical` evaluated to `True`).
- The label files differ solely in their `Label` column:
  - `announce_session_1_labels.csv` contains 42521 zeros and 4477 ones (SHA-256: `6a03a10bd9f4748031a7e8dc66305107d734db01079499fd7018661ba501046a`).
  - `announce_session_2_labels.csv` contains 37211 zeros and 9787 ones (SHA-256: `840769d5c5c54177dc3ee9ae1648f4edf36450b817c11b129c8e8973641fb689`).
- A total of 5312 rows conflict between the two files. The conflict is essentially one-directional:
  - 5311 rows transition from 0 in Session 1 to 1 in Session 2.
  - Exactly 1 row transitions from 1 in Session 1 to 0 in Session 2.
  - Thus, the positive set of Session 2 is essentially a superset of Session 1.

### 2.3 Rule Reproducibility Analysis

- **Session 2 Exact Reproducibility**:
  - Scanning all `(Source, MessageType)` combinations in the capture reveals that `announce_session_2_labels.csv` is 100% reproduced by a single capture-intrinsic rule:
    `Source == 1 AND MessageType == 11`
  - This rule matches exactly 9787 rows and agrees with the label column across all 46998 of 46998 rows (zero false positives, zero false negatives).
- **Session 1 Unreproducibility**:
  - No single `(Source, MessageType)` rule reproduces `announce_session_1_labels.csv`.
  - The 4477 positive labels in Session 1 consist of 4476 Announce frames (`MessageType == 11`) and 1 Follow_Up frame (`MessageType == 8`) from Source 1.
  - The presence of an isolated non-Announce frame (Follow_Up) is the classic signature of an arbitrary time-window filter that clipped a boundary-adjacent packet, rather than a coherent protocol identity rule.

### 2.4 Label Set Disposition

- **Retained Label Set**: `announce_session_2_labels.csv` is retained as the authoritative representation for this capture because it follows an exact, mathematically reproducible protocol rule.
- **Quarantined Label Set**: `announce_session_1_labels.csv` is quarantined as an unreproducible, partial labeling artifact. It is retained on disk for provenance tracing and audit history, but excluded from model training and evaluation.

### 2.5 Scope Caveat on Label Semantics (Mirroring Production Capture)

- The full capture inventory reveals the following frame distribution across sources and message types:
  - Source 0: 10634 Sync (`MessageType == 0`), 5317 Announce (`MessageType == 11`), 12 Delay_Resp (`MessageType == 9`).
  - Source 1: 10618 Sync (`MessageType == 0`), 10618 Follow_Up (`MessageType == 8`), 9787 Announce (`MessageType == 11`), 12 Delay_Req (`MessageType == 1`).
- Source 1 transmitted a total of 31035 frames across the capture, including full two-step master streams (10618 Sync frames and 10618 Follow_Up frames).
- In both Session 1 and Session 2, all 10618 Sync frames and all 10618 Follow_Up frames from Source 1 are labeled 0. Only Announce frames from Source 1 are labeled 1 in Session 2.
- **Semantic Conclusion**: The label column signifies "Announce frame from Source 1", not "malicious frame". Positive labels omit the transmitter's synchronized timing frames within the same session.

---

## 3. Scope of Established Facts vs. Unestablished Claims

### Established Facts
1. The two PCAP files represent a single capture duplicated under two separate filenames.
2. `announce_session_2_labels.csv` is exactly described by `Source == 1 AND MessageType == 11`.
3. `announce_session_1_labels.csv` is an incomplete subset with an extraneous boundary-clipped Follow_Up frame.
4. Positive labels cover only Announce messages and omit concurrent Sync and Follow_Up traffic from the same sender.

### Unestablished Claims (Do Not Infer)
1. **Unauthorised Source Identity**: The packet data demonstrates that Source 1 transmitted Announce frames at grandmaster cadence, but does not prove that Source 1 was an unauthorized rogue attacker versus a misconfigured or secondary master.
2. **True Attack Window**: Packet timestamps alone cannot define the operational attack boundary without independent launcher execution logs.
3. **Clock-Health and Recovery Outcomes**: This dataset contains packet-level traffic without physical receiver oscillator telemetry, phase offset measurements, or automated healing action acknowledgments.
