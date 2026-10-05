#!/usr/bin/env bash
# S15 independent validation batch: graded jitter sweep, all no_action.
# Frozen by S15_INDEPENDENT_VALIDATION_PROTOCOL_V2.json.
# Trial order is COUNTERBALANCED AND RANDOMISED, generated once from seed 20260913
# (randomised 5x5 cyclic Latin square over the five levels, rows shuffled, plus one
# extra randomly permuted repetition). The order is written out literally below so the
# script and the frozen protocol cannot drift apart. Do not edit or regenerate it.
# Run from project root as root.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT="$HERE/s15_runs"
RUNNER="$HERE/run_s15_validation_trial.sh"
mkdir -p "$ROOT"

ORDER_1="j200 j060 j020 j100 j140"
ORDER_2="j100 j140 j200 j060 j020"
ORDER_3="j140 j200 j060 j020 j100"
ORDER_4="j020 j100 j140 j200 j060"
ORDER_5="j060 j020 j100 j140 j200"
ORDER_6="j060 j200 j020 j140 j100"

for i in 1 2 3 4 5 6; do
  eval "SEQ=\$ORDER_$i"
  echo "=== S15 Repetition $i / 6 : $SEQ ==="
  for c in $SEQ; do
    bash "$RUNNER" "$ROOT/20260913_s15_${c}_r$i" "v${c#j}$i" "$c" no_action
  done
done
echo "S15 batch complete."
