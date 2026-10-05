"""Prospective V3 causal persistence observation; V2 is retained unchanged."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from streaming_discriminator_v1 import StreamState, observe


@dataclass
class V3State:
    v2: StreamState = field(default_factory=StreamState)
    trailing_dispersion_count: dict[tuple, int] = field(default_factory=lambda: defaultdict(int))


def observe_v3(state: V3State, packet: dict, *, persistence_count: int = 16, **kwargs) -> dict:
    """Return only arrival-prefix information; no scenario label or future packet is consumed."""
    if persistence_count < 1:
        raise ValueError("persistence_count must be positive")
    result = observe(state.v2, packet, **kwargs)
    result["v2_classification"] = result["classification"]
    if result["classification"] != "CONFIGURED_IMPAIRMENT_SUSPECT":
        return result
    context = packet["context"]  # capture, transport/version/domain, and sourcePortIdentity
    state.trailing_dispersion_count[context] += 1
    result["persistence_count"] = state.trailing_dispersion_count[context]
    if result["persistence_count"] >= persistence_count:
        result.update({"classification": "TRAILING_DISPERSION_PERSISTENCE_OBSERVED", "reason": "prospective_causal_persistence_rule"})
    else:
        result.update({"classification": "TRAILING_DISPERSION_OBSERVED", "reason": "below_prospective_persistence_count"})
    return result
