#!/usr/bin/env bash
set -euo pipefail
ROOT="outputs/empirical_software_network_pilot_v1/v4_runs"
RUNNER="01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/harness/run_empirical_software_pilot.sh"
run() { PILOT_DURATION_SECONDS=8 bash "$RUNNER" --execute "$ROOT/$3" "$1" "$2"; }
for i in 1 2 3 4 5; do
  run "w4b$i" baseline_control "20260913_v4_b$i"
  run "w4n$i" netem_delay_jitter_loss "20260913_v4_n$i"
  run "w4d$i" benign_delay_jitter_no_loss "20260913_v4_d$i"
  run "w4c$i" authorized_source_change_no_action_control "20260913_v4_c$i"
  run "w4s$i" authorized_source_change_intervention "20260913_v4_s$i"
done
