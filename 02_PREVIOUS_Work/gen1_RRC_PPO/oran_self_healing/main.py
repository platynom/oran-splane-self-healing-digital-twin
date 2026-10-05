import sys
sys.path.insert(0, 'src')
import numpy as np

print("Step 1: Imports started")

from mobility_simulator import MobilitySimulator
from dataset_generator import RRCDatasetGenerator
from failure_injector import FailureInjector
from rrc_twin_env import RRCDigitalTwin
from kpi_engine import KPIEngine
from rl_agent import train_rl_agent
from self_healing_loop import SelfHealingLoop
from evaluation import Evaluator
from anomaly_detector import AnomalyDetector

print("Step 2: Imports completed")


# ----------------------------------------------------
# Random Baseline Agent
# ----------------------------------------------------
class RandomAgent:
    def __init__(self, action_space):
        self.action_space = action_space

    def predict(self, obs, deterministic=False):
        return self.action_space.sample(), None


# ----------------------------------------------------
# Step 1 - Generate Mobility Data
# ----------------------------------------------------
print("\nStep 3: Generating mobility simulation...")

sim = MobilitySimulator(n_cells=7, n_ues=20)
gen = RRCDatasetGenerator(sim)

df = gen.run(steps=2000)

print(f"Step 4: Dataset generated ({len(df)} records)")


# ----------------------------------------------------
# Step 2 - Inject Failures
# ----------------------------------------------------
print("Step 5: Injecting failures...")

injector = FailureInjector()
df_failed = injector.inject(df, sim.cells)

print("Step 6: Failures injected")

df_failed.to_csv("data/rrc_dataset.csv", index=False)

print(f"Step 7: Dataset saved ({len(df_failed)} records)")


# ----------------------------------------------------
# Step 2.5 - Train Anomaly Detector (Milestone 4)
# ----------------------------------------------------
print("\nStep 7.5: Training Anomaly Detector...")

anomaly_detector = AnomalyDetector(threshold_percentile=95, epochs=10, batch_size=128)
anomaly_detector.train(df)

print("Step 7.6: Anomaly Detector Ready")


# ----------------------------------------------------
# Step 3 - Random Baseline Environment Setup
# ----------------------------------------------------
print("\nStep 8: Creating baseline environment...")

env = RRCDigitalTwin(df_failed, shuffle=False)

print("Step 9: Creating Random Agent...")

baseline_agent = RandomAgent(env.action_space)

print("Step 10: Baseline ready")


# ----------------------------------------------------
# Step 4 - Train RL Agent
# ----------------------------------------------------
print("Step 11: Creating RL Environment...")

env2 = RRCDigitalTwin(df_failed, shuffle=False)

print("Step 12: Starting RL Training (50000 timesteps)...")

# Change back to 200000 if your professor specifically wants it.
healed_agent = train_rl_agent(
    env2,
    total_timesteps=50000
)

print("Step 13: RL Training Completed")


# ----------------------------------------------------
# Step 5 - Evaluate Healed Agent (Milestone 5 Closed-Loop)
# ----------------------------------------------------
print("Step 14: Evaluating Self-Healing Agent...")

kpi = KPIEngine()

# shuffle=False ensures chronological evaluation for sequence-based anomaly detection
env3 = RRCDigitalTwin(df_failed, shuffle=False)

loop = SelfHealingLoop(
    env3,
    healed_agent,
    anomaly_detector,
    kpi
)

healed_log = loop.run(n_episodes=5)

print("Step 15: Self-Healing Evaluation Completed")


# ----------------------------------------------------
# Step 6 - Evaluate Random Baseline (With Anomaly Detector Gate)
# ----------------------------------------------------
print("Step 16: Evaluating Random Baseline...")

env4 = RRCDigitalTwin(df_failed, shuffle=False)

loop_b = SelfHealingLoop(
    env4,
    baseline_agent,
    anomaly_detector,
    kpi
)

baseline_log = loop_b.run(n_episodes=5)

print("Step 17: Baseline Evaluation Completed")


# ----------------------------------------------------
# Step 7 - Compare Results
# ----------------------------------------------------
print("Step 18: Generating Evaluation Report...")

evaluator = Evaluator(
    baseline_log,
    healed_log
)

metrics = evaluator.report()

print("Step 19: Report Generated Successfully")

print("Step 19.5: Saving Evaluation Graph...")

evaluator.plot()

print("Step 20: Graph Saved Successfully")


# ----------------------------------------------------
# Final Message
# ----------------------------------------------------
print("\n========================================")
print("   O-RAN SELF-HEALING PROJECT COMPLETE")
print("========================================")

print("\nOutputs Generated:")
print("[OK] data/rrc_dataset.csv")
print("[OK] outputs/evaluation_results.png")

print("\nEvaluation Metrics:")
for k, v in metrics.items():
    print(f"[OK] {k}: {v:.2f}%")

avg_anom_healed = np.mean([ep["anomalies_detected"] for ep in healed_log])
avg_anom_base = np.mean([ep["anomalies_detected"] for ep in baseline_log])
print(f"[OK] Avg anomalies detected per episode (Self-Healed): {avg_anom_healed:.1f}")
print(f"[OK] Avg anomalies detected per episode (Baseline): {avg_anom_base:.1f}")

print("\nProgram Finished Successfully.")