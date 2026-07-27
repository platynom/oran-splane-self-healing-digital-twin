from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataset.build import build_dataset
from discriminator.model import train_and_evaluate
from fronthaul_sim.simulator import SimConfig, healthy_trace, has_linuxptp
from benchmark.run import run_benchmark
from telemetry.features import label_integrity


def load_config() -> dict:
    with (ROOT / "config" / "default.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def append_progress(text: str) -> None:
    path = ROOT / "results" / "PROGRESS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().isoformat(timespec='seconds')}\n{text}\n")


def write_summary(metrics, bench, config: dict) -> None:
    best = metrics.iloc[0]
    governed = bench[bench["method"] == "governed_loop"].iloc[0]
    (ROOT / "results" / "SUMMARY.md").write_text(
        "# Summary\n\n"
        "Built an end-to-end, CPU-only O-RAN Open-Fronthaul S-plane self-healing prototype using a deterministic "
        "pure-Python PTP/SyncE simulator and digital twin.\n\n"
        f"- linuxptp available: {has_linuxptp()} (pure-Python remains default).\n"
        f"- H0/H1 discriminator accuracy: {best['accuracy']:.3f}; macro F1: {best['f1_macro']:.3f}; ROC-AUC(H1): {best['roc_auc_h1']:.3f}.\n"
        f"- Governed-loop recovery success: {governed['recovery_success_rate']:.3f}; wrong-action rate: {governed['wrong_action_rate']:.3f}; mean MTTR: {governed['mean_mttr_s']:.3f} s.\n"
        f"- Time-error budget: {config['time_error_budget_ns']} ns; failure window: {config['failure_window_s']} s.\n\n"
        "Phase mapping: P1 simulator, P2 labelled dataset, P3 discriminator + detection-only baseline, P4 twin forecasts "
        "with fidelity score, P5 governed loop, P6 benchmark tables and plots, P7 one-command reproduction.\n\n"
        "Honest limitations: this is emulation, not hardware timestamping. Real PTP NIC/O-RU validation and linuxptp/netem "
        "experiments remain TODO integration stubs.\n",
        encoding="utf-8",
    )


def main() -> None:
    config = load_config()
    sim_cfg = SimConfig(seed=config["seed"], time_error_budget_ns=config["time_error_budget_ns"], **config["sim"])
    healthy = healthy_trace(sim_cfg)
    assert healthy.tail(80)["offset_ns"].abs().mean() < config["time_error_budget_ns"], "healthy servo outside budget"
    append_progress("P1 passed: healthy pure-Python S-plane servo converges within the configured time-error budget.")

    windows = build_dataset(config, ROOT / "dataset")
    assert label_integrity(windows), "dataset label integrity failed"
    append_progress("P2 passed: generated labelled healthy/H0/H1 telemetry windows and datasheet.")

    clf, metrics = train_and_evaluate(windows, config, ROOT / "results")
    assert metrics.iloc[0]["f1_macro"] > metrics.iloc[1]["f1_macro"], "discriminator did not beat detection-only baseline"
    append_progress("P3 passed: trained H0-vs-H1 discriminator and beat detection-only baseline on held-out windows.")

    from twin.model import forecast_all
    forecasts = forecast_all(windows.iloc[-1], config["healing"]["actions"])
    forecasts.to_csv(ROOT / "results" / "twin_action_forecasts.csv", index=False)
    assert not forecasts.empty and forecasts["fidelity"].between(0, 1).all()
    append_progress("P4 passed: produced per-action digital-twin forecasts with bounded fidelity score.")

    bench = run_benchmark(windows, clf, config, ROOT / "results")
    governed = bench[bench["method"] == "governed_loop"].iloc[0]
    assert governed["within_2s_rate"] == 1.0 and governed["recovery_success_rate"] >= 0.9
    append_progress("P5/P6 passed: governed loop restored timing in benchmark scenarios and outperformed baselines.")

    write_summary(metrics, bench, config)
    append_progress("P7/P8 passed: run_all.py reproduced dataset, training, twin forecasts, benchmark, plots, and SUMMARY.md.")
    print("All phases complete. See results/SUMMARY.md")


if __name__ == "__main__":
    main()
