import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def audit_criterion06():
    root = Path(__file__).resolve().parent
    repo_root = root.parents[1]
    raw_dir = repo_root / 'dataset' / 'timesafe' / 'timesafe_multi_raw'

    pcap1_path = raw_dir / 'announce_session_1.pcap'
    pcap2_path = raw_dir / 'announce_session_2.pcap'
    csv1_path = raw_dir / 'announce_session_1_labels.csv'
    csv2_path = raw_dir / 'announce_session_2_labels.csv'

    # a) sha256 of pcaps and pcaps_identical
    sha256_pcap1 = compute_sha256(pcap1_path)
    sha256_pcap2 = compute_sha256(pcap2_path)
    pcaps_identical = (sha256_pcap1 == sha256_pcap2)

    # b) sha256 of label csvs
    sha256_csv1 = compute_sha256(csv1_path)
    sha256_csv2 = compute_sha256(csv2_path)

    # Load rows
    with open(csv1_path, 'r', encoding='utf-8') as f:
        rows1 = list(csv.DictReader(f))
    with open(csv2_path, 'r', encoding='utf-8') as f:
        rows2 = list(csv.DictReader(f))

    # c) row counts, label counts per file, count of conflicting rows, conflict direction breakdown
    row_count_csv1 = len(rows1)
    row_count_csv2 = len(rows2)

    labels_csv1_counts = dict(Counter(row['Label'] for row in rows1))
    labels_csv2_counts = dict(Counter(row['Label'] for row in rows2))

    conflicts_0_to_1 = 0
    conflicts_1_to_0 = 0
    for r1, r2 in zip(rows1, rows2):
        l1 = r1['Label']
        l2 = r2['Label']
        if l1 == '0' and l2 == '1':
            conflicts_0_to_1 += 1
        elif l1 == '1' and l2 == '0':
            conflicts_1_to_0 += 1

    conflicting_rows_count = conflicts_0_to_1 + conflicts_1_to_0

    # d) boolean nonlabel_columns_identical
    nonlabel_cols = [c for c in rows1[0].keys() if c != 'Label']
    nonlabel_columns_identical = (
        len(rows1) == len(rows2) and
        all(all(r1[col] == r2[col] for col in nonlabel_cols) for r1, r2 in zip(rows1, rows2))
    )

    # g) full (Source, MessageType) frame inventory of the capture
    inventory_counts = Counter((row['Source'], row['MessageType']) for row in rows1)
    inventory_list = [
        {
            "source": src,
            "message_type": mt,
            "frame_count": count
        }
        for (src, mt), count in sorted(inventory_counts.items())
    ]

    all_pairs = sorted(inventory_counts.keys())

    # e) exhaustive scan over every (Source, MessageType) pair present for EACH file
    def scan_rules(rows):
        total = len(rows)
        results = []
        for src, mt in all_pairs:
            match_count = sum(1 for r in rows if r['Source'] == src and r['MessageType'] == mt)
            agreed_count = sum(
                1 for r in rows
                if (r['Source'] == src and r['MessageType'] == mt) == (r['Label'] == '1')
            )
            exact = (agreed_count == total)
            results.append({
                "source": src,
                "message_type": mt,
                "rule_match_count": match_count,
                "rows_agreeing_with_label": agreed_count,
                "exact": exact
            })
        return results

    rule_scan_csv1 = scan_rules(rows1)
    rule_scan_csv2 = scan_rules(rows2)

    # f) positives broken down by (Source, MessageType) for EACH file
    positives_csv1_counts = Counter(
        (row['Source'], row['MessageType']) for row in rows1 if row['Label'] == '1'
    )
    positives_csv2_counts = Counter(
        (row['Source'], row['MessageType']) for row in rows2 if row['Label'] == '1'
    )

    positives_csv1 = [
        {"source": src, "message_type": mt, "count": cnt}
        for (src, mt), cnt in sorted(positives_csv1_counts.items())
    ]
    positives_csv2 = [
        {"source": src, "message_type": mt, "count": cnt}
        for (src, mt), cnt in sorted(positives_csv2_counts.items())
    ]

    result = {
        "pcap_comparison": {
            "announce_session_1_pcap_sha256": sha256_pcap1,
            "announce_session_2_pcap_sha256": sha256_pcap2,
            "pcaps_identical": pcaps_identical
        },
        "csv_comparison": {
            "announce_session_1_labels_csv_sha256": sha256_csv1,
            "announce_session_2_labels_csv_sha256": sha256_csv2,
            "row_count_csv1": row_count_csv1,
            "row_count_csv2": row_count_csv2,
            "nonlabel_columns_identical": nonlabel_columns_identical,
            "labels_csv1_counts": labels_csv1_counts,
            "labels_csv2_counts": labels_csv2_counts,
            "conflicting_rows_count": conflicting_rows_count,
            "conflict_breakdown": {
                "conflicts_0_to_1": conflicts_0_to_1,
                "conflicts_1_to_0": conflicts_1_to_0
            }
        },
        "frame_inventory": inventory_list,
        "labels_file_1": {
            "positives_by_source_and_type": positives_csv1,
            "rule_scan": rule_scan_csv1
        },
        "labels_file_2": {
            "positives_by_source_and_type": positives_csv2,
            "rule_scan": rule_scan_csv2
        }
    }

    out_file = root / 'criterion06_audit.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"Audit output written to {out_file}")

if __name__ == '__main__':
    audit_criterion06()
