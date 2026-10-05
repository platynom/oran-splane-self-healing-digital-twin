"""Prospective causal, bounded-window observation. No V2 code or result is modified."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from streaming_discriminator_v1 import StreamState, observe


@dataclass
class WindowedV3State:
    v2: StreamState = field(default_factory=StreamState)
    candidate_arrivals: dict[tuple, deque[float]] = field(default_factory=lambda: defaultdict(deque))


def observe_windowed_v3(
    state: WindowedV3State,
    packet: dict,
    *,
    candidate_count: int = 4,
    candidate_window_s: float = 1.0,
    **kwargs,
) -> dict:
    """Use only arrived valid packets; invalid observations do not count, clear, or default state."""
    if candidate_count < 1 or candidate_window_s <= 0:
        raise ValueError("candidate_count and candidate_window_s must be positive")
    result = observe(state.v2, packet, **kwargs)
    result["v2_classification"] = result["classification"]
    if packet["validity"] != "VALID":
        return result
    context, timestamp = packet["context"], packet["ts"]
    arrivals = state.candidate_arrivals[context]
    while arrivals and timestamp - arrivals[0] > candidate_window_s:
        arrivals.popleft()
    if result["classification"] != "CONFIGURED_IMPAIRMENT_SUSPECT":
        result["windowed_candidate_count"] = len(arrivals)
        return result
    arrivals.append(timestamp)
    result["windowed_candidate_count"] = len(arrivals)
    if len(arrivals) >= candidate_count:
        result.update({"classification": "TRAILING_DISPERSION_WINDOWED_PERSISTENCE_OBSERVED", "reason": "prospective_causal_windowed_count"})
    else:
        result.update({"classification": "TRAILING_DISPERSION_OBSERVED", "reason": "below_prospective_windowed_count"})
    return result
