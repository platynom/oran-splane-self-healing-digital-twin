# fault_coupling.py
# Makes GENUINE faults physically coherent (coupled KPMs move together), matching
# how a real radio fault behaves. This is what lets the AML guard separate a real
# fault (all coupled KPMs degrade together) from an adversarial spoof (one KPM
# manipulated, couplings broken). Applied only to genuine-fault rows; adversarial
# rows are injected AFTER this and deliberately stay inconsistent.
import numpy as np

# generator physics: sinr ~ rsrp + ~124.45 (thermal noise + offset), clipped
SINR_OFFSET = 124.45
CQI_THRESH = [-6.7, -4.7, -2.3, 0.2, 2.4, 4.3, 5.9, 8.1, 10.3, 11.7,
              14.1, 16.3, 18.7, 21.0, 22.7]
RSRP_DRIVEN = {"RLF", "SIGNAL_DEGRADATION"}


def _sinr_to_cqi(sinr):
    return int(sum(1 for t in CQI_THRESH if sinr > t))


def couple_faults(df, seed=0):
    rng = np.random.default_rng(seed)
    df = df.copy()
    for i in df.index:
        ft = df.at[i, "failure_type"]
        if ft in RSRP_DRIVEN:
            rsrp = df.at[i, "rsrp"]
            sinr = float(np.clip(rsrp + SINR_OFFSET + rng.normal(0, 1.5), -10, 30))
            cqi = _sinr_to_cqi(sinr)
            df.at[i, "sinr"] = sinr
            df.at[i, "cqi"] = cqi
            df.at[i, "packet_loss"] = float(np.clip(
                0.01 + (1 - cqi / 15) * 0.15
                + df.at[i, 'network_load'] * 0.05, 0, 1))
            df.at[i, "latency_ms"] = float(df.at[i, "latency_ms"]
                                           + max(0, (10 - sinr)) * 2)
    return df
