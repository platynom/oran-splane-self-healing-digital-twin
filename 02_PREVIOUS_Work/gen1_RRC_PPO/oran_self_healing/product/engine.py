"""
GovernanceEngine - the productised decision core.

Wraps the four novelty components (anomaly gate, AML guard, LLM governor,
twin verifier) behind a single streaming API:

    engine.decide(kpm)  ->  {cause, action, action_name, verdict, confidence, reason}

`kpm` is one KPM report dict for a UE. The engine keeps a per-UE rolling window
so it works on a live stream (E2/KPM indications), not just offline replay.
"""
import os, sys, time
from collections import defaultdict, deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
from aml_guard import AMLGuard
from llm_governor import LLMGovernor, ACTION_NAMES, SAFE_DEFAULT
from twin_verifier import TwinVerifier

# gate feature order (matches src pipeline)
GATE_FEATURES = ["rsrp", "rsrq", "sinr", "cqi", "latency_ms", "packet_loss"]
RRC_ENC = {"RRC_IDLE": 0, "RRC_INACTIVE": 1, "RRC_CONNECTED": 2}


def kpm_to_obs(k):
    """Build the 13-dim observation vector the RL policy expects."""
    return np.array([
        k.get("rsrp", -80), k.get("rsrq", -12), k.get("sinr", 20),
        k.get("cqi", 12), k.get("neighbor_rsrp_1", -90),
        k.get("neighbor_rsrp_2", -95), k.get("network_load", 0.4),
        k.get("latency_ms", 20), k.get("packet_loss", 0.02),
        RRC_ENC.get(k.get("rrc_state", "RRC_CONNECTED"), 2),
        k.get("ue_speed", 3), k.get("ping_pong_count", 0), k.get("rlf_count", 0),
    ], dtype=float)


class GovernanceEngine:
    def __init__(self, gate, guard, agent, governor=None, verifier=None,
                 seq_len=10, safe_default=SAFE_DEFAULT):
        self.gate = gate
        self.guard = guard
        self.agent = agent
        self.governor = governor or LLMGovernor(backend="offline")
        self.verifier = verifier or TwinVerifier()
        self.seq_len = seq_len
        self.safe_default = safe_default
        self._windows = defaultdict(lambda: deque(maxlen=seq_len))
        self.stats = defaultdict(int)

    def _snapshot(self, k):
        return {kk: float(k.get(kk, 0.0)) for kk in
                ["rsrp", "rsrq", "sinr", "cqi", "packet_loss",
                 "network_load", "latency_ms"]}

    def decide(self, kpm):
        t0 = time.time()
        ue = kpm.get("ue_id", 0)
        # normalise with safe defaults for fields guard/verifier require
        kpm = {
            "failure_type": "None", "traffic_type": "Data",
            "rrc_state": "RRC_CONNECTED", "network_load": 0.4,
            "neighbor_rsrp_1": kpm.get("rsrp", -80) - 5,
            "neighbor_rsrp_2": kpm.get("rsrp", -80) - 10,
            **kpm,
        }
        obs = kpm_to_obs(kpm)
        win = self._windows[ue]
        win.append([kpm.get(f, 0.0) for f in GATE_FEATURES])

        # anomaly gate (needs a full window)
        anomaly_flag, ascore = False, 0.0
        if self.gate is not None and len(win) == self.seq_len:
            arr = np.expand_dims(np.array(win), axis=0)
            anomaly_flag, ascore = self.gate.detect(arr)

        # RL proposal
        rl_action, _ = self.agent.predict(obs, deterministic=True)
        rl_action = int(rl_action)

        if not anomaly_flag:
            decision = dict(cause="benign", action=self.safe_default,
                            verdict="commit", confidence=0.9,
                            reason="No anomaly; maintaining connection.")
        else:
            aml_flag, aml_score, bd = self.guard.analyze(kpm)
            appr, fc = self.verifier.verify(kpm, rl_action)
            fc["approved_action"] = appr
            d = self.governor.decide({
                "snapshot": self._snapshot(kpm), "anomaly_flag": True,
                "anomaly_score": ascore, "aml_flag": aml_flag,
                "aml_score": aml_score, "aml_breakdown": bd,
                "rl_action": rl_action, "twin_forecast": fc})
            decision = dict(d)

        act = int(decision["action"])
        self.stats["decisions"] += 1
        self.stats[f"cause_{decision['cause']}"] += 1
        return {
            "ue_id": ue,
            "cause": decision["cause"],
            "action": act,
            "action_name": ACTION_NAMES[act],
            "verdict": decision["verdict"],
            "confidence": round(float(decision["confidence"]), 3),
            "rl_proposed": ACTION_NAMES[rl_action],
            "anomaly": bool(anomaly_flag),
            "reason": decision["reason"],
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }
