"""In-process throughput + latency benchmark for the decision engine."""
import os, sys, time, argparse
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
from engine import GovernanceEngine
from persistence import load_artifacts
from lite_components import LitePolicyAgent

def run(n=20000):
    gate, guard, _ = load_artifacts("artifacts")
    eng = GovernanceEngine(gate, guard, LitePolicyAgent())
    rng = np.random.default_rng(0)
    kpms = []
    for i in range(n):
        spoof = rng.random() < 0.06
        kpms.append(dict(ue_id=i % 50,
            rsrp=(-128 if spoof else rng.uniform(-95, -60)),
            sinr=(30 if spoof else rng.uniform(18, 30)), cqi=15,
            neighbor_rsrp_1=rng.uniform(-95, -70),
            network_load=rng.uniform(0.2, 0.6),
            latency_ms=rng.uniform(10, 25), packet_loss=rng.uniform(0.01, 0.04)))
    t0 = time.time()
    lat = []
    for k in kpms:
        d = eng.decide(k); lat.append(d["latency_ms"])
    dt = time.time() - t0
    lat.sort()
    p = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))]
    print(f"decisions        : {n}")
    print(f"wall time        : {dt:.2f}s")
    print(f"throughput       : {n/dt:,.0f} decisions/sec")
    print(f"latency p50/p95/p99 (ms): {p(.5):.3f} / {p(.95):.3f} / {p(.99):.3f}")
    print(f"cause breakdown  : {dict(eng.stats)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("-n", type=int, default=20000)
    run(ap.parse_args().n)
