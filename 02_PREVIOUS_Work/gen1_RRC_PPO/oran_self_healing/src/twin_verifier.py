# twin_verifier.py
# ---------------------------------------------------------------------------
# NOVELTY COMPONENT (3/4): Digital-twin counterfactual verifier (post-decision
# shield). This is what makes the digital twin LOAD-BEARING at decision time
# instead of being just a data generator.
#
# Before committing the RL agent's proposed RRC action on a GENUINE fault, we
# roll the twin's reward dynamics forward for (a) the proposed action and
# (b) the safe default (keep_connected), and only commit the proposed action if
# the twin predicts it is genuinely better. Otherwise we override to the safe
# default. This catches cases where the RL policy would act destructively.
#
# It mirrors the reward model in rrc_twin_env.py so the forecast is consistent
# with the environment the agent was trained on.
# ---------------------------------------------------------------------------
import numpy as np

SAFE_DEFAULT = 5  # keep_connected


def _immediate_reward(row, action, ping_pong_count=0):
    """Pure reproduction of the per-step reward in rrc_twin_env.step()."""
    reward = 0.0
    if row["failure_type"] == "RLF":
        reward -= 10

    if action == 0:      # trigger_handover
        if row["rsrp"] < -100 and row["neighbor_rsrp_1"] > row["rsrp"] + 3:
            reward += 5
        else:
            reward -= 2
    elif action == 1:    # delay_handover
        reward += 2 if row["rsrp"] > -95 else -3
    elif action == 2:    # modify_threshold
        reward += 1
    elif action == 3:    # adjust_report_interval
        if row["network_load"] > 0.7:
            reward += 0.5
    elif action == 4:    # idle_transition
        if row["rrc_state"] == "RRC_CONNECTED" and row["traffic_type"] == "IoT":
            reward += 3
        else:
            reward -= 1
    elif action == 5:    # keep_connected
        if row["sinr"] > 10 and row["latency_ms"] < 20:
            reward += 2

    reward -= row["packet_loss"] * 5
    reward -= max(0, row["latency_ms"] - 20) * 0.05
    reward -= ping_pong_count * 0.1
    return float(np.clip(reward, -10, 10))


class TwinVerifier:
    def __init__(self, margin=0.5):
        # require the proposed action to beat the safe default by `margin`
        self.margin = margin

    def verify(self, row, proposed_action, ping_pong_count=0):
        """Return (approved_action, forecast_dict)."""
        r_prop = _immediate_reward(row, int(proposed_action), ping_pong_count)
        r_safe = _immediate_reward(row, SAFE_DEFAULT, ping_pong_count)

        # extra caution: a handover that isn't clearly justified risks ping-pong
        pingpong_risk = (
            int(proposed_action) == 0
            and not (row["rsrp"] < -100 and row["neighbor_rsrp_1"] > row["rsrp"] + 3)
        )

        approved = int(proposed_action)
        reason = "commit"
        if pingpong_risk or (r_prop < r_safe + self.margin):
            approved = SAFE_DEFAULT
            reason = "override_to_safe_default"

        forecast = {
            "reward_proposed": round(r_prop, 2),
            "reward_safe_default": round(r_safe, 2),
            "pingpong_risk": bool(pingpong_risk),
            "decision": reason,
        }
        return approved, forecast
