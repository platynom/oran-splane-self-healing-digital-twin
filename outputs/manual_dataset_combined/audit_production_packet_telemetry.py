"""Read-only event trace of the configured PCAP-to-telemetry state machine."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
sys.path.insert(0, str(APP))
from ingest import ptp_wire as w  # noqa: E402

PCAP = APP / "data" / "external" / "timesafe_prod_successful_announce_attack_ptp.pcap"


def main() -> None:
    last_t1 = last_t2 = None
    last_sync_corr = 0.0
    pending_sync: dict[int, tuple[int, float, int]] = {}
    dreq_t3: dict[int, tuple[int, int]] = {}
    mean_path_delay = last_known_pd = last_exchange_ns = None
    t0 = None
    decoded = 0
    emitted: list[dict] = []
    skipped: list[dict] = []
    message_counts = Counter()
    sequence_reuse = Counter()
    last_seq_type: dict[tuple[str, int], int] = {}

    def emit(packet_index: int, ts_ns: int, msg_type: str, seq: int) -> None:
        nonlocal mean_path_delay
        if last_t1 is None or last_t2 is None:
            skipped.append({"packet_index": packet_index, "message_type": msg_type, "sequence_id": seq,
                            "reason": "no resolved Sync origin/arrival state"})
            return
        stale = mean_path_delay is None or (last_exchange_ns is not None and (ts_ns - last_exchange_ns) / 1e9 > 2.0)
        emitted.append({"packet_index": packet_index, "t_s": (ts_ns - t0) / 1e9,
                        "message_type": msg_type, "sequence_id": seq,
                        "path_delay_state": "last_known_or_zero" if mean_path_delay is None else ("stale" if stale else "fresh")})

    for packet_index, (capture_ns, frame) in enumerate(w.read_pcap(str(PCAP)), start=1):
        payload = w.parse_eth_frame(frame)
        if payload is None:
            continue
        msg = w.decode_ptp_payload(payload)
        if msg is None:
            continue
        decoded += 1
        if t0 is None:
            t0 = capture_ns
        msg_name = w.MSG_NAME[msg.msg_type]
        message_counts[msg_name] += 1
        key = (msg_name, msg.seq_id)
        if key in last_seq_type:
            sequence_reuse[key] += 1
        last_seq_type[key] = packet_index
        if msg.msg_type == w.MT_SYNC:
            if msg.origin_ts_ns:
                last_t1, last_t2, last_sync_corr = int(msg.origin_ts_ns), capture_ns, msg.correction_ns
                emit(packet_index, capture_ns, msg_name, msg.seq_id)
            else:
                pending_sync[msg.seq_id] = (capture_ns, msg.correction_ns, packet_index)
                skipped.append({"packet_index": packet_index, "message_type": msg_name, "sequence_id": msg.seq_id,
                                "reason": "two-step Sync waits for matching Follow_Up"})
        elif msg.msg_type == w.MT_FOLLOW_UP:
            if msg.seq_id in pending_sync and msg.origin_ts_ns is not None:
                t2, corr, sync_index = pending_sync.pop(msg.seq_id)
                last_t1, last_t2, last_sync_corr = int(msg.origin_ts_ns), t2, corr + msg.correction_ns
                emit(sync_index, t2, "Sync", msg.seq_id)
                emit(packet_index, capture_ns, msg_name, msg.seq_id)
            else:
                skipped.append({"packet_index": packet_index, "message_type": msg_name, "sequence_id": msg.seq_id,
                                "reason": "no matching pending two-step Sync or missing origin timestamp"})
        elif msg.msg_type == w.MT_DELAY_REQ:
            dreq_t3[msg.seq_id] = (capture_ns, packet_index)
            emit(packet_index, capture_ns, msg_name, msg.seq_id)
        elif msg.msg_type == w.MT_DELAY_RESP:
            if msg.seq_id in dreq_t3 and msg.origin_ts_ns is not None and last_t1 is not None:
                t3, _ = dreq_t3.pop(msg.seq_id)
                mean_path_delay = ((last_t2 - last_t1) + (int(msg.origin_ts_ns) - t3)) / 2.0
                last_known_pd, last_exchange_ns = mean_path_delay, capture_ns
            emit(packet_index, capture_ns, msg_name, msg.seq_id)
        else:
            emit(packet_index, capture_ns, msg_name, msg.seq_id)

    emitted_by_packet = Counter(row["packet_index"] for row in emitted)
    duplicate_timestamps = sum(n - 1 for n in Counter(row["t_s"] for row in emitted).values() if n > 1)
    result = {
        "purpose": "Read-only trace that mirrors pcap_ingest state transitions; not a cross-capture join.",
        "pcap": str(PCAP.relative_to(ROOT)),
        "decoded_ptp_packets": decoded,
        "message_counts": dict(message_counts),
        "telemetry_emissions": len(emitted),
        "source_packets_with_no_emission": decoded - len(emitted_by_packet),
        "source_packets_with_multiple_emissions": sum(1 for n in emitted_by_packet.values() if n > 1),
        "max_emissions_per_packet": max(emitted_by_packet.values(), default=0),
        "skipped_reason_counts": dict(Counter(row["reason"] for row in skipped)),
        "unresolved_pending_sync_sequences": len(pending_sync),
        "unresolved_delay_request_sequences": len(dreq_t3),
        "duplicate_derived_timestamps": duplicate_timestamps,
        "reused_message_type_sequence_pairs": sum(sequence_reuse.values()),
        "first_skipped": skipped[:20],
        "first_emitted": emitted[:20],
    }
    out = Path(__file__).with_name("production_packet_telemetry_alignment.json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
