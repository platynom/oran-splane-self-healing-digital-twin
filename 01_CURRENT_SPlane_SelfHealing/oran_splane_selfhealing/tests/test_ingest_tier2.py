from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ingest.linuxptp_ingest import parse_linuxptp_lines
from ingest.pcap_ingest import pcap_to_telemetry
from ingest.schema import TELEMETRY_COLUMNS, validate_telemetry
from ingest.sync_status import parse_pmc_output, parse_synce4l_ql
from scripts.make_synthetic_pcap import generate_synthetic_pcap
from telemetry.features import FEATURE_COLUMNS, window_features


def test_pcap_roundtrip_recovers_offset(tmp_path):
    pcap = tmp_path / "s.pcap"
    truth = generate_synthetic_pcap(pcap, n=150, scenario="healthy")
    # strict mode: measure offset accuracy only on properly-resolved samples
    tel = pcap_to_telemetry(pcap, tolerate_incomplete=False)
    assert validate_telemetry(tel)
    assert list(tel.columns) == TELEMETRY_COLUMNS
    seqs = tel["ptp_seq_id"].to_numpy()
    mae = float(np.abs(tel["offset_ns"].to_numpy() - truth[seqs]).mean())
    # recovery error is bounded by path-delay variation, must be well under a ns-budget scale
    assert mae < 40.0, f"pcap offset recovery MAE too high: {mae}"
    assert abs(tel["path_delay_ns"].mean() - 50_000.0) < 200.0
    assert tel["msg_rate_hz"].max() > tel["msg_rate_hz"].min()


def test_pcap_telemetry_flows_into_features(tmp_path):
    pcap = tmp_path / "s.pcap"
    generate_synthetic_pcap(pcap, n=200, scenario="attack")
    tel = pcap_to_telemetry(pcap, label="H1")
    feats = window_features(tel, window_s=0.4, step_s=0.2)
    assert not feats.empty
    assert feats[FEATURE_COLUMNS].notna().all().all()


def test_holdover_pcap_yields_flagged_telemetry(tmp_path):
    """A capture with NO Delay_Req/Delay_Resp exchange (holdover/outage) must still
    produce holdover-flagged rows, not raise."""
    from ingest import ptp_wire as w
    pcap = tmp_path / "holdover.pcap"
    EP = 1_700_000_000 * 10 ** 9
    wr = w.PcapWriter(str(pcap))
    off = 40.0
    for i in range(25):
        t1 = EP + int(i * 0.0625e9)
        off = off * 0.9 + 3
        t2 = t1 + int(round(50_000 + off))
        wr.write(t2, w.build_eth_frame(b"\x00" * 6, b"\x11" * 6, w.build_ptp_payload(w.MT_SYNC, i, 0)))
        wr.write(t2 + 1000, w.build_eth_frame(b"\x00" * 6, b"\x11" * 6, w.build_ptp_payload(w.MT_FOLLOW_UP, i, t1)))
    wr.close()
    tel = pcap_to_telemetry(pcap, scenario="netem_holdover")
    assert len(tel) == 50
    assert bool(tel["holdover"].all())


def test_linuxptp_log_parsing():
    lines = [
        "ptp4l[100.001]: master offset  -8 s2 freq -1200 path delay 512",
        "ptp4l[100.126]: master offset  42 s2 freq -1180 path delay 520",
        "ptp4l[100.376]: master offset 310 s0 freq -1000 path delay 900",
    ]
    tel = parse_linuxptp_lines(lines)
    assert len(tel) == 3
    assert validate_telemetry(tel)
    assert bool(tel["holdover"].iloc[-1]) is True   # s0 -> holdover flag
    assert tel["offset_ns"].iloc[-1] == 310.0


def _announce_payload(seq: int, clock_class: int, time_source: int) -> bytes:
    from ingest import ptp_wire as w

    payload = bytearray(w.build_ptp_payload(w.MT_ANNOUNCE, seq))
    payload.extend(b"\x00" * (64 - len(payload)))
    payload[2:4] = (64).to_bytes(2, "big")
    payload[34:44] = w.encode_timestamp(1_700_000_000_000_000_000)
    payload[44:46] = (37).to_bytes(2, "big", signed=True)
    payload[47] = 128
    payload[48] = clock_class
    payload[49] = 0x21
    payload[50:52] = (0x4321).to_bytes(2, "big")
    payload[52] = 129
    payload[53:61] = bytes.fromhex("001b19fffe123456")
    payload[61:63] = (2).to_bytes(2, "big")
    payload[63] = time_source
    return bytes(payload)


def test_announce_decoding():
    from ingest import ptp_wire as w

    msg = w.decode_ptp_payload(_announce_payload(41, clock_class=7, time_source=0xA0))
    assert msg is not None
    assert msg.msg_type == w.MT_ANNOUNCE
    assert msg.seq_id == 41
    assert msg.current_utc_offset == 37
    assert msg.grandmaster_clock_class == 7
    assert msg.grandmaster_clock_accuracy == 0x21
    assert msg.offset_scaled_log_variance == 0x4321
    assert msg.grandmaster_identity == bytes.fromhex("001b19fffe123456")
    assert msg.steps_removed == 2
    assert msg.time_source == 0xA0


def test_pcap_records_real_message_mix_and_announce_status(tmp_path):
    from ingest import ptp_wire as w

    pcap = tmp_path / "announce_mix.pcap"
    epoch = 1_700_000_000 * 10**9
    with w.PcapWriter(str(pcap)) as writer:
        for seq in range(8):
            t1 = epoch + int(seq * 0.1e9)
            t2 = t1 + 50_040
            t3 = t2 + 500_000
            t4 = t3 + 49_960
            frame = lambda payload: w.build_eth_frame(b"\x00" * 6, b"\x11" * 6, payload)
            writer.write(t2 - 10_000, frame(_announce_payload(seq, clock_class=7, time_source=0xA0)))
            writer.write(t2, frame(w.build_ptp_payload(w.MT_SYNC, seq, 0)))
            writer.write(t2 + 1_000, frame(w.build_ptp_payload(w.MT_FOLLOW_UP, seq, t1)))
            writer.write(t3, frame(w.build_ptp_payload(w.MT_DELAY_REQ, seq, 0)))
            writer.write(t3 + 100_000, frame(w.build_ptp_payload(w.MT_DELAY_RESP, seq, t4)))

    tel = pcap_to_telemetry(pcap)
    assert {"Announce", "Sync", "Follow_Up", "Delay_Req", "Delay_Resp"}.issubset(
        set(tel["ptp_msg_type"])
    )
    announce_rows = tel[tel["ptp_msg_type"] == "Announce"]
    assert not announce_rows.empty
    assert bool(announce_rows["holdover"].all())
    assert not bool(announce_rows["gnss_available"].any())
    feats = window_features(tel, window_s=0.4, step_s=0.2)
    assert (feats["msg_irregularity"] > 0).any()
    assert feats["msg_rate_mean"].nunique() > 1
    assert feats["msg_rate_std"].max() > 0


def test_sync_status_parsers():
    pmc = """
    sending: GET PARENT_DATA_SET
        grandmasterClockQuality
            clockClass 7
    sending: GET TIME_STATUS_NP
        gmPresent true
    """
    status = parse_pmc_output(pmc)
    assert status.clock_class == 7
    assert status.gm_present is True
    assert status.holdover is True
    assert status.gnss_available is False
    assert parse_synce4l_ql(["port 1 received QL-SSU-A", "port 1 selected QL-DNU"]) == 4
