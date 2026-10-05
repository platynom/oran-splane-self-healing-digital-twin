#!/usr/bin/env bash
# S14 broader software experiment batch runner.
# Frozen by S14_BROADER_EXPERIMENT_PROTOCOL.json. Run from project root as root.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT="$HERE/s14_runs"
RUNNER="$HERE/run_s14_broader_trial.sh"
mkdir -p "$ROOT"

for i in 1 2 3 4 5; do
  echo "=== S14 Repetition $i / 5 ==="
  bash "$RUNNER" "$ROOT/20260913_s14_base$i"   "sb$i"  baseline_clean             no_action
  bash "$RUNNER" "$ROOT/20260913_s14_bng$i"    "sg$i"  benign_delay_jitter        no_action
  bash "$RUNNER" "$ROOT/20260913_s14_jact$i"   "sja$i" jitter_fault_action        action
  bash "$RUNNER" "$ROOT/20260913_s14_jnoact$i" "sjn$i" jitter_fault_no_action      no_action
  bash "$RUNNER" "$ROOT/20260913_s14_asf$i"    "saf$i" authorized_source_failover no_action
done
echo "S14 batch complete."
