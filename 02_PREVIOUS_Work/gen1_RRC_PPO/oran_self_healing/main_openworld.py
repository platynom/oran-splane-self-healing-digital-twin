"""
Open-World Self-Healing — demonstrator.
Trains a tabular agent ONLY on seen faults, then shows three behaviours on a
mix of seen + HELD-OUT (unseen) faults:
  vanilla    : acts confidently even on unseen faults        -> harm
  shield     : holds (safe default) when unsure               -> safe, never heals
  open-world : competence-gate -> synthesize -> twin-validate -> distil (learns)
Produces the competence-growth curve (deferral on unseen drops over episodes).
"""
import os, sys, copy, json
sys.path.insert(0, "src"); sys.path.insert(0, "src/openworld")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mobility_simulator import MobilitySimulator
from dataset_generator import RRCDatasetGenerator
from twin_verifier import _immediate_reward
from ow_core import (TabularQAgent, LLMPolicySynthesizer, TwinReferee,
                     discretize, SAFE_DEFAULT)

SEED = 42; np.random.seed(SEED)
SEEN   = ["RLF", "CONGESTION"]
UNSEEN = ["NEW_INTERFERENCE", "TRAFFIC_SPIKE_UNSEEN"]
os.makedirs("outputs/openworld", exist_ok=True)

# ----------------- controlled fault signatures (KPI-separable) -----------------
def inject(df, rate=0.5, seed=0):
    rng = np.random.default_rng(seed); df = df.copy().reset_index(drop=True)
    df["failure_type"] = "None"
    types = SEEN + UNSEEN
    for i in range(len(df)):
        if rng.random() > rate:      # leave some benign
            continue
        t = types[rng.integers(len(types))]
        if t == "RLF":
            df.at[i,"rsrp"]=rng.uniform(-135,-118); df.at[i,"sinr"]=rng.uniform(-8,2)
            df.at[i,"cqi"]=rng.integers(0,3); df.at[i,"packet_loss"]=rng.uniform(0.2,0.4)
            df.at[i,"neighbor_rsrp_1"]=df.at[i,"rsrp"]+rng.uniform(4,10)
        elif t == "CONGESTION":
            df.at[i,"network_load"]=rng.uniform(0.92,1.0); df.at[i,"latency_ms"]=rng.uniform(90,200)
            df.at[i,"packet_loss"]=rng.uniform(0.15,0.4)
        elif t == "NEW_INTERFERENCE":                 # unseen: rsrp OK but sinr trashed
            df.at[i,"rsrp"]=rng.uniform(-85,-70); df.at[i,"sinr"]=rng.uniform(-8,3)
            df.at[i,"cqi"]=rng.integers(0,4); df.at[i,"packet_loss"]=rng.uniform(0.1,0.25)
            df.at[i,"neighbor_rsrp_1"]=df.at[i,"rsrp"]-rng.uniform(2,8)  # no better neighbour
        elif t == "TRAFFIC_SPIKE_UNSEEN":             # unseen: high load, LOW packet loss
            df.at[i,"network_load"]=rng.uniform(0.88,0.98); df.at[i,"latency_ms"]=rng.uniform(35,70)
            df.at[i,"packet_loss"]=rng.uniform(0.01,0.05)
        df.at[i,"failure_type"]=t
    return df

# ----------------- one decision under a given mode -----------------
def decide(mode, agent, row, tau, nmin, synth, ref):
    s = discretize(row); a = agent.best(s)
    pred = agent.predicted_value(s, a); twin_r = ref.outcome(row, a)
    # N1 (twin-grounded competence): out of competence if the agent's predicted
    # outcome disagrees with the digital twin's simulated outcome, or the state
    # was never validated before.
    novelty = abs(pred - twin_r) > tau
    out_of_comp = (agent.visits(s) == 0) or novelty
    deferred = False
    if mode == "vanilla":
        applied = a
    elif mode == "shield":
        applied = SAFE_DEFAULT if out_of_comp else a
        deferred = out_of_comp
    else:  # open-world
        if not out_of_comp:
            applied = a
        else:
            deferred = True
            cand = synth.propose(row)
            best_a, best_r = ref.validate(row, cand)
            hold_r = ref.outcome(row, SAFE_DEFAULT)
            applied = best_a if best_r > hold_r else SAFE_DEFAULT
            agent.distill(s, applied, ref.outcome(row, applied))   # N3
    realized = _immediate_reward(row, applied)
    hold = _immediate_reward(row, SAFE_DEFAULT)
    return dict(applied=applied, realized=realized, hold=hold, deferred=deferred)

