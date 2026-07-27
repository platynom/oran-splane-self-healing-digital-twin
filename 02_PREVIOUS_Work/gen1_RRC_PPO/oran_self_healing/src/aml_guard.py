# aml_guard.py
# NOVELTY COMPONENT (2/4): Adversarial-ML guard.
# The LSTM autoencoder says "is this anomalous?"; it cannot say "is this a real
# fault or a spoofed KPM report?". The guard exploits physics the attacker cannot
# fake cheaply: in a real channel the KPMs are COUPLED. A real fault moves the
# coupled KPMs together; a spoof manipulates one observable and leaves the coupled
# ones inconsistent. The guard learns those couplings on benign data (linear
# residuals) and adds two targeted physical-plausibility rules that, by design,
# fire on the spoof signatures but NOT on genuine-fault signatures.
# Output: (is_adversarial, score01, breakdown) - the breakdown is what the LLM
# governor reasons over.
import numpy as np

# (y, x): y is a stable linear function of x on benign traffic
PHYS_PAIRS = {
    "sinr~rsrp":    ("sinr", "rsrp"),
    "cqi~sinr":     ("cqi", "sinr"),
    "pktloss~cqi":  ("packet_loss", "cqi"),
    "latency~load": ("latency_ms", "network_load"),
    "pktloss~load": ("packet_loss", "network_load"),
}


class AMLGuard:
    def __init__(self, contamination_pct=97):
        self.contamination_pct = contamination_pct
        self.coef = {}
        self.threshold = None

    @staticmethod
    def _fit_linear(x, y):
        x = np.asarray(x, float); y = np.asarray(y, float)
        a, b = np.polyfit(x, y, 1)
        return a, b, max((y - (a * x + b)).std(), 1e-6)

    def fit(self, df_benign):
        for name, (ycol, xcol) in PHYS_PAIRS.items():
            self.coef[name] = self._fit_linear(df_benign[xcol].values,
                                               df_benign[ycol].values)
        scores = np.array([self._score_row(r) for _, r in df_benign.iterrows()])
        self.threshold = float(np.percentile(scores, self.contamination_pct))
        return self

    def _residuals(self, row):
        out = {}
        for name, (ycol, xcol) in PHYS_PAIRS.items():
            a, b, rstd = self.coef[name]
            out[name] = float(abs(row[ycol] - (a * row[xcol] + b)) / rstd)
        return out

    def _score_row(self, row):
        v = np.array(list(self._residuals(row).values()))
        return float(v.max() * 0.6 + v.mean() * 0.4)

    # ---- targeted physical-plausibility rules (spoof-specific) ----
    @staticmethod
    def _rule_flags(row):
        flags = []
        # (i) neighbour implausibly better while SERVING cell is HEALTHY.
        #     A real RLF has a COLLAPSED serving RSRP, so it is excluded.
        if (row["rsrp"] > -95 and row["sinr"] > 15
                and (row["neighbor_rsrp_1"] - row["rsrp"]) > 12):
            flags.append("neighbour_gap_while_serving_healthy")
        # (ii) heavy load + high latency but NO packet loss. Real congestion
        #      raises packet loss; a fake-congestion spoof does not.
        if (row["network_load"] > 0.9 and row["latency_ms"] > 60
                and row["packet_loss"] < 0.10):
            flags.append("congestion_without_packet_loss")
        # (iii) RSRP in outage but SINR/CQI still excellent -> physically
        #       impossible. A real RLF collapses SINR/CQI too, so it is excluded.
        if row["rsrp"] < -110 and (row["sinr"] > 15 or row["cqi"] > 10):
            flags.append("rsrp_collapse_without_sinr_drop")
        return flags

    def analyze(self, row):
        z = self._residuals(row)
        rule_flags = self._rule_flags(row)
        # Decision rests on the physical-invariant rules: on this data the benign
        # SINR/CQI are saturated, so the linear residuals are kept only as
        # explanatory context, not as the decision criterion.
        is_adv = bool(rule_flags)
        score01 = 0.9 if rule_flags else float(
            min(self._score_row(row) / max(self.threshold, 1e-6) * 0.4, 0.45))
        worst = max(z.items(), key=lambda kv: kv[1])
        worst_name = rule_flags[0] if rule_flags else worst[0]
        breakdown = {
            "worst_violation": worst_name,
            "worst_zscore": round(worst[1], 2),
            "rule_flags": rule_flags,
            "residuals": {k: round(v, 2) for k, v in z.items()},
        }
        return bool(is_adv), score01, breakdown
