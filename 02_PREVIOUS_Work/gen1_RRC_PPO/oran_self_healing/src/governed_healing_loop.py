# governed_healing_loop.py
# ---------------------------------------------------------------------------
# The integrated closed loop. Runs ONE chronological pass over the twin and
# supports three modes so we can compare like-for-like:
#
#   mode="rl_only"        : PPO acts on every step (no gate, no governance)
#   mode="anomaly_gated"  : LSTM gate -> PPO   (the ORIGINAL system)
#   mode="governed"       : LSTM gate -> AML guard -> LLM governor -> twin verify
#                           -> commit / override / veto      (THE NOVELTY)
#
# Returns a summary dict plus per-step records used to compute security metrics.
# ---------------------------------------------------------------------------
import numpy as np

FEATURE_IDX = [0, 1, 2, 3, 7, 8]   # rsrp, rsrq, sinr, cqi, latency_ms, packet_loss
HARMFUL_ACTIONS = {0, 1, 4}
SAFE_DEFAULT = 5


class GovernedHealingLoop:
    def __init__(self, env, agent, anomaly=None, aml_guard=None,
                 governor=None, verifier=None, mode="governed"):
        self.env = env
        self.agent = agent
        self.anomaly = anomaly
        self.aml_guard = aml_guard
        self.governor = governor
        self.verifier = verifier
        self.mode = mode

    def _snapshot(self, row):
        return {
            "rsrp": row["rsrp"], "rsrq": row["rsrq"], "sinr": row["sinr"],
            "cqi": row["cqi"], "packet_loss": row["packet_loss"],
            "network_load": row["network_load"], "latency_ms": row["latency_ms"],
        }

    @staticmethod
    def _gt_cause(row):
        if bool(row.get("is_adversarial", False)):
            return "adversarial"
        if row.get("failure_type", "None") != "None":
            return "genuine_fault"
        return "benign"

    def run(self):
        obs, _ = self.env.reset()
        window, records, rewards = [], [], []
        done = False

        while not done:
            row = self.env.df.iloc[self.env.current_idx]
            gt_cause = self._gt_cause(row)

            # --- anomaly gate (shared by gated + governed) ---
            window.append(obs[FEATURE_IDX])
            if len(window) > 10:
                window.pop(0)
            anomaly_flag, ascore = False, 0.0
            if self.anomaly is not None and len(window) == 10:
                arr = np.expand_dims(np.array(window), axis=0)
                anomaly_flag, ascore = self.anomaly.detect(arr)

            # --- RL proposal ---
            rl_action, _ = self.agent.predict(obs, deterministic=True)
            rl_action = int(rl_action)

            gov_cause, verdict, confidence, reason = None, None, None, None
            aml_flag, aml_score = False, 0.0

            if self.mode == "rl_only":
                final_action = rl_action

            elif self.mode == "anomaly_gated":
                final_action = rl_action if anomaly_flag else SAFE_DEFAULT

            else:  # governed
                if not anomaly_flag:
                    final_action, gov_cause, verdict = SAFE_DEFAULT, "benign", "commit"
                    confidence, reason = 0.9, "no anomaly"
                else:
                    aml_flag, aml_score, bd = self.aml_guard.analyze(row)
                    # twin counterfactual forecast for the RL proposal
                    appr, fc = self.verifier.verify(row, rl_action)
                    fc["approved_action"] = appr
                    decision = self.governor.decide({
                        "snapshot": self._snapshot(row),
                        "anomaly_flag": anomaly_flag, "anomaly_score": ascore,
                        "aml_flag": aml_flag, "aml_score": aml_score,
                        "aml_breakdown": bd, "rl_action": rl_action,
                        "twin_forecast": fc,
                    })
                    final_action = int(decision["action"])
                    gov_cause = decision["cause"]
                    verdict = decision["verdict"]
                    confidence = decision["confidence"]
                    reason = decision["reason"]

            obs, reward, terminated, truncated, info = self.env.step(final_action)
            done = terminated or truncated
            rewards.append(reward)

            records.append({
                "gt_cause": gt_cause, "gov_cause": gov_cause,
                "rl_action": rl_action, "final_action": final_action,
                "anomaly_flag": bool(anomaly_flag), "aml_flag": bool(aml_flag),
                "verdict": verdict, "confidence": confidence,
                "attack_target_action": int(row.get("attack_target_action", -1)),
                "reward": float(reward), "reason": reason,
            })

        summary = {
            "mode": self.mode,
            "total_reward": float(np.sum(rewards)),
            "mean_reward": float(np.mean(rewards)),
            "steps": len(records),
        }
        return summary, records
