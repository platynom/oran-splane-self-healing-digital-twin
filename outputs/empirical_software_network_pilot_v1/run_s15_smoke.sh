#!/usr/bin/env bash
# One isolated S15 smoke run. Excluded from S15 estimation by construction: it is written to
# s15_smoke/, not s15_runs/, and evaluate_s15.py reads only s15_runs/.
# Required by S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json before the batch may start.
# Run from project root as root. Failed smoke runs are preserved, never deleted.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$HERE/s15_smoke/$STAMP"
mkdir -p "$HERE/s15_smoke"
echo "=== S15 smoke run -> $OUT ==="
bash "$HERE/run_s15_validation_trial.sh" "$OUT" "smk1" "j100" no_action
python3 "$HERE/check_s15_smoke.py" "$OUT"
