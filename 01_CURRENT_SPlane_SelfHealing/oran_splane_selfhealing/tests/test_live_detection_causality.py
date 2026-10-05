"""S9: falsifiable checks that the frozen detector is usable live.

Each test can fail. They assert properties a live detector must have:
no lookahead, no end-of-file dependence, no identity/label leakage, bounded state.
"""
from __future__ import annotations
import hashlib, sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
PILOT = ROOT / "outputs" / "empirical_software_network_pilot_v1"
sys.path.insert(0, str(PILOT))
sys.path.insert(0, str(ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"))

from streaming_discriminator_v1 import packet_from_frame, StreamState, observe, tick  # noqa: E402
from streaming_discriminator_v3_nonoverlap import NonoverlapV3State, observe_nonoverlap_v3  # noqa: E402
from ingest.ptp_wire import read_pcap  # noqa: E402

CAPTURES = [PILOT / "v4_runs" / f"20260913_v4_{t}" / "capture.pcap" for t in ("n1", "b1", "s1", "d1")]


def _frames(path: Path):
    return [(ts / 1e9, fr) for ts, fr in read_pcap(str(path))]


def _run(frames, capture_id: str):
    state = NonoverlapV3State()
    out = []
    for ts, fr in frames:
        r = observe_nonoverlap_v3(state, packet_from_frame(capture_id, ts, fr))
        out.append((r["classification"], r["reason"], tuple(e["type"] for e in r["events"])))
    return out


def test_no_lookahead_prefix_determinism():
    """Outputs for the first k packets must not depend on packets after k."""
    for cap in CAPTURES:
        frames = _frames(cap)
        cid = hashlib.sha256(cap.read_bytes()).hexdigest()
        full = _run(frames, cid)
        for k in (1, 17, 113, len(frames) // 2, len(frames) - 1):
            if k < 1 or k >= len(frames):
                continue
            assert _run(frames[:k], cid) == full[:k], f"lookahead detected in {cap.name} at k={k}"


def test_no_end_of_file_dependence():
    """Appending unrelated trailing frames must not change earlier outputs."""
    for cap in CAPTURES[:2]:
        frames = _frames(cap)
        cid = hashlib.sha256(cap.read_bytes()).hexdigest()
        base = _run(frames, cid)
        last_ts = frames[-1][0]
        extended = frames + [(last_ts + 0.1, b"\x00" * 60), (last_ts + 0.2, frames[-1][1])]
        assert _run(extended, cid)[: len(base)] == base, f"end-of-file dependence in {cap.name}"


def test_capture_identity_does_not_change_classifications():
    """capture_id partitions context only; it must not alter the decision sequence."""
    for cap in CAPTURES:
        frames = _frames(cap)
        a = [row[0] for row in _run(frames, "A" * 64)]
        b = [row[0] for row in _run(frames, "live-stream-0")]
        assert a == b, f"capture identity leaked into classifications for {cap.name}"


def test_no_filename_or_scenario_reaches_the_engine():
    """The only engine inputs are a stream id, a timestamp and raw bytes."""
    import inspect
    params = list(inspect.signature(packet_from_frame).parameters)
    assert params == ["capture_id", "ts", "frame"], params
    src = (PILOT / "streaming_discriminator_v1.py").read_text() + (
        PILOT / "streaming_discriminator_v3_nonoverlap.py").read_text()
    for banned in ("scenario", "baseline", "netem", "benign", "intervention", "v4_runs", "filename"):
        assert banned not in src.lower(), f"engine source references '{banned}'"


def test_timestamp_regression_is_rejected_not_crashed():
    state = StreamState()
    frames = _frames(CAPTURES[0])[:40]
    for ts, fr in frames:
        observe(state, packet_from_frame("x", ts, fr))
    ts, fr = frames[-1]
    r = observe(state, packet_from_frame("x", ts - 5.0, fr))
    assert r["validity"] == "TIMESTAMP_REGRESSION" and r["reason"] == "arrival_order_regression"


def test_state_is_bounded_over_a_long_stream():
    """Repeating a capture many times must not grow per-context pending state without bound."""
    frames = _frames(CAPTURES[0])
    state = NonoverlapV3State()
    for repeat in range(6):
        offset = repeat * 100.0
        for ts, fr in frames:
            observe_nonoverlap_v3(state, packet_from_frame("x", ts + offset, fr))
    assert len(state.v2.sync_to_followup) <= 64, len(state.v2.sync_to_followup)
    assert all(len(v) <= 8 for v in state.v2.paired_gaps.values())
    assert all(len(v) <= 8 for v in state.block_gaps.values())


def test_tick_emits_silence_without_fabricating_a_packet():
    """Live use needs a clock tick during arrival gaps; it must not invent packets."""
    state = StreamState()
    frames = _frames(CAPTURES[2])
    last_ts = frames[0][0]
    for ts, fr in frames[:200]:
        observe(state, packet_from_frame("x", ts, fr))
        last_ts = ts
    events = tick(state, "x", 0, 2, 0, last_ts + 5.0)
    assert any(e["type"] == "SOURCE_ANNOUNCE_SILENCE_OBSERVED" for e in events), events
