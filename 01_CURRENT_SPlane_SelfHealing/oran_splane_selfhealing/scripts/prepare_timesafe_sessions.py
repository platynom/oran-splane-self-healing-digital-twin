from __future__ import annotations

"""Split released TIMESAFE captures into labelled per-session telemetry files."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingest.pcap_ingest import pcap_to_telemetry


def split_session(
    pcap_path: Path,
    labels_path: Path,
    attack_family: str,
    out_dir: Path,
    allow_unvalidated_interval_projection: bool = False,
) -> tuple[Path, Path]:
    if not allow_unvalidated_interval_projection:
        raise ValueError(
            "Refusing to convert packet-label timing into H0/H1 clock-state labels. "
            "Pass --allow-unvalidated-interval-projection only for an explicitly "
            "quarantined exploratory export."
        )
    labels = pd.read_csv(labels_path)
    if "Label" not in labels or "Time Interval" not in labels:
        raise ValueError(f"{labels_path} lacks TIMESAFE Label/Time Interval columns")
    packet_times = labels["Time Interval"].astype(float).cumsum()
    attack_times = packet_times[labels["Label"].astype(int) == 1]
    if attack_times.empty:
        raise ValueError(f"{labels_path} contains no attack-labelled packets")
    attack_start = float(attack_times.min())
    attack_end = float(attack_times.max())

    capture_id = pcap_path.stem
    telemetry = pcap_to_telemetry(pcap_path, scenario=capture_id, label="unlabeled")
    telemetry["capture_id"] = capture_id
    telemetry["attack_family"] = attack_family
    # The packet labels identify injected malicious messages. Their first/last
    # timestamps bound the operational attack interval: ordinary PTP packets
    # inside that interval still carry the attacked clock state and must not be
    # relabelled benign.
    in_attack = telemetry["t_s"].between(attack_start, attack_end, inclusive="both")
    benign = telemetry[~in_attack].copy()
    attack = telemetry[in_attack].copy()
    benign["label"] = "H0"
    attack["label"] = "H1"
    if benign.empty or attack.empty:
        raise ValueError(
            f"{capture_id}: split produced benign={len(benign)}, attack={len(attack)} rows"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    benign_path = out_dir / f"{capture_id}__benign.csv"
    attack_path = out_dir / f"{capture_id}__{attack_family}.csv"
    benign.to_csv(benign_path, index=False)
    attack.to_csv(attack_path, index=False)
    (out_dir / "TIMESAFE_SESSION_METADATA.json").write_text(
        json.dumps(
            {
                "validation_status": "unvalidated_interval_projection",
                "label_meaning": "H0/H1 was projected from first/last supplied packet labels; not a measured clock-health or attack-exposure label.",
                "source_pcap": str(pcap_path),
                "source_labels": str(labels_path),
                "attack_family": attack_family,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"{capture_id}: attack={attack_start:.6f}..{attack_end:.6f}s, "
        f"benign_rows={len(benign)}, attack_rows={len(attack)}"
    )
    return benign_path, attack_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", action="append", required=True)
    parser.add_argument("--labels", action="append", required=True)
    parser.add_argument("--family", action="append", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--allow-unvalidated-interval-projection", action="store_true")
    args = parser.parse_args()
    if not (len(args.pcap) == len(args.labels) == len(args.family)):
        parser.error("--pcap, --labels, and --family counts must match")
    for pcap, labels, family in zip(args.pcap, args.labels, args.family):
        split_session(
            Path(pcap), Path(labels), family, Path(args.out_dir),
            args.allow_unvalidated_interval_projection,
        )


if __name__ == "__main__":
    main()
