"""
main_governed.py  -  Adversarial-aware, digital-twin-verified LLM-governed
                     self-healing loop for O-RAN RRC management.

Pipeline
--------
1. Digital twin -> synthetic RRC/KPM stream
2. Inject genuine faults (RLF, congestion, ping-pong, ...)
3. Inject ADVERSARIAL (spoofed/poisoned) KPM reports
4. Train LSTM anomaly gate + AML physical-consistency guard (benign only)
5. Load PPO healing agent
6. Run 3 configs on the SAME data:
       rl_only  |  anomaly_gated (original)  |  governed (ours)
7. Security evaluation + plots
8. Real-data validation on OAI/FlexRIC KPM trace
"""
import sys, os, json
sys.path.insert(0, "src")
import numpy as np
import pandas as pd

from mobility_simulator import MobilitySimulator
from dataset_generator import RRCDatasetGenerator
from failure_injector import FailureInjector
from adversarial_injector import AdversarialInjector
from fault_coupling import couple_faults
from aml_guard import AMLGuard
from llm_governor import LLMGovernor
from twin_verifier import TwinVerifier
from rrc_twin_env import RRCDigitalTwin
from governed_healing_loop import GovernedHealingLoop
import governed_evaluation as gev
from real_kpm_validation import run_real_validation

SEED = 42
np.random.seed(SEED)
os.makedirs("outputs", exist_ok=True)

print("\n[1/8] Generating digital-twin KPM stream ...")
sim = MobilitySimulator(n_cells=7, n_ues=10)
df = RRCDatasetGenerator(sim).run(steps=900)
print(f"      {len(df)} records")

print("[2/8] Injecting genuine faults ...")
df = FailureInjector().inject(df, sim.cells)
df = couple_faults(df, seed=SEED)   # make genuine faults physically coherent

print("[3/8] Injecting adversarial / spoofed KPM reports ...")
df = AdversarialInjector(attack_rate=0.06, seed=SEED).inject(df)
df.to_csv("data/rrc_dataset_adversarial.csv", index=False)
gt = df.apply(AdversarialInjector.ground_truth_cause, axis=1)
print("      cause distribution:", dict(gt.value_counts()))

print("[4/8] Training anomaly gate + AML guard on benign data ...")
benign = df[(df.failure_type == "None") & (~df.is_adversarial)].copy()
try:
    from anomaly_detector import AnomalyDetector          # real LSTM-AE (torch)
    anomaly = AnomalyDetector(threshold_percentile=95, epochs=6, batch_size=128)
    anomaly.train(benign)
    print("      gate: LSTM autoencoder (torch)")
except Exception as e:
    from lite_components import LiteAnomalyGate            # torch-free fallback
    anomaly = LiteAnomalyGate(threshold_percentile=95).train(benign)
    print(f"      gate: PCA-reconstruction surrogate (torch unavailable: {type(e).__name__})")
guard = AMLGuard(contamination_pct=97).fit(benign)

print("[5/8] Loading healing agent ...")
try:
    from stable_baselines3 import PPO                       # real trained PPO
    agent = PPO.load("rrc_ppo_agent", device="cpu")
    print("      agent: PPO (rrc_ppo_agent.zip)")
except Exception as e:
    from lite_components import LitePolicyAgent             # torch-free fallback
    agent = LitePolicyAgent()
    print(f"      agent: KPI-reactive policy surrogate (SB3 unavailable: {type(e).__name__})")

governor = LLMGovernor(backend="offline")   # flip to backend="claude" with a key
verifier = TwinVerifier(margin=0.5)

print("[6/8] Running 3 configurations on identical data ...")
configs = {
    "rl_only":       dict(anomaly=None,    aml=None,  gov=None,      ver=None),
    "anomaly_gated": dict(anomaly=anomaly, aml=None,  gov=None,      ver=None),
    "governed":      dict(anomaly=anomaly, aml=guard, gov=governor,  ver=verifier),
}
results, all_records = {}, {}
for mode, c in configs.items():
    env = RRCDigitalTwin(df, shuffle=False)
    loop = GovernedHealingLoop(env, agent, anomaly=c["anomaly"], aml_guard=c["aml"],
                               governor=c["gov"], verifier=c["ver"], mode=mode)
    summary, records = loop.run()
    results[mode] = gev.compute_metrics(records)
    all_records[mode] = records
    print(f"      {mode:<14} steps={summary['steps']} mean_reward={summary['mean_reward']:.3f}")

print("[7/8] Building security evaluation + plots ...")
gev.print_report(results)
conf = gev.confusion(all_records["governed"])
plot_path = gev.plot_comparison(results, conf, save_dir="outputs")
print(f"      plot -> {plot_path}")
print("\n      Governor cause-classification confusion matrix:")
print(conf.to_string())

print("\n[8/8] Real-data validation on OAI/FlexRIC KPM trace ...")
real = run_real_validation()
print("      ", real)

# persist everything
out = {"synthetic_metrics": results,
       "confusion_matrix": conf.to_dict(),
       "real_data_validation": real}
with open("outputs/governed_results.json", "w") as f:
    json.dump(out, f, indent=2, default=float)
print("\nSaved outputs/governed_results.json")
print("\nDONE.")
