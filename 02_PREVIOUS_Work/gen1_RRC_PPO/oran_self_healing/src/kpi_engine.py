# kpi_engine.py
import pandas as pd
import numpy as np

class KPIEngine:
    def __init__(self):
        self.history = []

    def compute_kpis(self, df_window):
        """Compute KPIs over a rolling window of records."""
        n = len(df_window)
        rlf_events = (df_window['failure_type'] == 'RLF').sum()
        ho_events = (df_window['serving_cell'].diff() != 0).sum()
        pp_events = (df_window['failure_type'] == 'PING_PONG').sum()

        # Detect successful HOs (serving cell changed without RLF)
        ho_success = ho_events - rlf_events
        ho_success_rate = ho_success / max(ho_events, 1)

        kpis = {
            "rlf_rate": rlf_events / n,
            "ho_success_rate": ho_success_rate,
            "avg_latency_ms": df_window['latency_ms'].mean(),
            "p95_latency_ms": df_window['latency_ms'].quantile(0.95),
            "avg_packet_loss": df_window['packet_loss'].mean(),
            "ping_pong_rate": pp_events / max(ho_events, 1),
            "avg_cell_load": df_window['network_load'].mean(),
            "signaling_overhead": ho_events / n,
            "qoe_score": self._compute_qoe(df_window)
        }
        self.history.append(kpis)
        return kpis

    def _compute_qoe(self, df):
        # Simple MOS-like QoE: 1-5 scale
        sinr_score = np.clip(df['sinr'].mean() / 30, 0, 1)
        latency_score = 1 - np.clip(df['latency_ms'].mean() / 200, 0, 1)
        loss_score = 1 - np.clip(df['packet_loss'].mean() / 0.3, 0, 1)
        return 1 + 4 * (0.4*sinr_score + 0.35*latency_score + 0.25*loss_score)