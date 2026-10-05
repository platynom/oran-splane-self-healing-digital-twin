import gymnasium as gym
import numpy as np
from gymnasium import spaces

class RRCDigitalTwin(gym.Env):
    """
    State: [rsrp, rsrq, sinr, cqi, neighbor_rsrp1, neighbor_rsrp2,
            network_load, latency, packet_loss, rrc_state_enc,
            ue_speed, ping_pong_count, rlf_count]
    Actions: 0=trigger_handover, 1=delay_handover, 2=modify_a3_offset,
             3=adjust_report_interval, 4=idle_transition, 5=keep_connected
    """

    def __init__(self, dataset_df, shuffle=True):
        super().__init__()

        self.df = dataset_df.reset_index(drop=True)
        self.shuffle = shuffle
        self.current_idx = 0

        self.ping_pong_count = 0
        self.rlf_count = 0

        self.prev_serving_cell = None
        self.prev_prev_cell = None      # <-- Added

        # Observation space
        self.observation_space = spaces.Box(
            low=np.array(
                [-140,-20,-10,0,-140,-140,0,0,0,0,0,0,0],
                dtype=np.float32
            ),
            high=np.array(
                [-44,-3,30,15,-44,-44,1,500,1,3,30,50,50],
                dtype=np.float32
            )
        )

        # Action space
        self.action_space = spaces.Discrete(6)

    def _get_obs(self):
        row = self.df.iloc[self.current_idx]

        rrc_enc = {
            "RRC_IDLE":0,
            "RRC_INACTIVE":1,
            "RRC_CONNECTED":2
        }.get(row["rrc_state"],2)

        return np.array([
            row["rsrp"],
            row["rsrq"],
            row["sinr"],
            row["cqi"],
            row["neighbor_rsrp_1"],
            row["neighbor_rsrp_2"],
            row["network_load"],
            row["latency_ms"],
            row["packet_loss"],
            rrc_enc,
            row["ue_speed"],
            self.ping_pong_count,
            self.rlf_count
        ], dtype=np.float32)

    def step(self, action):

        row = self.df.iloc[self.current_idx]

        reward = 0
        terminated = False

        # -------------------------
        # Improved Ping-Pong Detection
        # Detect only A→B→A pattern
        # -------------------------
        curr_cell = row["serving_cell"]

        if (
            self.prev_prev_cell is not None
            and self.prev_serving_cell is not None
            and curr_cell == self.prev_prev_cell
            and curr_cell != self.prev_serving_cell
        ):
            self.ping_pong_count += 1

        self.prev_prev_cell = self.prev_serving_cell
        self.prev_serving_cell = curr_cell

        # -------------------------
        # Detect RLF
        # -------------------------
        if row["failure_type"] == "RLF":
            self.rlf_count += 1
            reward -= 10

        action_names = [
            "trigger_handover",
            "delay_handover",
            "modify_threshold",
            "adjust_report_interval",
            "idle_transition",
            "keep_connected"
        ]

        # -------------------------
        # Action Rewards
        # -------------------------
        if action == 0:

            if row["rsrp"] < -100 and row["neighbor_rsrp_1"] > row["rsrp"] + 3:
                reward += 5
            else:
                reward -= 2

        elif action == 1:

            if row["rsrp"] > -95:
                reward += 2
            else:
                reward -= 3

        elif action == 2:

            reward += 1

        elif action == 3:

            if row["network_load"] > 0.7:
                reward += 0.5

        elif action == 4:

            if (
                row["rrc_state"] == "RRC_CONNECTED"
                and row["traffic_type"] == "IoT"
            ):
                reward += 3
            else:
                reward -= 1

        elif action == 5:

            if row["sinr"] > 10 and row["latency_ms"] < 20:
                reward += 2

        # -------------------------
        # QoE penalties
        # -------------------------
        reward -= row["packet_loss"] * 5
        reward -= max(0, row["latency_ms"] - 20) * 0.05
        reward -= self.ping_pong_count * 0.1

        # -------------------------
        # Reward Normalization
        # -------------------------
        reward = np.clip(reward, -10, 10)

        self.current_idx += 1

        if self.current_idx >= len(self.df):
            terminated = True

        obs = (
            self._get_obs()
            if not terminated
            else np.zeros(13, dtype=np.float32)
        )

        return obs, reward, terminated, False, {
            "action": action_names[action]
        }

    def reset(self, seed=None, options=None):

        super().reset(seed=seed)

        # Shuffle or sort dataset depending on the mode
        if self.shuffle:
            self.df = self.df.sample(frac=1).reset_index(drop=True)
        else:
            self.df = self.df.sort_values(by=["ue_id", "timestamp"]).reset_index(drop=True)

        self.current_idx = 0
        self.ping_pong_count = 0
        self.rlf_count = 0

        self.prev_serving_cell = None
        self.prev_prev_cell = None

        return self._get_obs(), {}