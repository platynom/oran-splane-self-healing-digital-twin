# rl_agent.py — using Stable-Baselines3
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

def train_rl_agent(env, total_timesteps=50000):
    check_env(env)
    
    try:
        import tensorboard
        tb_log = "./logs/ppo_rrc"
    except ImportError:
        tb_log = None
        print("TensorBoard is not installed. Disabling TensorBoard logging.")

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        tensorboard_log=tb_log
    )
    model.learn(total_timesteps=total_timesteps)
    model.save("rrc_ppo_agent")
    return model