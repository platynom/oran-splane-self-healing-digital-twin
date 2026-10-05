from __future__ import annotations
import importlib.util
import sys
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("stream_v1", ROOT / "outputs/empirical_software_network_pilot_v1/streaming_discriminator_v1.py")
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = m; SPEC.loader.exec_module(m)
sys.modules["streaming_discriminator_v1"] = m
PILOT = ROOT / "outputs" / "empirical_software_network_pilot_v1"
V3SPEC = importlib.util.spec_from_file_location("stream_v3", PILOT / "streaming_discriminator_v3_nonoverlap.py")
assert V3SPEC and V3SPEC.loader
v3 = importlib.util.module_from_spec(V3SPEC); sys.modules[V3SPEC.name] = v3; V3SPEC.loader.exec_module(v3)
sys.modules["streaming_discriminator_v3_nonoverlap"] = v3
sys.path.insert(0, str(PILOT))
EVALSPEC = importlib.util.spec_from_file_location("evaluate_v2", PILOT / "evaluate_v2_repeated.py")
assert EVALSPEC and EVALSPEC.loader
ev = importlib.util.module_from_spec(EVALSPEC); sys.modules[EVALSPEC.name] = ev; EVALSPEC.loader.exec_module(ev)
EVAL3SPEC = importlib.util.spec_from_file_location("evaluate_v3", PILOT / "evaluate_v3_nonoverlap.py")
assert EVAL3SPEC and EVAL3SPEC.loader
ev3 = importlib.util.module_from_spec(EVAL3SPEC); sys.modules[EVAL3SPEC.name] = ev3; EVAL3SPEC.loader.exec_module(ev3)

def p(ts, msg, seq=1, source="0011223344550001", length=64, domain=0, capture="x"):
    return {"capture_id":capture, "ts":ts, "validity":"VALID", "declared_length":length, "message_type":msg, "sequence_id":seq, "context":(capture,0,2,domain,source)}

def test_prefix_invariance_and_no_future_announce_silence() -> None:
    prefix = [p(0.0, 11), p(0.1, 0, 7), p(0.11, 8, 7)]
    a, b = m.StreamState(), m.StreamState()
    left = [m.observe(a, x) for x in prefix]
    right = [m.observe(b, x) for x in prefix + [p(3.0, 11, source="aa")]][:3]
    assert left == right
    assert left[0]["classification"] == "WARMUP"

def test_context_boundaries_and_invalid_length_are_unknown() -> None:
    s = m.StreamState(); m.observe(s, p(0.0, 11, domain=1)); m.observe(s, p(0.1, 11, domain=2))
    assert m.observe(s, p(0.2, 11, length=40))["classification"] == "UNKNOWN"
    assert m.packet_from_frame("x", 0.0, b"\0" * 10)["validity"] == "NOT_PTP"

def test_silence_event_survives_every_message_branch_and_reappearance_clears_it() -> None:
    for message in (0, 1, 8, 9, 11):
        s = m.StreamState(); m.observe(s, p(0.0, 11, source="a"))
        out = m.observe(s, p(1.0, message, source="b"))
        assert any(e["type"] == "SOURCE_ANNOUNCE_SILENCE_OBSERVED" for e in out["events"])
        again = m.observe(s, p(1.1, message, seq=2, source="b"))
        assert not any(e["type"] == "SOURCE_ANNOUNCE_SILENCE_OBSERVED" for e in again["events"])
        returned = m.observe(s, p(1.2, 11, source="a"))
        assert any(e["type"] == "SOURCE_ANNOUNCE_REAPPEARED" for e in returned["events"])

def test_timestamp_regression_sequence_reuse_and_tick_are_explicit() -> None:
    s = m.StreamState(); m.observe(s, p(1.0, 0, 3));
    assert m.observe(s, p(1.1, 0, 3))["reason"] == "sequence_reuse_before_followup"
    assert m.observe(s, p(.9, 1))["validity"] == "TIMESTAMP_REGRESSION"
    s = m.StreamState(); m.observe(s, p(0, 11, source="a"))
    assert m.tick(s, "x", 0, 2, 0, 1.0)[0]["type"] == "SOURCE_ANNOUNCE_SILENCE_OBSERVED"

def test_message_body_length_rejected_before_any_state_mutation() -> None:
    raw = bytearray(14 + 34); raw[12:14] = b"\x88\xf7"; raw[14] = 0; raw[15] = 2; raw[16:18] = (34).to_bytes(2,"big")
    invalid = m.packet_from_frame("x", 2.0, bytes(raw))
    assert invalid["validity"] == "TRUNCATED_MESSAGE_BODY"
    state = m.StreamState(); m.observe(state, p(1.0,11)); before=copy.deepcopy(state)
    assert m.observe(state,invalid)["classification"] == "UNKNOWN"
    assert state == before

def test_trim_and_tick_are_scoped_to_capture_group() -> None:
    s=m.StreamState(); m.observe(s,p(0,0,5,capture="a")); m.observe(s,p(100,0,6,capture="b"))
    assert (p(0,0,5,capture="a")["context"],5) in s.sync_to_followup
    before=copy.deepcopy(s); out=m.tick(s,"a",0,2,0,-1)
    assert out[0]["type"] == "TIMESTAMP_REGRESSION" and s == before

def test_frozen_rule_needs_only_trailing_pairs() -> None:
    s = m.StreamState()
    out = None
    for i in range(8):
        m.observe(s, p(i / 10, 0, i))
        out = m.observe(s, p(i / 10 + (0.001 if i % 2 else 0.0), 8, i), impairment_std_threshold_s=0.0001)
    assert out["classification"] == "CONFIGURED_IMPAIRMENT_SUSPECT"

