from __future__ import annotations

"""Drive netem_harness.sh across scenarios and convert each captured pcap into
canonical telemetry, producing a real-trace dataset alongside the synthetic one.

Runs only where the harness can (root + linuxptp). Elsewhere it reports what it
would do and exits cleanly, so it never blocks the rest of Tier 2.
"""

import argparse
import subprocess
import time
from pathlib import Path

import pandas as pd

from ingest.linuxptp_ingest import linuxptp_available
from ingest.pcap_ingest import pcap_to_telemetry

HERE = Path(__file__).resolve().parent
# netem impairments are benign-fault-like -> H0; 'baseline' -> healthy.
SCENARIO_LABELS = {"baseline": "healthy", "pdv": "H0", "loss": "H0", "reorder": "H0", "holdover": "H0"}


def _wait_for_pcap_flush(path: Path, attempts: int = 8, delay_s: float = 0.25) -> None:
    """Give tcpdump a short moment to close/flush small pcaps before ingestion."""
    last_size = -1
    stable = 0
    for _ in range(attempts):
        size = path.stat().st_size if path.exists() else -1
        if size > 0 and size == last_size:
            stable += 1
            if stable >= 2:
                return
        else:
            stable = 0
        last_size = size
        time.sleep(delay_s)


def can_run() -> bool:
    import os
    return os.name == "posix" and os.geteuid() == 0 and linuxptp_available()


def run(scenarios, duration: int, out_dir: Path) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    status = []
    for scen in scenarios:
        pcap = out_dir / f"netem_{scen}.pcap"
        # One scenario must never abort the others. Capture + ingest each
        # independently, record the outcome, and continue.
        try:
            subprocess.run(["bash", str(HERE / "netem_harness.sh"), scen, str(duration), str(pcap)], check=True)
            _wait_for_pcap_flush(pcap)
            tel = pcap_to_telemetry(pcap, scenario=f"netem_{scen}", label=SCENARIO_LABELS.get(scen, "unlabeled"))
            tel["run_id"] = 0
            tel.to_csv(out_dir / f"netem_telemetry_{scen}.csv", index=False)  # persist per-scenario progress
            frames.append(tel)
            status.append({"scenario": scen, "status": "ok", "windows": len(tel), "detail": ""})
        except subprocess.CalledProcessError as e:
            status.append({"scenario": scen, "status": "capture_failed", "windows": 0, "detail": str(e)})
        except Exception as e:  # e.g. ingestion found no complete PTP exchange
            status.append({"scenario": scen, "status": "ingest_failed", "windows": 0, "detail": str(e)})

    pd.DataFrame(status).to_csv(out_dir / "netem_run_status.csv", index=False)
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_csv(out_dir / "netem_telemetry.csv", index=False)
    else:
        combined = pd.DataFrame()
    ok = [s["scenario"] for s in status if s["status"] == "ok"]
    bad = [f"{s['scenario']}({s['status']})" for s in status if s["status"] != "ok"]
    print(f"netem scenarios ok: {ok or 'none'}; failed: {bad or 'none'}")
    return combined


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="+", default=["baseline", "pdv", "loss", "holdover"])
    ap.add_argument("--duration", type=int, default=30)
    ap.add_argument("--out-dir", default="results/tier2/netem")
    args = ap.parse_args()
    if not can_run():
        print("netem harness needs Linux + root + linuxptp. Skipping live capture.\n"
              "On your box:  sudo python -m harness.run_netem_scenarios --duration 60")
        raise SystemExit(0)
    df = run(args.scenarios, args.duration, Path(args.out_dir))
    print(f"captured {len(df)} real-trace windows -> {args.out_dir}/netem_telemetry.csv")
