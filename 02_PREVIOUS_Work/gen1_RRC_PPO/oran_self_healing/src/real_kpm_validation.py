# real_kpm_validation.py
# ---------------------------------------------------------------------------
# Real-data validation of the CORE novelty idea (physical-consistency based
# adversarial detection) on genuine O-RAN KPMs.
#
# Dataset: VERGE-PROJECT/OAI_RAN_KPM_dataset - RAN KPM time-series captured on a
# bare-metal OpenAirInterface + FlexRIC + KPM-xApp testbed (CSV/XLSX).
#
# The synthetic twin uses RSRP/SINR/CQI couplings; here we show the SAME residual
# consistency principle holds on REAL KPMs whose native couplings are
# throughput<->traffic-volume<->PRB-utilisation<->RLC-delay. We spoof a fraction
# of real snapshots (inflate one KPM, leave the coupled ones untouched) and test
# whether the consistency guard separates spoofed from genuine reports.
# ---------------------------------------------------------------------------
import numpy as np
import pandas as pd

REAL_PATH = "data/real/oai_kpm_5weeks.xlsx"
FEATS = ["RRU.PrbTotDl", "RRU.PrbTotUl", "DRB.PdcpSduVolumeDL",
         "DRB.PdcpSduVolumeUL", "DRB.RlcSduDelayDl", "DRB.UEThpDl", "DRB.UEThpUl"]

# native physical couplings in the real KPMs  (y | x)
PAIRS = {
    "ThpDl|VolDl":  ("DRB.UEThpDl", "DRB.PdcpSduVolumeDL"),
    "ThpUl|VolUl":  ("DRB.UEThpUl", "DRB.PdcpSduVolumeUL"),
    "PrbUl|VolUl":  ("RRU.PrbTotUl", "DRB.PdcpSduVolumeUL"),
    "Delay|PrbDl":  ("DRB.RlcSduDelayDl", "RRU.PrbTotDl"),
}


def _fit(x, y):
    a, b = np.polyfit(x, y, 1)
    return a, b, max((y - (a * x + b)).std(), 1e-6)


def run_real_validation(spoof_rate=0.15, seed=7):
    rng = np.random.default_rng(seed)
    df = pd.read_excel(REAL_PATH, sheet_name="KPM Metrics")[FEATS].dropna().reset_index(drop=True)
    n = len(df)

    # split: fit couplings on first 60% (assumed genuine), test on the rest
    cut = int(n * 0.6)
    train, test = df.iloc[:cut].copy(), df.iloc[cut:].copy().reset_index(drop=True)
    coef = {name: _fit(train[x].values, train[y].values) for name, (y, x) in PAIRS.items()}

    # threshold from genuine training residuals
    def score(row):
        zs = []
        for name, (y, x) in PAIRS.items():
            a, b, rstd = coef[name]
            zs.append(abs(row[y] - (a * row[x] + b)) / rstd)
        zs = np.array(zs)
        return zs.max() * 0.6 + zs.mean() * 0.4
    thr = np.percentile([score(r) for _, r in train.iterrows()], 97)

    # spoof a fraction of the TEST set: inflate one KPM, leave couplings broken
    labels, preds = [], []
    for i in range(len(test)):
        row = test.iloc[i].copy()
        is_spoof = rng.random() < spoof_rate
        if is_spoof:
            tgt = rng.choice(["DRB.UEThpDl", "RRU.PrbTotUl", "DRB.RlcSduDelayDl"])
            row[tgt] = row[tgt] * rng.uniform(3, 6) + 1.0
        s = score(row)
        labels.append(int(is_spoof))
        preds.append(int(s >= thr))

    labels, preds = np.array(labels), np.array(preds)
    tp = int(((preds == 1) & (labels == 1)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    recall = tp / max(tp + fn, 1)
    precision = tp / max(tp + fp, 1)
    fpr = fp / max(fp + tn, 1)
    acc = (tp + tn) / max(len(labels), 1)
    return {
        "samples_total": n, "test_samples": len(test),
        "spoofed": int(labels.sum()),
        "detection_recall": round(recall, 3),
        "precision": round(precision, 3),
        "false_positive_rate": round(fpr, 3),
        "accuracy": round(acc, 3),
    }


if __name__ == "__main__":
    print(run_real_validation())
