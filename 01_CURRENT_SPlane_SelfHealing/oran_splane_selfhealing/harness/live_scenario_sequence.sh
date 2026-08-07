#!/usr/bin/env bash
# Sequential real ptp4l scenarios for the recommendation-only live-loop demo.
set -euo pipefail
DURATION="${1:-210}"
OUT_DIR="${2:-results/live/mixed_pcaps}"
mkdir -p "$OUT_DIR"
for scenario in pdv loss holdover; do
  echo "phase=$scenario utc=$(date -u +%FT%TZ) duration_s=$DURATION"
  bash ./harness/netem_harness.sh "$scenario" "$DURATION" "$OUT_DIR/${scenario}.pcap"
done
echo "phase=complete utc=$(date -u +%FT%TZ)"
