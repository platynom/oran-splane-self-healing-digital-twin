# lite_components.py
# Lightweight, dependency-free stand-ins for the two heavy learned components,
# exposing identical interfaces so the governed harness runs without PyTorch/SB3.
#   LiteAnomalyGate <-> AnomalyDetector (LSTM-AE)  .detect(window)
#   LitePolicyAgent <-> PPO agent (SB3)            .predict(obs)
# The novelty layer is identical whichever backend is used. LitePolicyAgent is
# deliberately observation-reactive -> like any trained RRC policy it is foolable
# by spoofed KPMs, which is exactly the vulnerability the governor fixes.
import numpy as np

FEATURES = ["rsrp", "rsrq", "sinr", "cqi", "latency_ms", "packet_loss"]


class LiteAnomalyGate:
    def __init__(self, threshold_percentile=97, seq_len=10, n_components=8):
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        self.seq_len = seq_len
        self.pct = threshold_percentile
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)
        self.threshold = None
        self.features = FEATURES

    def _windows(self, df):
        dfx = df.sort_values(["ue_id", "timestamp"]).copy()
        dfx[self.features] = self.scaler.transform(dfx[self.features].values)
        v = dfx[self.features].values
        return np.array([v[i:i + self.seq_len].flatten()
                         for i in range(len(v) - self.seq_len + 1)])

    def train(self, benign_df):
        self.scaler.fit(benign_df[self.features].values)
        X = self._windows(benign_df)
        self.pca.fit(X)
        rec = self.pca.inverse_transform(self.pca.transform(X))
        errs = ((X - rec) ** 2).mean(axis=1)
        self.threshold = float(np.percentile(errs, self.pct))
        return self

    def detect(self, window):
        flat = window.reshape(-1, len(self.features))
        scaled = self.scaler.transform(flat).reshape(1, -1)
        rec = self.pca.inverse_transform(self.pca.transform(scaled))
        mse = float(((scaled - rec) ** 2).mean())
        return (mse > self.threshold if self.threshold else False), mse


class LitePolicyAgent:
    def predict(self, obs, deterministic=True):
        rsrp, sinr = obs[0], obs[2]
        nb1, load, lat = obs[4], obs[6], obs[7]
        if rsrp < -100 and nb1 > rsrp + 3:
            a = 0
        elif nb1 > rsrp + 6:
            a = 0
        elif load > 0.9 and lat > 60:
            a = 4
        elif load > 0.85:
            a = 3
        elif sinr > 10 and lat < 20:
            a = 5
        else:
            a = 2
        return np.array(a), None
