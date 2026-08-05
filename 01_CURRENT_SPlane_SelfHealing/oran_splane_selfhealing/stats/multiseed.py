from __future__ import annotations

"""Multi-seed evaluation with 95% confidence intervals, plus a leave-one-attack-out
generalization test. Answers: are the headline numbers stable across seeds, and
does the discriminator catch an attack family it never trained on?
"""

import copy
import hashlib
import json
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as sstats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import recall_score

from benchmark.run import run_benchmark
from dataset.build import build_dataset
from discriminator.model import train_and_evaluate
from faults.injectors import H0_SCENARIOS, H1_SCENARIOS
from telemetry.features import FEATURE_COLUMNS

_METRICS = ["accuracy", "f1_macro", "roc_auc_h1", "recovery_success_rate", "wrong_action_rate", "mean_mttr_s"]
_ATTACK_FAMILY = {
    "ptp_spoof": "spoof",
    "ptp_replay": "replay",
    "ptp_dos_flood": "dos",
    "gnss_spoof": "gnss_spoof",
    "gnss_jam": "gnss_jam",
}


def _cache_signature() -> str:
    definition = json.dumps(
        {"features": FEATURE_COLUMNS, "h0_scenarios": H0_SCENARIOS, "h1_scenarios": H1_SCENARIOS},
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(definition).hexdigest()[:10]


def _one_run(base_config: dict, seed: int, tmp: Path) -> dict:
    cfg = copy.deepcopy(base_config)
    cfg["seed"] = seed
    cfg["discriminator"]["random_state"] = seed
    windows = build_dataset(cfg, tmp / f"ds_{seed}")
    _clf, metrics = train_and_evaluate(windows, cfg, tmp / f"res_{seed}")
    bench = run_benchmark(windows, _clf, cfg, tmp / f"res_{seed}")
    gov = bench[bench["method"] == "governed_loop"].iloc[0]
    best = metrics.iloc[0]
    return {
        "seed": seed,
        "accuracy": float(best["accuracy"]),
        "f1_macro": float(best["f1_macro"]),
        "roc_auc_h1": float(best["roc_auc_h1"]),
        "recovery_success_rate": float(gov["recovery_success_rate"]),
        "wrong_action_rate": float(gov["wrong_action_rate"]),
        "mean_mttr_s": float(gov["mean_mttr_s"]),
    }


def ci95(x: np.ndarray) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=float)
    n = len(x)
    mean = float(x.mean())
    if n < 2:
        return mean, 0.0, 0.0
    sem = float(x.std(ddof=1) / np.sqrt(n))
    half = float(sstats.t.ppf(0.975, n - 1) * sem)
    return mean, half, float(x.std(ddof=1))


def run_multiseed(base_config: dict, seeds: list[int], out_dir: Path) -> pd.DataFrame | None:
    """Resumable: each seed's result is cached on completion, so this can be
    called repeatedly (e.g. under a wall-clock cap) until all seeds finish. The
    final summary is only written once every seed is cached."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = out_dir / "_seedcache"
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for s in seeds:
            cf = cache / f"seed_{s}_{_cache_signature()}.json"
            if cf.exists():
                continue
            cf.write_text(json.dumps(_one_run(base_config, s, tmp)), encoding="utf-8")

    cache_files = [cache / f"seed_{s}_{_cache_signature()}.json" for s in seeds]
    done = [json.loads(path.read_text()) for path in cache_files if path.exists()]
    if len(done) < len(seeds):
        print(f"multiseed progress: {len(done)}/{len(seeds)} seeds cached (re-run to continue)")
        return None
    per_seed = pd.DataFrame(done)
    per_seed.to_csv(out_dir / "multiseed_per_seed.csv", index=False)

    summary_rows = []
    for m in _METRICS:
        mean, half, sd = ci95(per_seed[m].to_numpy())
        summary_rows.append({"metric": m, "mean": mean, "ci95_halfwidth": half,
                             "ci95_low": mean - half, "ci95_high": mean + half, "std": sd, "n": len(seeds)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_dir / "multiseed_summary.csv", index=False)
    _plot(summary, out_dir / "multiseed_ci.png")
    return summary


def leave_one_attack_out(base_config: dict, seed: int, out_dir: Path) -> pd.DataFrame:
    """Train the H0/H1 discriminator with ONE attack family held out entirely,
    then measure recall on that unseen family. Tests generalization to novel
    attacks (the reviewer's 'does it only memorize known attacks?' question)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = copy.deepcopy(base_config)
    cfg["seed"] = seed
    with tempfile.TemporaryDirectory() as td:
        windows = build_dataset(cfg, Path(td) / "ds")
    rows = []
    for held in H1_SCENARIOS:
        train = windows[(windows["label"] == "H0") |
                        ((windows["label"] == "H1") & (windows["scenario"] != held))]
        test_attack = windows[(windows["label"] == "H1") & (windows["scenario"] == held)]
        if test_attack.empty:
            continue
        clf = RandomForestClassifier(n_estimators=90, max_depth=6, random_state=seed, class_weight="balanced")
        clf.fit(train[FEATURE_COLUMNS], train["label"])
        pred = clf.predict(test_attack[FEATURE_COLUMNS])
        recall = recall_score((test_attack["label"] == "H1").astype(int),
                              (pd.Series(pred) == "H1").astype(int), zero_division=0)
        rows.append({
            "held_out_attack": held,
            "attack_family": _ATTACK_FAMILY.get(held, held),
            "unseen_attack_recall": float(recall),
            "n_windows": int(len(test_attack)),
        })
    logo = pd.DataFrame(rows)
    logo.to_csv(out_dir / "leave_one_attack_out.csv", index=False)
    return logo


def _plot(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.errorbar(summary["metric"], summary["mean"], yerr=summary["ci95_halfwidth"],
                fmt="o", capsize=5, color="#1f4e79")
    ax.set_title("Tier-2 multi-seed metrics (mean ± 95% CI)")
    ax.set_ylim(0, 1.05)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()
