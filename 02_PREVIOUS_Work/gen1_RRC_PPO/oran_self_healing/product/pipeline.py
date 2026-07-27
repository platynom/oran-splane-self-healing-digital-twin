"""
Unified productisation CLI.

  python product/pipeline.py train      # fit gate+guard on data, persist artifacts
  python product/pipeline.py evaluate   # run the 3-config security evaluation
  python product/pipeline.py serve      # launch the decision microservice
"""
import os, sys, argparse, yaml
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd

CFG = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "config.yaml")))

def _load_or_build_data():
    csv = CFG["data"]["train_csv"]
    if os.path.exists(csv):
        return pd.read_csv(csv)
    # build it via the existing generator if not present
    from mobility_simulator import MobilitySimulator
    from dataset_generator import RRCDatasetGenerator
    from failure_injector import FailureInjector
    from fault_coupling import couple_faults
    from adversarial_injector import AdversarialInjector
    np.random.seed(42)
    sim = MobilitySimulator(n_cells=7, n_ues=10)
    df = RRCDatasetGenerator(sim).run(steps=900)
    df = FailureInjector().inject(df, sim.cells)
    df = couple_faults(df, seed=42)
    df = AdversarialInjector(attack_rate=0.06, seed=42).inject(df)
    os.makedirs(os.path.dirname(csv), exist_ok=True)
    df.to_csv(csv, index=False)
    return df

def cmd_train(_):
    from aml_guard import AMLGuard
    from persistence import save_artifacts
    df = _load_or_build_data()
    ft = df.failure_type.fillna("None").astype(str)
    adv = df.get("is_adversarial", pd.Series(False, index=df.index)).fillna(False).astype(bool)
    benign = df[(ft == "None") & (~adv)].copy()
    try:
        from anomaly_detector import AnomalyDetector
        gate = AnomalyDetector(threshold_percentile=CFG["gate"]["threshold_percentile"],
                               epochs=6, batch_size=128); gate.train(benign)
        gate_kind = "LSTM-AE"
    except Exception as e:
        from lite_components import LiteAnomalyGate
        gate = LiteAnomalyGate(threshold_percentile=CFG["gate"]["threshold_percentile"]).train(benign)
        gate_kind = f"PCA-surrogate ({type(e).__name__})"
    guard = AMLGuard(contamination_pct=CFG["guard"]["contamination_pct"]).fit(benign)
    save_artifacts(CFG["runtime"]["artifacts_dir"], gate, guard,
                   meta={"gate": gate_kind, "n_benign": int(len(benign))})
    print(f"[train] fitted gate={gate_kind}, guard on {len(benign)} benign rows -> "
          f"{CFG['runtime']['artifacts_dir']}/")

def cmd_evaluate(_):
    os.system(f"{sys.executable} main_governed.py")

def cmd_serve(_):
    os.system(f"{sys.executable} -m uvicorn product.governor_service:app "
              f"--host 0.0.0.0 --port 8080")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in [("train", cmd_train), ("evaluate", cmd_evaluate), ("serve", cmd_serve)]:
        sub.add_parser(name).set_defaults(func=fn)
    a = ap.parse_args(); a.func(a)
