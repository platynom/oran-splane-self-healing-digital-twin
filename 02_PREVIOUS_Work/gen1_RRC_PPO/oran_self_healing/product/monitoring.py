"""Production observability: decision audit log, guard drift monitor, metrics."""
import os, json, time
from collections import defaultdict, deque


class AuditLog:
    """Append-only JSONL log of every decision (for compliance / replay)."""
    def __init__(self, path="logs/decisions.jsonl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path

    def write(self, kpm, decision):
        rec = {"ts": time.time(), "kpm": kpm, "decision": decision}
        with open(self.path, "a") as f:
            f.write(json.dumps(rec, default=float) + "\n")


class DriftMonitor:
    """Tracks the rolling anomaly/adversarial flag rate. If live traffic drifts
    far from the rate seen at fit time, the guard/gate may need refitting."""
    def __init__(self, window=500, baseline_anomaly_rate=0.15):
        self.window = window
        self.baseline = baseline_anomaly_rate
        self.recent = deque(maxlen=window)

    def update(self, decision):
        self.recent.append(1 if decision.get("anomaly") else 0)

    def status(self):
        if not self.recent:
            return {"anomaly_rate": 0.0, "drift": False, "n": 0}
        rate = sum(self.recent) / len(self.recent)
        drift = abs(rate - self.baseline) > 0.25
        return {"anomaly_rate": round(rate, 3), "baseline": self.baseline,
                "drift": bool(drift), "n": len(self.recent)}


class Metrics:
    """Prometheus-style text metrics."""
    def __init__(self):
        self.counters = defaultdict(int)
        self.latencies = deque(maxlen=5000)

    def observe(self, decision):
        self.counters["decisions_total"] += 1
        self.counters[f'cause_total{{cause="{decision["cause"]}"}}'] += 1
        self.counters[f'verdict_total{{verdict="{decision["verdict"]}"}}'] += 1
        self.latencies.append(decision.get("latency_ms", 0.0))

    def render(self):
        lines = [f"{k} {v}" for k, v in self.counters.items()]
        if self.latencies:
            s = sorted(self.latencies)
            p = lambda q: s[min(len(s) - 1, int(q * len(s)))]
            lines += [f"decision_latency_ms_p50 {p(0.50)}",
                      f"decision_latency_ms_p95 {p(0.95)}",
                      f"decision_latency_ms_p99 {p(0.99)}"]
        return "\n".join(lines) + "\n"
