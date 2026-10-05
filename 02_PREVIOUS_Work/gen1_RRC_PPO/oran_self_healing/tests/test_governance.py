import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from aml_guard import AMLGuard
from llm_governor import LLMGovernor
from twin_verifier import TwinVerifier
import pandas as pd, numpy as np

def _benign(n=400):
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "rsrp": rng.uniform(-90, -60, n), "rsrq": rng.uniform(-15, -8, n),
        "sinr": np.clip(rng.uniform(18, 30, n), -10, 30), "cqi": rng.integers(12, 16, n),
        "neighbor_rsrp_1": rng.uniform(-95, -70, n), "network_load": rng.uniform(0.2, 0.6, n),
        "latency_ms": rng.uniform(10, 25, n), "packet_loss": rng.uniform(0.01, 0.04, n),
    })

GUARD = AMLGuard().fit(_benign())
GOV = LLMGovernor(backend="offline")
VER = TwinVerifier()

def _ctx(row, rl_action):
    is_adv, sc, bd = GUARD.analyze(row)
    appr, fc = VER.verify(row, rl_action); fc["approved_action"] = appr
    snap = {k: row[k] for k in ["rsrp","rsrq","sinr","cqi","packet_loss","network_load","latency_ms"]}
    return dict(snapshot=snap, anomaly_flag=True, anomaly_score=9.9,
                aml_flag=is_adv, aml_score=sc, aml_breakdown=bd,
                rl_action=rl_action, twin_forecast=fc)

def test_spoofed_rsrp_is_vetoed():
    row = dict(rsrp=-128, rsrq=-12, sinr=30, cqi=15, neighbor_rsrp_1=-120,
               network_load=0.4, latency_ms=18, packet_loss=0.02,
               failure_type="None", traffic_type="Data", rrc_state="RRC_CONNECTED")
    d = GOV.decide(_ctx(row, 0))
    assert d["cause"] == "adversarial" and d["action"] == 5

def test_fake_congestion_is_vetoed():
    row = dict(rsrp=-70, rsrq=-12, sinr=30, cqi=15, neighbor_rsrp_1=-90,
               network_load=0.97, latency_ms=180, packet_loss=0.02,
               failure_type="None", traffic_type="Data", rrc_state="RRC_CONNECTED")
    d = GOV.decide(_ctx(row, 4))
    assert d["cause"] == "adversarial" and d["action"] == 5

def test_genuine_rlf_is_healed():
    row = dict(rsrp=-123, rsrq=-18, sinr=1.5, cqi=1, neighbor_rsrp_1=-95,
               network_load=0.4, latency_ms=45, packet_loss=0.35,
               failure_type="RLF", traffic_type="Data", rrc_state="RRC_CONNECTED")
    d = GOV.decide(_ctx(row, 0))
    assert d["cause"] == "genuine_fault"

def test_healthy_snapshot_holds():
    row = dict(rsrp=-65, rsrq=-10, sinr=28, cqi=15, neighbor_rsrp_1=-85,
               network_load=0.3, latency_ms=15, packet_loss=0.02,
               failure_type="None", traffic_type="Data", rrc_state="RRC_CONNECTED")
    d = GOV.decide(_ctx(row, 0))
    assert d["cause"] == "benign" and d["action"] == 5
