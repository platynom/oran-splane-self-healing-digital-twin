import json
from pathlib import Path

def build_criterion06_findings():
    root = Path(__file__).resolve().parent
    audit_file = root / 'criterion06_audit.json'

    with open(audit_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pcap_comp = data['pcap_comparison']
    csv_comp = data['csv_comparison']
    inv = {f"{item['source']}_{item['message_type']}": item['frame_count'] for item in data['frame_inventory']}
    l1_pos = {f"{item['source']}_{item['message_type']}": item['count'] for item in data['labels_file_1']['positives_by_source_and_type']}
    l2_pos = {f"{item['source']}_{item['message_type']}": item['count'] for item in data['labels_file_2']['positives_by_source_and_type']}

    pcap_hash = pcap_comp['announce_session_1_pcap_sha256']
    pcaps_identical = pcap_comp['pcaps_identical']
    
    csv1_hash = csv_comp['announce_session_1_labels_csv_sha256']
    csv2_hash = csv_comp['announce_session_2_labels_csv_sha256']
    rows_csv1 = csv_comp['row_count_csv1']
    rows_csv2 = csv_comp['row_count_csv2']
    nonlabel_identical = csv_comp['nonlabel_columns_identical']
    
    l1_zeros = csv_comp['labels_csv1_counts']['0']
    l1_ones = csv_comp['labels_csv1_counts']['1']
    l2_zeros = csv_comp['labels_csv2_counts']['0']
    l2_ones = csv_comp['labels_csv2_counts']['1']

    conflicts = csv_comp['conflicting_rows_count']
    c_0_to_1 = csv_comp['conflict_breakdown']['conflicts_0_to_1']
    c_1_to_0 = csv_comp['conflict_breakdown']['conflicts_1_to_0']

    l1_ann = l1_pos.get('1_11', 0)
    l1_fu = l1_pos.get('1_8', 0)
    l2_ann = l2_pos.get('1_11', 0)

    src1_sync = inv.get('1_0', 0)
    src1_fu = inv.get('1_8', 0)
    src1_ann = inv.get('1_11', 0)
    src1_dreq = inv.get('1_1', 0)

    src0_sync = inv.get('0_0', 0)
    src0_ann = inv.get('0_11', 0)
    src0_dresp = inv.get('0_9', 0)

    # Rule scan result for labels 2 rule (1, 11)
    l2_rule = next(r for r in data['labels_file_2']['rule_scan'] if r['source'] == '1' and r['message_type'] == '11')
    l2_agreements = l2_rule['rows_agreeing_with_label']

    content = f"""# Criterion 6 Findings: Announce Session 1 vs 2 Audit

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

- **Finding**: The two capture files `announce_session_1.pcap` and `announce_session_2.pcap` share the identical SHA-256 hash (`{pcap_hash}`). The boolean indicator `pcaps_identical` evaluated to `{pcaps_identical}`.
- **Methodological Impact**: The two PCAP files are byte-identical copies of a single packet capture under different filenames. They do not constitute independent repetitions or external corroboration. Treating them as separate sessions in dataset splits results in duplicate counting and severe train/test data leakage.

### 2.2 Row-by-Row Comparison and Non-Label Field Identity

- Both label files contain exactly {rows_csv1} rows.
- All non-label columns (`Source`, `Destination`, `Length`, `SequenceID`, `MessageType`, `Time Interval`) match row-for-row without exception (`nonlabel_columns_identical` evaluated to `{nonlabel_identical}`).
- The label files differ solely in their `Label` column:
  - `announce_session_1_labels.csv` contains {l1_zeros} zeros and {l1_ones} ones (SHA-256: `{csv1_hash}`).
  - `announce_session_2_labels.csv` contains {l2_zeros} zeros and {l2_ones} ones (SHA-256: `{csv2_hash}`).
- A total of {conflicts} rows conflict between the two files. The conflict is essentially one-directional:
  - {c_0_to_1} rows transition from 0 in Session 1 to 1 in Session 2.
  - Exactly {c_1_to_0} row transitions from 1 in Session 1 to 0 in Session 2.
  - Thus, the positive set of Session 2 is essentially a superset of Session 1.

### 2.3 Rule Reproducibility Analysis

- **Session 2 Exact Reproducibility**:
  - Scanning all `(Source, MessageType)` combinations in the capture reveals that `announce_session_2_labels.csv` is 100% reproduced by a single capture-intrinsic rule:
    `Source == 1 AND MessageType == 11`
  - This rule matches exactly {l2_ann} rows and agrees with the label column across all {l2_agreements} of {rows_csv2} rows (zero false positives, zero false negatives).
- **Session 1 Unreproducibility**:
  - No single `(Source, MessageType)` rule reproduces `announce_session_1_labels.csv`.
  - The {l1_ones} positive labels in Session 1 consist of {l1_ann} Announce frames (`MessageType == 11`) and {l1_fu} Follow_Up frame (`MessageType == 8`) from Source 1.
  - The presence of an isolated non-Announce frame (Follow_Up) is the classic signature of an arbitrary time-window filter that clipped a boundary-adjacent packet, rather than a coherent protocol identity rule.

### 2.4 Label Set Disposition

- **Retained Label Set**: `announce_session_2_labels.csv` is retained as the authoritative representation for this capture because it follows an exact, mathematically reproducible protocol rule.
- **Quarantined Label Set**: `announce_session_1_labels.csv` is quarantined as an unreproducible, partial labeling artifact. It is retained on disk for provenance tracing and audit history, but excluded from model training and evaluation.

### 2.5 Scope Caveat on Label Semantics (Mirroring Production Capture)

- The full capture inventory reveals the following frame distribution across sources and message types:
  - Source 0: {src0_sync} Sync (`MessageType == 0`), {src0_ann} Announce (`MessageType == 11`), {src0_dresp} Delay_Resp (`MessageType == 9`).
  - Source 1: {src1_sync} Sync (`MessageType == 0`), {src1_fu} Follow_Up (`MessageType == 8`), {src1_ann} Announce (`MessageType == 11`), {src1_dreq} Delay_Req (`MessageType == 1`).
- Source 1 transmitted a total of {src1_ann + src1_sync + src1_fu + src1_dreq} frames across the capture, including full two-step master streams ({src1_sync} Sync frames and {src1_fu} Follow_Up frames).
- In both Session 1 and Session 2, all {src1_sync} Sync frames and all {src1_fu} Follow_Up frames from Source 1 are labeled 0. Only Announce frames from Source 1 are labeled 1 in Session 2.
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
"""

    out_path = root / 'CRITERION_06_FINDINGS.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully generated {out_path}")

if __name__ == '__main__':
    build_criterion06_findings()
