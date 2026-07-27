import os
import pandas as pd
import matplotlib.pyplot as plt

class Evaluator:
    def __init__(self, baseline_log, healed_log):
        self.baseline = pd.DataFrame(baseline_log)
        self.healed = pd.DataFrame(healed_log)

    def report(self):
        metrics = {
            "RLF Reduction (%)": self._pct_improvement("rlf_count"),
            "Ping-Pong Reduction (%)": self._pct_improvement("ping_pong_count"),
            "Reward Improvement (%)": self._pct_improvement(
                "total_reward",
                higher_is_better=True
            ),
        }

        print("\n========== Evaluation Report ==========")
        for k, v in metrics.items():
            print(f"{k}: {v:.2f}%")
        print("=======================================\n")

        return metrics

    def _pct_improvement(self, col, higher_is_better=False):
        b = self.baseline[col].mean()
        h = self.healed[col].mean()

        if higher_is_better:
            return ((h - b) / max(abs(b), 1e-9)) * 100

        return ((b - h) / max(abs(b), 1e-9)) * 100

    def plot(self):

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        plots = [
            ("total_reward", "Cumulative Reward"),
            ("rlf_count", "RLF Count"),
            ("ping_pong_count", "Ping-Pong Count")
        ]

        for ax, (col, title) in zip(axes, plots):

            ax.plot(
                self.baseline[col],
                label="Baseline",
                linewidth=2
            )

            ax.plot(
                self.healed[col],
                label="Self-Healed",
                linewidth=2
            )

            ax.set_title(title)
            ax.set_xlabel("Episode")
            ax.grid(True)
            ax.legend()

        plt.tight_layout()

        os.makedirs("outputs", exist_ok=True)

        save_path = "outputs/evaluation_results.png"

        plt.savefig(save_path, dpi=300)

        print(f"Graph saved to: {save_path}")

        # IMPORTANT:
        # Close figure instead of waiting forever
        plt.close(fig)