#!/usr/bin/env bash
# V5 single-variable attribution batch. Frozen by V5_SINGLE_VARIABLE_PROTOCOL.json.
# Run from the project root in the same WSL environment as V4 (root; ip, tc, ptp4l, tcpdump present).
set -euo pipefail
ROOT="outputs/empirical_software_network_pilot_v1/v5_runs"
RUNNER="01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/harness/run_empirical_software_pilot_v5.sh"
run() { PILOT_DURATION_SECONDS=8 bash "$RUNNER" --execute "$ROOT/$3" "$1" "$2"; }
for i in 1 2 3 4 5; do
  run "w5a$i" benign_delay_jitter_no_loss "20260913_v5_a$i"   # A reference
  run "w5b$i" v5_loss_only                "20260913_v5_b$i"   # B loss only
  run "w5c$i" v5_jitter_only              "20260913_v5_c$i"   # C jitter only
  run "w5d$i" v5_delay_only               "20260913_v5_d$i"   # D delay only
  run "w5e$i" netem_delay_jitter_loss     "20260913_v5_e$i"   # E full impairment
done
