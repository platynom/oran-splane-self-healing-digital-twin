# adversarial_injector.py
# ---------------------------------------------------------------------------
# NOVELTY COMPONENT (1/4): Adversarial KPM injector.
#
# Distinguishes THREE classes of "anomaly" that hit the self-healing loop:
#   - benign            : normal operation
#   - genuine_fault     : a real radio problem (RLF, congestion, ping-pong...)
#                         where the physically-coupled KPMs move TOGETHER.
#   - adversarial       : a crafted / spoofed / poisoned KPM report where ONE
#                         observable is manipulated to mislead the agent while
#                         the physically-coupled observables stay inconsistent.
#
# The attacker's goal is to make the RL healing agent take a HARMFUL RRC action
# (unnecessary handover -> ping-pong, idle_transition -> drop an active session,
# or delay_handover when a real handover was actually needed).
#
# This is the raw material the LLM governor must learn to separate: a real fault
# to heal vs. an attack to neutralise.
# ---------------------------------------------------------------------------
import numpy as np
import pandas as pd

# RRC actions (must match rrc_twin_env.py)
#   0=trigger_handover 1=delay_handover 2=modify_threshold
#   3=adjust_report_interval 4=idle_transition 5=keep_connected
HARMFUL_ACTIONS = {0, 1, 4}   # actions an attacker tries to provoke

ATTACK_TYPES = [
    "spoof_rsrp_collapse",   # fake RLF  -> provoke trigger_handover / idle
    "neighbor_spoof",        # fake better neighbor -> provoke handover -> ping-pong
    "false_congestion",      # fake load spike -> provoke idle / report change
    "gradient_evasion",      # small multi-feature nudge -> slip past detector
]


class AdversarialInjector:
    """Injects adversarial KPM manipulations into an already fault-injected
    dataframe. Adds three columns:
        is_adversarial (bool), attack_type (str), attack_target_action (int)
    Genuine faults are left physically consistent; adversarial rows break the
    physical coupling on purpose.
    """

    def __init__(self, attack_rate=0.06, seed=None):
        self.attack_rate = attack_rate
        self.rng = np.random.default_rng(seed)

    def inject(self, df):
        df = df.copy().reset_index(drop=True)
        df["is_adversarial"] = False
        df["attack_type"] = "none"
        df["attack_target_action"] = -1

        n = len(df)
        for i in range(n):
            # never overwrite a genuine fault row -> keeps the two classes clean
            if df.at[i, "failure_type"] != "None":
                continue
            if self.rng.random() >= self.attack_rate:
                continue

            atk = self.rng.choice(ATTACK_TYPES)
            if atk == "spoof_rsrp_collapse":
                # Report an RLF-like RSRP collapse, but LEAVE sinr/cqi/latency
                # healthy -> physically impossible -> a real RLF would tank all.
                df.at[i, "rsrp"] = self.rng.uniform(-138, -122)
                # neighbor looks marginally better to bait a handover
                df.at[i, "neighbor_rsrp_1"] = df.at[i, "rsrp"] + self.rng.uniform(3, 8)
                target = 0  # trigger_handover

            elif atk == "neighbor_spoof":
                # Inflate a neighbor's RSRP far above the (healthy) serving cell
                df.at[i, "neighbor_rsrp_1"] = df.at[i, "rsrp"] + self.rng.uniform(15, 30)
                df.at[i, "neighbor_rsrp_1"] = min(df.at[i, "neighbor_rsrp_1"], -44)
                target = 0  # trigger_handover -> ping-pong

            elif atk == "false_congestion":
                # Fake a load/latency spike but keep packet_loss & cqi healthy
                df.at[i, "network_load"] = self.rng.uniform(0.9, 1.0)
                df.at[i, "latency_ms"] = df.at[i, "latency_ms"] * self.rng.uniform(4, 8)
                target = 4  # idle_transition / disruptive reconfig

            else:  # gradient_evasion: small coordinated nudges to flip detector
                df.at[i, "rsrp"] += self.rng.uniform(-6, -3)
                df.at[i, "sinr"] += self.rng.uniform(-3, -1)
                df.at[i, "latency_ms"] *= self.rng.uniform(1.4, 2.0)
                df.at[i, "neighbor_rsrp_1"] += self.rng.uniform(4, 8)
                target = 1  # delay_handover (suppress a needed handover)

            df.at[i, "is_adversarial"] = True
            df.at[i, "attack_type"] = atk
            df.at[i, "attack_target_action"] = int(target)

        # clip back into physical ranges
        df["rsrp"] = df["rsrp"].clip(-140, -44)
        df["neighbor_rsrp_1"] = df["neighbor_rsrp_1"].clip(-140, -44)
        df["network_load"] = df["network_load"].clip(0, 1)
        return df

    @staticmethod
    def ground_truth_cause(row):
        """Return the true cause label for evaluation."""
        if bool(row.get("is_adversarial", False)):
            return "adversarial"
        if row.get("failure_type", "None") != "None":
            return "genuine_fault"
        return "benign"


if __name__ == "__main__":
    df = pd.read_csv("data/rrc_dataset.csv")
    adv = AdversarialInjector(attack_rate=0.06, seed=42).inject(df)
    print(adv["attack_type"].value_counts())
    print("adversarial rows:", int(adv["is_adversarial"].sum()), "/", len(adv))
