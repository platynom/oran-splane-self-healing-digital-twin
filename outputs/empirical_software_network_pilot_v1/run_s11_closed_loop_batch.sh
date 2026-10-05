#!/usr/bin/env bash
# S11 closed-loop batch. Frozen by S11_CLOSED_LOOP_PROTOCOL.json. Run from the project root as root.
set -euo pipefail
ROOT="outputs/empirical_software_network_pilot_v1/s11_runs"
RUNNER="01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/harness/run_s11_closed_loop.sh"
for i in 1 2 3 4 5; do
  bash "$RUNNER" "$ROOT/20260913_s11_act$i"  "sa$i" action
  bash "$RUNNER" "$ROOT/20260913_s11_noact$i" "sn$i" no_action
done
