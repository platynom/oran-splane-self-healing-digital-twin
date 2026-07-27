# governed_evaluation.py
# Security-aware evaluation for the governed self-healing loop.
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HARMFUL_ACTIONS = {0, 1, 4}
CAUSES = ["benign", "genuine_fault", "adversarial"]


def compute_metrics(records):
    df = pd.DataFrame(records)
    adv = df[df.gt_cause == "adversarial"]
    ben = df[df.gt_cause == "benign"]
    fault = df[df.gt_cause == "genuine_fault"]

    def harmful_frac(sub):
        if len(sub) == 0:
            return 0.0
        return float(sub.final_action.isin(HARMFUL_ACTIONS).mean())

    m = {
        "attack_success_rate": harmful_frac(adv),
        "false_heal_rate": harmful_frac(ben),
        "genuine_fault_reward": float(fault.reward.mean()) if len(fault) else 0.0,
        "mean_reward": float(df.reward.mean()),
        "n_adversarial": int(len(adv)),
        "n_benign": int(len(ben)),
        "n_fault": int(len(fault)),
    }
    m["attack_neutralised"] = 1.0 - m["attack_success_rate"]

    if df.gov_cause.notna().any():
        labeled = df[df.gov_cause.notna()]
        m["cause_accuracy"] = float((labeled.gov_cause == labeled.gt_cause).mean())
        flagged = labeled[labeled.anomaly_flag]
        if len(flagged):
            m["cause_acc_on_flagged"] = float(
                (flagged.gov_cause == flagged.gt_cause).mean())
        if len(adv):
            m["adversarial_recall"] = float((adv.gov_cause == "adversarial").mean())
    return m


def confusion(records):
    df = pd.DataFrame(records)
    df = df[df.gov_cause.notna()]
    mat = pd.DataFrame(0, index=CAUSES, columns=CAUSES)
    for _, r in df.iterrows():
        if r.gt_cause in CAUSES and r.gov_cause in CAUSES:
            mat.loc[r.gt_cause, r.gov_cause] += 1
    return mat


def plot_comparison(results, confusion_mat, save_dir="outputs"):
    os.makedirs(save_dir, exist_ok=True)
    modes = list(results.keys())
    labels = {"rl_only": "RL-only", "anomaly_gated": "Anomaly-Gated\n(original)",
              "governed": "Governed\n(ours)"}
    x = np.arange(len(modes))
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    asr = [results[m]["attack_success_rate"] * 100 for m in modes]
    fhr = [results[m]["false_heal_rate"] * 100 for m in modes]
    w = 0.35
    axes[0].bar(x - w / 2, asr, w, label="Attack Success Rate", color="#c0392b")
    axes[0].bar(x + w / 2, fhr, w, label="False-Heal Rate", color="#e67e22")
    axes[0].set_title("Security: lower is better")
    axes[0].set_ylabel("%")
    axes[0].set_xticks(x); axes[0].set_xticklabels([labels[m] for m in modes])
    axes[0].legend(); axes[0].grid(True, axis="y", alpha=0.3)

    gfr = [results[m]["genuine_fault_reward"] for m in modes]
    axes[1].bar(x, gfr, color="#27ae60")
    axes[1].set_title("Healing quality on genuine faults\n(higher is better)")
    axes[1].set_ylabel("Mean reward")
    axes[1].set_xticks(x); axes[1].set_xticklabels([labels[m] for m in modes])
    axes[1].grid(True, axis="y", alpha=0.3)

    im = axes[2].imshow(confusion_mat.values, cmap="Blues")
    axes[2].set_title("Governor cause classification")
    axes[2].set_xticks(range(3)); axes[2].set_xticklabels(CAUSES, rotation=30, ha="right")
    axes[2].set_yticks(range(3)); axes[2].set_yticklabels(CAUSES)
    axes[2].set_xlabel("Predicted"); axes[2].set_ylabel("True")
    mx = confusion_mat.values.max()
    for i in range(3):
        for j in range(3):
            axes[2].text(j, i, int(confusion_mat.values[i, j]), ha="center",
                         va="center",
                         color="white" if confusion_mat.values[i, j] > mx / 2 else "black")

    plt.tight_layout()
    path = os.path.join(save_dir, "governed_evaluation.png")
    plt.savefig(path, dpi=200)
    plt.close(fig)
    return path


def print_report(results):
    print("\n=========== GOVERNED SELF-HEALING: SECURITY EVALUATION ===========")
    hdr = "{:<26}".format("metric") + "".join("{:>18}".format(m) for m in results)
    print(hdr)
    print("-" * len(hdr))
    rows = ["attack_success_rate", "attack_neutralised", "false_heal_rate",
            "genuine_fault_reward", "mean_reward", "cause_accuracy",
            "cause_acc_on_flagged", "adversarial_recall"]
    for r in rows:
        line = "{:<26}".format(r)
        for m in results:
            v = results[m].get(r)
            line += "{:>18}".format("-") if v is None else "{:>18.3f}".format(v)
        print(line)
    print("=" * len(hdr))
