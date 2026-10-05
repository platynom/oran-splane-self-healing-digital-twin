from __future__ import annotations

from collections import defaultdict, deque


class BaselineAnomalyDetector:
    """Rolling baseline detector that acts as the first AI-like anomaly module."""

    def __init__(self, warmup: int = 20, window: int = 30) -> None:
        self.warmup = warmup
        self.window = window
        self.history: dict[tuple[str, str], deque[dict[str, float]]] = defaultdict(lambda: deque(maxlen=window))
        self.metrics = [
            "latency_ms",
            "jitter_ms",
            "packet_loss_pct",
            "prb_util_pct",
            "handover_fail_pct",
            "edge_delay_ms",
            "backhaul_delay_ms",
            "bler_pct",
        ]

    def score(self, row: dict[str, object]) -> tuple[float, list[str]]:
        key = (str(row["cell_id"]), str(row["service_class"]))
        hist = self.history[key]
        current = {metric: float(row[metric]) for metric in self.metrics}
        if len(hist) < self.warmup:
            hist.append(current)
            return 0.0, []

        reasons: list[str] = []
        total = 0.0
        for metric in self.metrics:
            values = [item[metric] for item in hist]
            mu = sum(values) / len(values)
            variance = sum((value - mu) ** 2 for value in values) / len(values)
            sigma = variance ** 0.5 or 0.001
            z = (current[metric] - mu) / sigma
            if z > 2.8:
                reasons.append(f"{metric}_z={z:.1f}")
                total += min(4.0, z)
        hist.append(current)
        score = min(1.0, total / 12.0)
        return round(score, 4), reasons
