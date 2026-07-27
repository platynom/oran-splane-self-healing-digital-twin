# Running Tier 2 on a real Linux box (no PTP hardware needed)

Everything below runs on an ordinary Linux machine or VM. Only `sudo` + the
`linuxptp` package are required — no PTP NIC, O-RU, or O-DU.

## 0. Install prerequisites

```bash
sudo apt-get update && sudo apt-get install -y linuxptp tcpdump iproute2
pip install -r requirements.txt
```

## 1. Generate REAL degraded PTP traffic with netem, capture it

```bash
cd oran_splane_selfhealing
sudo python -m harness.run_netem_scenarios --scenarios baseline pdv loss holdover --duration 60
```

This spins up a veth pair in a network namespace, runs `ptp4l` master↔slave over
it with software timestamping, degrades the link with `tc netem`, and captures a
nanosecond-precision pcap per scenario. Output:
`results/tier2/netem/netem_telemetry.csv` (canonical schema, ready for the pipeline).

To run a single scenario and keep the pcap:

```bash
sudo ./harness/netem_harness.sh pdv 60 results/tier2/netem/pdv.pcap
```

## 2. Ingest an existing capture (e.g. a released public dataset)

Point the config at any PTP-over-Ethernet capture and ingest it:

```python
from ingest.pcap_ingest import pcap_to_telemetry
tel = pcap_to_telemetry("path/to/capture.pcap", label="unlabeled")
```

Or parse a live `ptp4l` log:

```bash
sudo ptp4l -i eth0 -m -q -s -S > ptp4l.log      # -S = software timestamping
```
```python
from ingest.linuxptp_ingest import ptp4l_log_to_telemetry
tel = ptp4l_log_to_telemetry("ptp4l.log")
```

## 3. Feed real telemetry through the existing pipeline

Because the ingesters emit the canonical schema, the unchanged feature extractor,
discriminator, twin, and healing loop all consume it:

```python
from telemetry.features import window_features
from twin.model import forecast_all
feats = window_features(tel, window_s=0.4, step_s=0.2)   # same as simulator path
```

## 4. Full statistical suite

```bash
python scripts/run_tier2.py        # multi-seed CIs, generalization, twin, ingestion self-tests
```

## What this does NOT do

- No malicious spoof/replay injection (needs an active attacker; out of scope for netem).
- Software timestamps over veth ≠ hardware PTP timestamps (that is the Tier-3 hardware step).
