# self_healing_loop.py
import time
import numpy as np

class SelfHealingLoop:
    def __init__(self, twin_env, rl_agent, anomaly_detector, kpi_engine):
        self.env = twin_env
        self.agent = rl_agent
        self.anomaly = anomaly_detector
        self.kpi = kpi_engine
        self.episode_log = []

    def run(self, n_episodes=10):
        feature_indices = [0, 1, 2, 3, 7, 8] # rsrp, rsrq, sinr, cqi, latency_ms, packet_loss
        
        for ep in range(n_episodes):
            obs, _ = self.env.reset()
            done = False
            ep_rewards = []
            ep_actions = []
            obs_window = []
            anomalies_detected = 0
            steps = 0

            while not done:
                # Step 1: Observe and update sliding window (seq_len = 10)
                selected_obs = obs[feature_indices]
                obs_window.append(selected_obs)
                if len(obs_window) > 10:
                    obs_window.pop(0)

                # Step 2: Anomaly detection gate
                is_anomaly = False
                score = 0.0
                if len(obs_window) == 10 and self.anomaly is not None:
                    # Shape: [1, 10, 6]
                    window_arr = np.expand_dims(np.array(obs_window), axis=0)
                    is_anomaly, score = self.anomaly.detect(window_arr)
                    if is_anomaly:
                        anomalies_detected += 1

                # Step 3: Trigger healing logic based on anomaly detection
                if self.anomaly is not None:
                    if len(obs_window) < 10 or not is_anomaly:
                        # Normal behavior: perform action 5 (keep_connected)
                        action = 5
                    else:
                        # Anomaly detected: invoke RL decision engine
                        action, _ = self.agent.predict(obs, deterministic=True)
                else:
                    # If no anomaly detector is supplied, invoke RL on every step
                    action, _ = self.agent.predict(obs, deterministic=True)

                # Step 4: Execute action in digital twin environment
                obs, reward, terminated, truncated, info = self.env.step(action)
                done = terminated or truncated

                ep_rewards.append(reward)
                ep_actions.append(info['action'])
                steps += 1

            # Step 5: Log episode statistics
            print(f"Episode {ep}: Total Reward={sum(ep_rewards):.2f}, "
                  f"RLFs={self.env.rlf_count}, PingPongs={self.env.ping_pong_count}, "
                  f"Anomalies={anomalies_detected}/{steps}")
                  
            self.episode_log.append({
                "episode": ep,
                "total_reward": sum(ep_rewards),
                "rlf_count": self.env.rlf_count,
                "ping_pong_count": self.env.ping_pong_count,
                "anomalies_detected": anomalies_detected,
                "total_steps": steps,
                "actions": ep_actions
            })

        return self.episode_log