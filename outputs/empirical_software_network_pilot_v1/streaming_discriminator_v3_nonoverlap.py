"""Prospective causal observation using disjoint Sync/Follow_Up blocks only."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
import math

from streaming_discriminator_v1 import StreamState, observe


@dataclass
class NonoverlapV3State:
    v2: StreamState = field(default_factory=StreamState)
    block_gaps: dict[tuple, list[float]] = field(default_factory=lambda: defaultdict(list))
    high_block_arrivals: dict[tuple, deque[float]] = field(default_factory=lambda: defaultdict(deque))


def observe_nonoverlap_v3(
    state: NonoverlapV3State,
    packet: dict,
    *,
    block_size: int = 8,
    std_threshold_s: float = .00016,
    high_block_count: int = 2,
    high_block_window_s: float = 3.0,
    **kwargs,
) -> dict:
    """Consume one arrival; each gap participates in at most one V3 dispersion block."""
    if block_size < 2 or high_block_count < 1 or high_block_window_s <= 0:
        raise ValueError("invalid non-overlapping block configuration")
    result = observe(state.v2, packet, impairment_std_threshold_s=std_threshold_s, **kwargs)
    result["v2_classification"] = result["classification"]
    if packet["validity"] != "VALID" or "gap_s" not in result:
        return result
    context, timestamp = packet["context"], packet["ts"]
    high = state.high_block_arrivals[context]
    while high and timestamp - high[0] > high_block_window_s:
        high.popleft()
    block = state.block_gaps[context]
    block.append(result["gap_s"])
    result["nonoverlap_block_count"] = len(block)
    if len(block) < block_size:
        return result
    mean = sum(block) / block_size
    std = math.sqrt(sum((value - mean) ** 2 for value in block) / block_size)
    # Clear immediately: a later block cannot reuse any one gap from this block.
    state.block_gaps[context] = []
    result.update({"nonoverlap_block_count": block_size, "nonoverlap_block_std_s": std})
    if std < std_threshold_s:
        result.update({"classification": "NONOVERLAPPING_BLOCK_OBSERVED", "reason": "bounded_block_below_dispersion_threshold", "high_block_window_count": len(high)})
        return result
    high.append(timestamp)
    result["high_block_window_count"] = len(high)
    if len(high) >= high_block_count:
        result.update({"classification": "NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED", "reason": "prospective_causal_nonoverlap_block_count"})
    else:
        result.update({"classification": "NONOVERLAPPING_HIGH_DISPERSION_BLOCK_OBSERVED", "reason": "below_prospective_high_block_count"})
    return result
