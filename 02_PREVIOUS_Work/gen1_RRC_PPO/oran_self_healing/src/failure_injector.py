# failure_injector.py
import numpy as np

class FailureInjector:
    def __init__(self, failure_rate=0.05):
        self.failure_rate = failure_rate
        self.active_failures = {}  # cell_id -> {type, start, duration}

    def inject(self, records_df, cells):
        df = records_df.copy()
        n = len(df)

        for i, row in df.iterrows():
            r = np.random.random()
            if r < 0.02:  # RLF: sudden RSRP collapse
                df.at[i, 'rsrp'] = np.random.uniform(-140, -120)
                df.at[i, 'failure_type'] = 'RLF'
                df.at[i, 'rrc_state'] = 'RRC_IDLE'

            elif r < 0.05:  # Signal degradation
                df.at[i, 'rsrp'] += np.random.uniform(-20, -10)
                df.at[i, 'sinr'] += np.random.uniform(-10, -5)
                df.at[i, 'failure_type'] = 'SIGNAL_DEGRADATION'

            elif r < 0.07:  # Congestion
                df.at[i, 'network_load'] = np.random.uniform(0.85, 1.0)
                df.at[i, 'latency_ms'] *= np.random.uniform(3, 8)
                df.at[i, 'packet_loss'] = min(df.at[i,'packet_loss'] * 5, 0.5)
                df.at[i, 'failure_type'] = 'CONGESTION'

            elif r < 0.09:  # Ping-pong handover (serving cell keeps switching)
                if i > 0 and df.at[i-1,'failure_type'] == 'PING_PONG':
                    df.at[i, 'serving_cell'] = df.at[i-1,'neighbor_cell_1']
                df.at[i, 'failure_type'] = 'PING_PONG'

            elif r < 0.10:  # Traffic spike
                df.at[i, 'network_load'] = min(df.at[i,'network_load'] * 4, 1.0)
                df.at[i, 'failure_type'] = 'TRAFFIC_SPIKE'

        # Cell outage: pick random cell, zero out its UEs for a window
        outage_start = np.random.randint(200, n-100)
        outage_cell = np.random.randint(0, len(cells))
        outage_mask = (df['timestamp'] >= outage_start) & \
                      (df['timestamp'] < outage_start+50) & \
                      (df['serving_cell'] == outage_cell)
        df.loc[outage_mask, 'rsrp'] = -140
        df.loc[outage_mask, 'failure_type'] = 'CELL_OUTAGE'
        df.loc[outage_mask, 'rrc_state'] = 'RRC_IDLE'

        return df