def run_mode(mode, base_agent, rows, episodes, tau, nmin):
    agent = copy.deepcopy(base_agent)
    synth, ref = LLMPolicySynthesizer(), TwinReferee()
    unseen_mask = np.array([r["failure_type"] in UNSEEN for r in rows])
    per_ep = []
    for ep in range(episodes):
        recs = [decide(mode, agent, r, tau, nmin, synth, ref) for r in rows]
        u = [rc for rc, m in zip(recs, unseen_mask) if m]
        harm = np.mean([rc["realized"] < rc["hold"] - 1e-9 for rc in u])
        rec  = np.mean([rc["realized"] > rc["hold"] + 1e-9 for rc in u])
        defr = np.mean([rc["deferred"] for rc in u])
        rew  = np.mean([rc["realized"] for rc in u])
        per_ep.append(dict(episode=ep, harm=harm, recovery=rec, deferral=defr, reward=rew))
    return per_ep

print("[1/4] Generating base traffic + injecting seen & UNSEEN faults ...")
sim = MobilitySimulator(n_cells=7, n_ues=10)
df_tr = inject(RRCDatasetGenerator(sim).run(steps=500), rate=0.5, seed=1)
df_ev = inject(RRCDatasetGenerator(MobilitySimulator(7,10)).run(steps=500), rate=0.6, seed=2)
train_rows = [r for _, r in df_tr.iterrows() if r["failure_type"] in SEEN or r["failure_type"]=="None"]
eval_rows  = [r for _, r in df_ev.iterrows()]
print(f"      train rows (seen only): {len(train_rows)} | eval rows: {len(eval_rows)}")
print(f"      eval unseen faults: {sum(r['failure_type'] in UNSEEN for r in eval_rows)}")

print("[2/4] Training tabular agent on SEEN faults only ...")
agent = TabularQAgent(lr=0.5).train(train_rows, epochs=8, seed=SEED)
print(f"      learned {len(agent.Q)} states")


TAU, NMIN, EPS = 1.0, 1, 6
res = {m: run_mode(m, agent, eval_rows, EPS, TAU, NMIN)
       for m in ["vanilla", "shield", "open_world"]}

# ----------------- report -----------------
print("\n=========== OPEN-WORLD SELF-HEALING — results on UNSEEN faults ===========")
print(f"{'mode':<12}{'harm%':>9}{'recovery%':>11}{'deferral%':>11}{'mean_reward':>13}")
for m in res:
    e0, eL = res[m][0], res[m][-1]
    print(f"{m:<12}{e0['harm']*100:>9.1f}{eL['recovery']*100:>11.1f}"
          f"{eL['deferral']*100:>11.1f}{eL['reward']:>13.2f}")

# ----------------- plots -----------------
fig, ax = plt.subplots(1, 3, figsize=(16, 5))
lbl = {"vanilla":"Vanilla RL","shield":"RL + Safe-Shield","open_world":"Open-World (ours)"}
col = {"vanilla":"#c0392b","shield":"#e67e22","open_world":"#2E9E4A"}
# 1) harm vs recovery (last episode)
x = np.arange(3); w = 0.35
harm = [res[m][-1]["harm"]*100 for m in res]; rec = [res[m][-1]["recovery"]*100 for m in res]
ax[0].bar(x-w/2, harm, w, label="Harm (worse than doing nothing)", color="#c0392b")
ax[0].bar(x+w/2, rec, w, label="Recovery (healed)", color="#2E9E4A")
ax[0].set_xticks(x); ax[0].set_xticklabels([lbl[m] for m in res], fontsize=9)
ax[0].set_ylabel("% of unseen-fault steps"); ax[0].set_title("On UNSEEN faults"); ax[0].legend(fontsize=8); ax[0].grid(axis="y",alpha=.3)
# 2) mean reward on unseen (last episode)
ax[1].bar(x, [res[m][-1]["reward"] for m in res], color=[col[m] for m in res])
ax[1].set_xticks(x); ax[1].set_xticklabels([lbl[m] for m in res], fontsize=9)
ax[1].set_ylabel("Mean reward"); ax[1].set_title("Healing quality on UNSEEN faults"); ax[1].grid(axis="y",alpha=.3)
# 3) THE MONEY GRAPH: deferral rate vs episode
for m in res:
    ax[2].plot(range(EPS), [e["deferral"]*100 for e in res[m]], marker="o", label=lbl[m], color=col[m], lw=2)
ax[2].set_xlabel("Episode (repeated exposure)"); ax[2].set_ylabel("Deferral rate on unseen (%)")
ax[2].set_title("Competence growth:\nours learns to heal the unseen"); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
plt.tight_layout(); path="outputs/openworld/openworld_results.png"; plt.savefig(path,dpi=200); plt.close()
json.dump(res, open("outputs/openworld/openworld_results.json","w"), indent=2, default=float)
print(f"\n[4/4] Saved plot -> {path}\nDONE.")
