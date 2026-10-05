#!/usr/bin/env bash
set -e
cd "/mnt/c/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin/01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing"
echo "Installing/checking linuxptp, tcpdump, iproute2. Enter the sudo password for oranuser if prompted."
sudo apt-get update
sudo apt-get install -y linuxptp tcpdump iproute2
echo "Installing/checking root Python packages needed by sudo python3."
sudo python3 -m pip install pandas numpy PyYAML || sudo python3 -m pip install pandas numpy PyYAML --break-system-packages
echo "Running real netem scenarios for baseline, pdv, loss, holdover."
sudo env PYTHONPATH="$PWD" python3 -m harness.run_netem_scenarios --scenarios baseline pdv loss holdover --duration 60
echo
echo "DONE: check results/tier2/netem/netem_telemetry.csv"
read -r -p "Press Enter to close..."
