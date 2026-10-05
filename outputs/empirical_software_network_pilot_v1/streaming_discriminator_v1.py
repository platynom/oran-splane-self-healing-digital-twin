"""Causal packet-arrival observations for the isolated pilot; no health/attack/recovery labels."""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass, field
import math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"))
from ingest.ptp_wire import read_pcap  # noqa: E402

ANNOUNCE, SYNC, FOLLOW_UP = 11, 0, 8
SUPPORTED = {SYNC, 1, FOLLOW_UP, 9, ANNOUNCE}
MINIMUM_MESSAGE_LENGTH = {SYNC: 44, 1: 44, FOLLOW_UP: 44, 9: 54, ANNOUNCE: 64}

@dataclass
class StreamState:
    last_announce: dict[tuple, float] = field(default_factory=dict)
    silence_reported: set[tuple] = field(default_factory=set)
    sync_to_followup: dict[tuple, float] = field(default_factory=dict)
    paired_gaps: dict[tuple, deque] = field(default_factory=lambda: defaultdict(deque))
    last_arrival: dict[tuple, float] = field(default_factory=dict)

def packet_from_frame(capture_id: str, ts: float, frame: bytes) -> dict:
    if len(frame) < 14 or frame[12:14] != b"\x88\xf7": return {"capture_id":capture_id,"ts":ts,"validity":"NOT_PTP"}
    ptp = frame[14:]
    if len(ptp) < 34: return {"capture_id":capture_id,"ts":ts,"validity":"TRUNCATED_HEADER"}
    declared = int.from_bytes(ptp[2:4], "big")
    if declared < 34 or declared > len(ptp): return {"capture_id":capture_id,"ts":ts,"validity":"INVALID_DECLARED_LENGTH"}
    version, transport, domain, msg = ptp[1] & 15, ptp[0] >> 4, ptp[4], ptp[0] & 15
    if version != 2: return {"capture_id":capture_id,"ts":ts,"validity":"UNSUPPORTED_VERSION"}
    if msg not in SUPPORTED: return {"capture_id":capture_id,"ts":ts,"validity":"UNSUPPORTED_MESSAGE"}
    if declared < MINIMUM_MESSAGE_LENGTH[msg]: return {"capture_id":capture_id,"ts":ts,"validity":"TRUNCATED_MESSAGE_BODY"}
    source = ptp[20:30].hex(); context = (capture_id, transport, version, domain, source)
    return {"capture_id":capture_id,"ts":ts,"validity":"VALID","declared_length":declared,"message_type":msg,"sequence_id":int.from_bytes(ptp[30:32],"big"),"context":context}

def _group(ctx): return ctx[:4]
def _trim(state: StreamState, group: tuple, ts: float, pair_age_s: float, window_s: float) -> None:
    for key, start in list(state.sync_to_followup.items()):
        if _group(key[0]) == group and ts - start > pair_age_s: del state.sync_to_followup[key]
    for ctx, values in state.paired_gaps.items():
        if _group(ctx) == group:
            while values and ts - values[0][0] > window_s: values.popleft()

def observe(state: StreamState, packet: dict, announce_silence_s: float = .75, impairment_std_threshold_s: float = .00016,
            pair_age_s: float = 1.0, trailing_window_s: float = 2.0, max_pairs: int = 8) -> dict:
    """Consume one arrival. Silence is arrival-driven; call `tick` if no packets arrive."""
    result = {"ts":packet["ts"],"validity":packet["validity"],"classification":"UNKNOWN","reason":"invalid_or_insufficient","events":[]}
    if packet["validity"] != "VALID": return result
    ctx, ts, msg = packet["context"], packet["ts"], packet["message_type"]; group = _group(ctx)
    previous_arrival = state.last_arrival.get(group)
    if previous_arrival is not None and ts < previous_arrival:
        result.update({"validity":"TIMESTAMP_REGRESSION","reason":"arrival_order_regression"}); return result
    state.last_arrival[group] = ts; _trim(state, group, ts, pair_age_s, trailing_window_s)
    # Independent, deduplicated event; never overwrites primary packet classification.
    for key, last in state.last_announce.items():
        if _group(key) == group and key != ctx and key not in state.silence_reported and ts-last >= announce_silence_s:
            state.silence_reported.add(key); result["events"].append({"type":"SOURCE_ANNOUNCE_SILENCE_OBSERVED","context":key,"elapsed_s":ts-last})
    if msg == ANNOUNCE:
        if packet["declared_length"] < 64: result.update({"classification":"UNKNOWN","reason":"truncated_announce"}); return result
        previous = state.last_announce.get(ctx); state.last_announce[ctx] = ts
        if ctx in state.silence_reported: state.silence_reported.remove(ctx); result["events"].append({"type":"SOURCE_ANNOUNCE_REAPPEARED","context":ctx})
        if previous is None: result.update({"classification":"WARMUP","reason":"first_valid_announce"})
        else: result.update({"classification":"ANNOUNCE_OBSERVED","reason":"per_source_gap","announce_gap_s":ts-previous})
        return result
    if msg == SYNC:
        key=(ctx,packet["sequence_id"])
        if key in state.sync_to_followup: result.update({"classification":"UNKNOWN","reason":"sequence_reuse_before_followup"})
        else: state.sync_to_followup[key]=ts; result.update({"classification":"WARMUP","reason":"sync_waiting_for_followup"})
    elif msg == FOLLOW_UP:
        start=state.sync_to_followup.pop((ctx,packet["sequence_id"]),None)
        if start is None: result.update({"classification":"UNKNOWN","reason":"unmatched_or_expired_followup"})
        else:
            values=state.paired_gaps[ctx]; values.append((ts,ts-start))
            while len(values)>max_pairs: values.popleft()
            gaps=[x[1] for x in values]; std=math.sqrt(sum((x-sum(gaps)/len(gaps))**2 for x in gaps)/len(gaps)) if len(gaps)>1 else None
            result.update({"classification":"OBSERVATION","reason":"causal_sync_followup_gap","gap_s":ts-start,"window_count":len(gaps),"trailing_std_s":std})
            if len(gaps)==max_pairs and std is not None and std>=impairment_std_threshold_s: result.update({"classification":"CONFIGURED_IMPAIRMENT_SUSPECT","reason":"frozen_trailing_dispersion_rule"})
    else: result.update({"classification":"NOT_APPLICABLE","reason":"message_type_not_used"})
    return result

def tick(state: StreamState, capture_id: str, transport: int, version: int, domain: int, ts: float, announce_silence_s: float=.75,
         pair_age_s: float=1.0, trailing_window_s: float=2.0) -> list[dict]:
    """Optional caller-provided time tick; no fabricated packet. Enables silence detection during arrival gaps."""
    group=(capture_id,transport,version,domain); events=[]; previous=state.last_arrival.get(group)
    if previous is not None and ts < previous: return [{"type":"TIMESTAMP_REGRESSION","group":group,"ts":ts}]
    state.last_arrival[group]=ts; _trim(state,group,ts,pair_age_s,trailing_window_s)
    for key,last in state.last_announce.items():
        if _group(key)==group and key not in state.silence_reported and ts-last>=announce_silence_s:
            state.silence_reported.add(key); events.append({"type":"SOURCE_ANNOUNCE_SILENCE_OBSERVED","context":key,"elapsed_s":ts-last})
    return events

def stream_pcap(capture_id: str, path: Path) -> list[dict]:
    state, rows=StreamState(),[]
    for ts_ns,frame in read_pcap(str(path)): rows.append(observe(state,packet_from_frame(capture_id,ts_ns/1e9,frame)))
    return rows