def _nonoverlap_block(state, base, gaps, source="a"):
    results=[]
    for i,gap in enumerate(gaps):
        v3.observe_nonoverlap_v3(state,p(base + i / 10,0,i,source=source),block_size=8,std_threshold_s=.0001,high_block_count=2,high_block_window_s=3)
        results.append(v3.observe_nonoverlap_v3(state,p(base + i / 10 + gap,8,i,source=source),block_size=8,std_threshold_s=.0001,high_block_count=2,high_block_window_s=3))
    return results

def test_nonoverlap_v3_single_outlier_does_not_repeat_across_rolling_windows() -> None:
    state=v3.NonoverlapV3State()
    high=_nonoverlap_block(state,0,[0]*7+[.001])[-1]
    assert high["classification"] == "NONOVERLAPPING_HIGH_DISPERSION_BLOCK_OBSERVED"
    # Eight normal pairs after the outlier are a separate low-dispersion block, not seven repeats of it.
    normal=_nonoverlap_block(state,.8,[0]*8)[-1]
    assert normal["classification"] == "NONOVERLAPPING_BLOCK_OBSERVED"
    assert normal["high_block_window_count"] == 1

def test_nonoverlap_v3_requires_two_disjoint_high_blocks_and_preserves_invalid() -> None:
    state=v3.NonoverlapV3State()
    assert _nonoverlap_block(state,0,[0]*7+[.001])[-1]["classification"] == "NONOVERLAPPING_HIGH_DISPERSION_BLOCK_OBSERVED"
    out=_nonoverlap_block(state,.8,[0]*7+[.001])[-1]
    assert out["classification"] == "NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED"
    # An invalid packet neither becomes an observation nor changes V3 state.
    invalid={"capture_id":"x","ts":2,"validity":"TRUNCATED_MESSAGE_BODY"}
    before=(dict(state.block_gaps),{key:list(value) for key,value in state.high_block_arrivals.items()})
    assert v3.observe_nonoverlap_v3(state,invalid)["classification"] == "UNKNOWN"
    assert (dict(state.block_gaps),{key:list(value) for key,value in state.high_block_arrivals.items()}) == before

def test_nonoverlap_v3_context_and_unknown_results_do_not_leak_state() -> None:
    state=v3.NonoverlapV3State()
    assert _nonoverlap_block(state,0,[0]*7+[.001],source="a")[-1]["classification"] == "NONOVERLAPPING_HIGH_DISPERSION_BLOCK_OBSERVED"
    # A high block from a different source cannot complete A's two-block condition.
    assert _nonoverlap_block(state,.8,[0]*7+[.001],source="b")[-1]["classification"] == "NONOVERLAPPING_HIGH_DISPERSION_BLOCK_OBSERVED"
    before=(dict(state.block_gaps),{key:list(value) for key,value in state.high_block_arrivals.items()})
    # Returned validity, rather than packet input validity, signals timestamp regression.
    regression=v3.observe_nonoverlap_v3(state,p(.1,1,99,source="b"))
    assert regression["validity"] == "TIMESTAMP_REGRESSION"
    unmatched=v3.observe_nonoverlap_v3(state,p(1.7,8,777,source="b"))
    assert unmatched["classification"] == "UNKNOWN" and unmatched["reason"] == "unmatched_or_expired_followup"
    v3.observe_nonoverlap_v3(state,p(1.8,0,778,source="b"))
    reused=v3.observe_nonoverlap_v3(state,p(1.9,0,778,source="b"))
    assert reused["classification"] == "UNKNOWN" and reused["reason"] == "sequence_reuse_before_followup"
    assert (dict(state.block_gaps),{key:list(value) for key,value in state.high_block_arrivals.items()}) == before

def test_evaluator_rejects_frozen_input_hash_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(ev, "sha", lambda _path: "0" * 64)
    try:
        ev.verify_frozen_inputs()
        assert False, "mismatched protocol hash must fail before replay"
    except RuntimeError as exc:
        assert "frozen input hash mismatch" in str(exc)

def test_v3_evaluator_rejects_frozen_input_hash_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(ev3, "sha256", lambda _path: "0" * 64)
    try:
        ev3.verify_frozen_inputs()
        assert False, "V3 must not replay changed frozen inputs"
    except RuntimeError as exc:
        assert "frozen input hash mismatch" in str(exc)

def test_v3_manifest_integrity_detects_modified_capture_and_log() -> None:
    manifest={name: "a" * 64 for name in ev3.REQUIRED_MANIFEST_ENTRIES}
    actual={name: "a" * 64 for name in manifest}
    assert ev3.manifest_mismatches(manifest, actual) == {}
    actual["capture.pcap"] = "b" * 64
    assert ev3.manifest_mismatches(manifest, actual)["capture.pcap"] == "hash_mismatch"
    actual["capture.pcap"] = "a" * 64; actual["slave.log"] = None
    assert ev3.manifest_mismatches(manifest, actual)["slave.log"] == "missing"

def test_v3_manifest_integrity_rejects_false_cached_validation() -> None:
    assert not ev3.cached_verification_valid({"status":"STRUCTURALLY_COMPLETE", "manifest_hashes_match":{"capture.pcap":False}})
    assert not ev3.cached_verification_valid({"status":"INCOMPLETE", "manifest_hashes_match":{"capture.pcap":True}})
    assert ev3.cached_verification_valid({"status":"STRUCTURALLY_COMPLETE", "manifest_hashes_match":{"capture.pcap":True}})
