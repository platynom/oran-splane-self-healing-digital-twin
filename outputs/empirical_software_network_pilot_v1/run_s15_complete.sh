#!/usr/bin/env bash
# ONE COMMAND: verify -> smoke -> batch -> evaluate -> rebuild the full dataset package.
# Frozen by S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json. Run as root from this directory.
#
# Every stage is a hard gate: if a stage fails the script stops and nothing downstream runs, so a
# failure can never be mistaken for a result. Nothing is ever deleted, tuned, or retried selectively.
# Safe to re-run after an interruption: completed trials are skipped, an incomplete trial stops it.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"
LOG="$HERE/s15_complete_console.log"
exec > >(tee -a "$LOG") 2>&1
say() { echo; echo "=============== $* ==============="; }

say "STAGE 0  preflight"
[ "$(id -u)" = "0" ] || { echo "FATAL: must run as root"; exit 1; }
for c in ip tc ptp4l tcpdump pmc python3; do
  command -v "$c" >/dev/null || { echo "FATAL: missing required command: $c"; exit 1; }
done
if pgrep -f "run_s15_validation_trial.sh" >/dev/null 2>&1; then
  echo "FATAL: an S15 trial is already running. Wait for it, or stop it deliberately."; exit 1
fi
echo "ptp4l: $(ptp4l -v 2>&1 | head -n1)"
echo "started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

say "STAGE 1  frozen-artifact integrity"
python3 - <<'PY'
import json, hashlib, sys
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
fr = json.load(open('S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json'))['frozen_rule']
m = {'live_detector_sha256': 'live_detect_and_act.py',
     's15_trial_runner_sha256': 'run_s15_validation_trial.sh',
     's15_batch_runner_sha256': 'run_s15_validation_batch.sh',
     's15_evaluator_sha256': 'evaluate_s15.py',
     's15_smoke_runner_sha256': 'run_s15_smoke.sh',
     's15_smoke_checker_sha256': 'check_s15_smoke.py',
     's15_apply_helper_sha256': 'apply_impairment.py',
     's15_complete_runner_sha256': 'run_s15_complete.sh',
     'dataset_builder_sha256': 'prepare_s14_dataset.py',
     'workbook_builder_sha256': 'build_s14_packet_xlsx.py'}
bad = [f for k, f in m.items() if fr[k] != sha(f)]
for k, f in m.items():
    print(("OK   " if fr[k] == sha(f) else "WRONG"), sha(f), f)
if bad:
    print("FATAL: these files do not match the frozen protocol:", bad); sys.exit(1)
print("all frozen artifacts verify")
PY

say "STAGE 2  isolated smoke run (excluded from estimation by construction)"
bash "$HERE/run_s15_smoke.sh"

say "STAGE 3  the 30-trial batch"
bash "$HERE/run_s15_validation_batch.sh"

say "STAGE 4  inventory"
echo "run directories: $(ls s15_runs | wc -l)"
ls s15_runs
UNSEALED=$(find s15_runs -mindepth 1 -maxdepth 1 -type d '!' -exec test -f '{}/source_manifest.sha256' ';' -print | wc -l)
echo "unsealed run directories: $UNSEALED"

say "STAGE 5  frozen evaluation"
python3 "$HERE/evaluate_s15.py"

say "STAGE 6  rebuild the complete dataset package (CSV sources, then workbook)"
python3 "$HERE/prepare_s14_dataset.py"
python3 "$HERE/build_s14_packet_xlsx.py"
cat s14_dataset/s14_full_detail_reconciliation.json

say "STAGE 7  final manifest"
python3 - <<'PY'
import hashlib, json, os
from pathlib import Path
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
out = {"generated_utc": __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
       "protocol": "S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json",
       "artifacts": {}}
for f in sorted(["S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json",
                 "S15_INDEPENDENT_VALIDATION_EVALUATION.json",
                 "s14_dataset/s14_packets.csv", "s14_dataset/s14_runs.csv",
                 "s14_dataset/s14_events.csv", "s14_dataset/s14_decisions.csv",
                 "s14_dataset/s14_receiver_log.csv", "s14_dataset/s14_receiver_transitions.csv",
                 "s14_dataset/s14_outcomes.csv",
                 "s14_dataset/s14_full_detail_reconciliation.json",
                 "s14_dataset/S14_empirical_full_packet_streamed.xlsx"]):
    if Path(f).is_file():
        out["artifacts"][f] = {"sha256": sha(f), "bytes": os.path.getsize(f)}
Path("S15_DELIVERY_MANIFEST.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
PY

say "DONE"
echo "finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Nothing in this run was interpreted. Read S15_INDEPENDENT_VALIDATION_EVALUATION.json for the result."
