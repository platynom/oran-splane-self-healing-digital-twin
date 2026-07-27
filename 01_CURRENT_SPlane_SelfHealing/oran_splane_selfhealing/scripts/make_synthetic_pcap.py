from __future__ import annotations

"""Generate a synthetic but wire-correct PTP-over-Ethernet pcap.

Purpose: validate the pcap ingestion path end-to-end WITHOUT the gated public
dataset. It emits real two-step PTP exchanges (Sync + Follow_Up + Delay_Req +
Delay_Resp) whose timestamps encode a known offset(t) and path delay, so a test
can assert the ingester recovers them. On your real Linux box you would instead
capture an actual ptp4l session with tcpdump and point the ingester at that file.

Clock convention (capture taken at the slave):
    t2 - t1 = path_delay + offset      (Sync:      master->slave)
    t4 - t3 = path_delay - offset      (Delay_Req: slave->master)
  => meanPathDelay = ((t2-t1)+(t4-t3))/2 = path_delay
     offsetFromMaster = (t2-t1) - meanPathDelay = offset
"""

import argparse
from pathlib import Path

import numpy as np

from ingest import ptp_wire as w

_MASTER_MAC = bytes.fromhex("001b19aabbcc")
_SLAVE_MAC = bytes.fromhex("001b1900ddee")
_EPOCH_S = 1_700_000_000


def generate_synthetic_pcap(path: str | Path, n: int = 200, interval_s: float = 0.0625,
                            path_delay_ns: float = 50_000.0, scenario: str = "healthy",
                            seed: int = 7) -> np.ndarray:
    """Write the pcap and return the ground-truth offset(t) array (ns)."""
    rng = np.random.default_rng(seed)
    true_offsets = np.zeros(n)
    offset = 30.0
    drift_ppb = 5.0
    writer = w.PcapWriter(str(path))
    try:
        for i in range(n):
            t_master_ns = _EPOCH_S * 1_000_000_000 + int(i * interval_s * 1e9)
            # evolve offset: servo-like wander + scenario perturbation
            offset += drift_ppb * interval_s + rng.normal(0, 2.0)
            offset *= 0.85  # a converging servo
            if scenario == "attack" and 0.45 * n <= i <= 0.75 * n:
                offset += 60.0          # sudden malicious step
            elif scenario == "fault" and 0.45 * n <= i <= 0.75 * n:
                offset += 8.0 * (i - 0.45 * n) * interval_s  # gradual holdover ramp
            pd_i = path_delay_ns + rng.normal(0, 20.0)
            jitter = rng.normal(0, 5.0)
            true_offsets[i] = offset

            # Keep timestamps as INTEGER ns: never add a float to the ~1.7e18 ns
            # epoch (float64 ULP there is ~256 ns). Round small terms first.
            t1 = int(t_master_ns)
            t2 = t1 + int(round(pd_i + offset + jitter))      # Sync arrival at slave (capture)
            t3 = t2 + 500_000                                 # slave sends Delay_Req 0.5 ms later
            t4 = t3 + int(round(pd_i - offset))               # master receives Delay_Req
            t_resp_cap = t3 + int(round(2 * pd_i))            # Delay_Resp back at slave (unused by math)

            seq = i & 0xFFFF
            # Sync (two-step: origin 0), then Follow_Up with precise origin t1
            writer.write(t2, w.build_eth_frame(_SLAVE_MAC, _MASTER_MAC,
                         w.build_ptp_payload(w.MT_SYNC, seq, origin_ts_ns=0)))
            writer.write(t2 + 1000, w.build_eth_frame(_SLAVE_MAC, _MASTER_MAC,
                         w.build_ptp_payload(w.MT_FOLLOW_UP, seq, origin_ts_ns=t1)))
            # Delay_Req sent by slave (captured at t3), Delay_Resp carries t4
            writer.write(t3, w.build_eth_frame(_MASTER_MAC, _SLAVE_MAC,
                         w.build_ptp_payload(w.MT_DELAY_REQ, seq, origin_ts_ns=0)))
            writer.write(t_resp_cap, w.build_eth_frame(_SLAVE_MAC, _MASTER_MAC,
                         w.build_ptp_payload(w.MT_DELAY_RESP, seq, origin_ts_ns=t4)))
    finally:
        writer.close()
    return true_offsets


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/tier2/synthetic_ptp.pcap")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--scenario", default="healthy", choices=["healthy", "fault", "attack"])
    args = ap.parse_args()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    generate_synthetic_pcap(args.out, n=args.n, scenario=args.scenario)
    print(f"wrote {args.out}")
