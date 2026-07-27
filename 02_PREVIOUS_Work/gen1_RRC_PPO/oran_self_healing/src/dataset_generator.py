# dataset_generator.py
import numpy as np
import pandas as pd

class RRCDatasetGenerator:
    def __init__(self, mobility_sim):
        self.sim = mobility_sim
        self.records = []

    def compute_rsrp(self, ue, cell):
        # 3GPP UMa path loss model (simplified)
        dist = max(np.sqrt((ue.x-cell.x)**2 + (ue.y-cell.y)**2), 1)
        tx_power_dbm = 46  # eNodeB TX power
        path_loss = 128.1 + 37.6 * np.log10(dist/1000)  # dB, dist in km
        shadow_fading = np.random.normal(0, 8)  # 8dB std
        rsrp = tx_power_dbm - path_loss + shadow_fading
        return np.clip(rsrp, -140, -44)  # 3GPP RSRP range

    def compute_rsrq(self, rsrp, n_rb=100, interference=-100):
        rssi = rsrp + 10*np.log10(n_rb) + np.random.normal(0,2)
        rsrq = rsrp - rssi
        return np.clip(rsrq, -19.5, -3)

    def compute_sinr(self, rsrp, interference_offset=-10):
        noise = -174 + 10*np.log10(180000) + 7  # thermal noise, 180kHz RB, 7dB NF
        sinr = rsrp - (noise + interference_offset + np.random.normal(0,3))
        return np.clip(sinr, -10, 30)

    def sinr_to_cqi(self, sinr):
        # Approximate CQI from SINR
        thresholds = [-6.7,-4.7,-2.3,0.2,2.4,4.3,5.9,8.1,10.3,11.7,14.1,16.3,18.7,21.0,22.7]
        cqi = 0
        for t in thresholds:
            if sinr > t:
                cqi += 1
        return cqi

    def generate_record(self, ue, cell, timestamp, failure_type=None, network_load=0.5):
        rsrp = self.compute_rsrp(ue, cell)
        rsrq = self.compute_rsrq(rsrp)
        sinr = self.compute_sinr(rsrp)
        cqi = self.sinr_to_cqi(sinr)

        # Neighbor cells
        neighbors = sorted(self.sim.cells, key=lambda c: np.sqrt((ue.x-c.x)**2+(ue.y-c.y)**2))
        neighbor_rsrp = [self.compute_rsrp(ue, n) for n in neighbors[1:4]]

        # Latency and packet loss based on load and signal
        base_latency = 5  # ms
        load_factor = network_load * 30
        sinr_penalty = max(0, (10 - sinr) * 2)
        latency = base_latency + load_factor + sinr_penalty + np.random.exponential(2)
        packet_loss = np.clip((0.01 + (1 - cqi/15) * 0.15 + network_load * 0.05), 0, 1)

        record = {
            "timestamp": timestamp,
            "ue_id": ue.ue_id,
            "serving_cell": cell.cell_id,
            "neighbor_cell_1": neighbors[1].cell_id if len(neighbors) > 1 else -1,
            "neighbor_cell_2": neighbors[2].cell_id if len(neighbors) > 2 else -1,
            "neighbor_rsrp_1": neighbor_rsrp[0] if len(neighbor_rsrp) > 0 else -140,
            "neighbor_rsrp_2": neighbor_rsrp[1] if len(neighbor_rsrp) > 1 else -140,
            "rsrp": rsrp,
            "rsrq": rsrq,
            "sinr": sinr,
            "cqi": cqi,
            "rrc_state": ue.rrc_state,
            "latency_ms": latency,
            "packet_loss": packet_loss,
            "network_load": network_load,
            "traffic_type": np.random.choice(["VoIP","Video","Data","IoT"], p=[0.2,0.3,0.4,0.1]),
            "failure_type": failure_type or "None",
            "ue_x": ue.x,
            "ue_y": ue.y,
            "ue_speed": ue.speed
        }
        return record

    def run(self, steps=1000):
        for t in range(steps):
            self.sim.step()
            load = np.random.beta(2,5)  # realistic load distribution
            for ue in self.sim.ues:
                cell = ue.serving_cell
                rec = self.generate_record(ue, cell, t, network_load=load)
                self.records.append(rec)
        return pd.DataFrame(self.records)