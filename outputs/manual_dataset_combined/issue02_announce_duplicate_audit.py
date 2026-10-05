"""Audit the conflicting Announce-session labels without modifying any source."""
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "dataset" / "timesafe"
UPSTREAM = DATA / "s-plane_security_repo" / "DataCollectionPTP"
FILES = {
    "raw_15min": UPSTREAM / "15min_announce_attack.csv",
    "raw_uedata": UPSTREAM / "2024-10-06-announce_attack_UEdata.csv",
    "pcap_15min": UPSTREAM / "15min_announce_attack.pcap",
    "pcap_uedata": UPSTREAM / "2024-10-06-announce_attack_UEdata.pcap",
    "session_1_pcap": DATA / "timesafe_multi_raw" / "announce_session_1.pcap",
    "session_2_pcap": DATA / "timesafe_multi_raw" / "announce_session_2.pcap",
    "session_1_labels": DATA / "timesafe_multi_raw" / "announce_session_1_labels.csv",
    "session_2_labels": DATA / "timesafe_multi_raw" / "announce_session_2_labels.csv",
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def label_rule(rows_, source, message_type):
    return [int(row["Source"] == source and row["MessageType"] == message_type)
            for row in rows_]


def matches_processed_label(raw_rows, labelled_rows):
    """Recreate the documented CSV preprocessing only far enough to check linkage."""
    mapping = {}
    for column in ("Source", "Destination"):
        for row in raw_rows:
            value = row[column]
            if value not in mapping:
                mapping[value] = len(mapping)
    previous_time = None
    for raw, labelled in zip(raw_rows, labelled_rows):
        current_time = Decimal(raw["Time"])
        interval = Decimal(0) if previous_time is None else current_time - previous_time
        message_types = {"Sync": "0", "Delay_Req": "1", "PDelay_Req": "2",
                         "PDelay_Resp": "3", "Follow_Up": "8", "Delay_Resp": "9",
                         "PDelay_Resp_Follow_Up": "10", "Announce": "11",
                         "Signaling": "12", "Management": "13"}
        expected = {
            "Source": str(mapping[raw["Source"]]),
            "Destination": str(mapping[raw["Destination"]]),
            "Length": raw["Length"], "SequenceID": raw["SequenceID"],
            "MessageType": message_types.get(raw["MessageType"], raw["MessageType"]),
        }
        if any(labelled[column] != value for column, value in expected.items()):
            return False
        if abs(Decimal(labelled["Time Interval"]) - interval) > Decimal("0.000000001"):
            return False
        previous_time = current_time
    return len(raw_rows) == len(labelled_rows)


facts = {
    name: {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
           "sha256": digest(path)}
    for name, path in FILES.items()
}
one, two = rows(FILES["session_1_labels"]), rows(FILES["session_2_labels"])
non_label_columns = [column for column in one[0] if column != "Label"]
raw_a, raw_b = rows(FILES["raw_15min"]), rows(FILES["raw_uedata"])
ptp_a = [row for row in raw_a if "ptp" in row["Protocol"].lower()]
ptp_b = [row for row in raw_b if "ptp" in row["Protocol"].lower()]

result = {
    "purpose": "Read-only duplicate and label-conflict audit. No label is promoted to ground truth.",
    "file_facts": facts,
    "pcap_sha256_groups": {},
    "row_counts": {"session_1_labels": len(one), "session_2_labels": len(two),
                   "raw_15min_ptp": len(ptp_a), "raw_uedata_ptp": len(ptp_b)},
    "alignment": {
        "session_1_matches_15min_after_ptp_filter_and_documented_encoding": matches_processed_label(ptp_a, one),
        "session_2_matches_uedata_after_ptp_filter_and_documented_encoding": matches_processed_label(ptp_b, two),
        "all_nonlabel_rows_identical_between_sessions": all(
            all(a[col] == b[col] for col in non_label_columns) for a, b in zip(one, two)),
    },
    "labels": {
        "session_1": dict(Counter(row["Label"] for row in one)),
        "session_2": dict(Counter(row["Label"] for row in two)),
        "conflicts": sum(a["Label"] != b["Label"] for a, b in zip(one, two)),
        "directions": dict(Counter(f'{a["Label"]}->{b["Label"]}' for a, b in zip(one, two)
                                  if a["Label"] != b["Label"])),
        "positive_packet_types_session_1": dict(Counter(f'{row["Source"]}|{row["MessageType"]}'
                                                        for row in one if row["Label"] == "1")),
        "positive_packet_types_session_2": dict(Counter(f'{row["Source"]}|{row["MessageType"]}'
                                                        for row in two if row["Label"] == "1")),
    },
}
for label_name, labelled_rows in (("session_1", one), ("session_2", two)):
    saved = [int(row["Label"]) for row in labelled_rows]
    result["labels"][f"{label_name}_source_6afa_announce_rule"] = {
        "matches_saved_labels": saved == label_rule(labelled_rows, "1", "11"),
        "false_positives": sum(saved_i == 0 and rule_i == 1 for saved_i, rule_i in zip(saved, label_rule(labelled_rows, "1", "11"))),
        "false_negatives": sum(saved_i == 1 and rule_i == 0 for saved_i, rule_i in zip(saved, label_rule(labelled_rows, "1", "11"))),
    }
for name, fact in facts.items():
    result["pcap_sha256_groups"].setdefault(fact["sha256"], []).append(name)

output = Path(__file__).with_name("issue02_announce_duplicate_verification.json")
output.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
