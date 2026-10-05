"""
Open-World Self-Healing — core mechanism (torch-free).

Implements the three novelty claims from OPEN_WORLD_NOVELTY.md:
  N1  Twin-grounded competence gate  (agent-vs-twin outcome disagreement)
  N2  LLM policy synthesis for unseen faults  (offline reasoning; API-swappable)
  N3  Twin-validated distillation -> competence expands over time
Reuses the digital-twin reward model from src/twin_verifier.py.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from twin_verifier import _immediate_reward   # the digital-twin outcome model

N_ACTIONS = 6
SAFE_DEFAULT = 5   # keep_connected

# ---- state discretisation (agent sees only KPIs, never the fault label) ----
def discretize(row):
    def b(v, edges):
        return int(np.digitize([v], edges)[0])
    return (
        b(row["rsrp"], [-125,-115,-105,-98,-90,-82,-74]),
        b(row["sinr"], [-2,2,6,10,14,18,24]),
        b(row["cqi"], [1,3,5,8,11,14]),
        b(row["network_load"], [0.4,0.6,0.75,0.85,0.92,0.97]),
        b(row["latency_ms"], [20,35,55,90,150]),
        b(row["packet_loss"], [0.03,0.07,0.12,0.2,0.3]),
    )


class TabularQAgent:
    """Contextual-bandit tabular learner (offline rows are i.i.d.; gamma=0)."""
    def __init__(self, lr=0.5):
        self.Q = {}          # state -> np.array(N_ACTIONS)
        self.N = {}          # state -> visit count
        self.lr = lr

    def _ensure(self, s):
        if s not in self.Q:
            self.Q[s] = np.zeros(N_ACTIONS)
            self.N[s] = 0

    def train(self, rows, epochs=6, seed=0):
        rng = np.random.default_rng(seed)
        idx = np.arange(len(rows))
        for _ in range(epochs):
            rng.shuffle(idx)
            for i in idx:
                row = rows[i]; s = discretize(row)
                self._ensure(s)
                a = int(rng.integers(N_ACTIONS)) if rng.random() < 0.25 else int(self.Q[s].argmax())
                r = _immediate_reward(row, a)
                self.Q[s][a] += self.lr * (r - self.Q[s][a])
                self.N[s] += 1
        return self

    def best(self, s):
        self._ensure(s)
        return int(self.Q[s].argmax())

    def predicted_value(self, s, a):
        self._ensure(s)
        return float(self.Q[s][a])

    def visits(self, s):
        return self.N.get(s, 0)

    # ---- N3: distil a twin-validated action into the policy ----
    def distill(self, s, a, twin_reward):
        self._ensure(s)
        self.Q[s][a] = max(self.Q[s][a], twin_reward)  # imprint the good action
        self.N[s] += 1                                  # competence rises with exposure


class LLMPolicySynthesizer:
    """N2: propose candidate healing actions for an unseen fault from first
    principles (offline reasoning; swap for the Claude API to get free-form
    policies). Returns a small candidate set the twin then validates."""
    def propose(self, row):
        cands = {SAFE_DEFAULT, 2}                      # always: hold, modify_threshold
        if row["rsrp"] < -100 and row["neighbor_rsrp_1"] > row["rsrp"] + 3:
            cands.add(0)                               # justified handover
        if row["neighbor_rsrp_1"] > row["rsrp"] + 6:
            cands.add(0)
        if row["network_load"] > 0.85:
            cands.add(3)                               # ease reporting under load
        if row["sinr"] < 5:
            cands.add(2)                               # threshold tweak vs interference
        if row.get("rrc_state") == "RRC_CONNECTED" and row.get("traffic_type") == "IoT":
            cands.add(4)
        return sorted(cands)


class TwinReferee:
    """N1 + validation: the digital twin as an online outcome oracle."""
    @staticmethod
    def outcome(row, a):
        return _immediate_reward(row, a)

    @staticmethod
    def validate(row, candidates):
        """Return (best_action, best_reward) among candidates vs safe default."""
        scored = [(a, _immediate_reward(row, a)) for a in candidates]
        best_a, best_r = max(scored, key=lambda kv: kv[1])
        return best_a, best_r
