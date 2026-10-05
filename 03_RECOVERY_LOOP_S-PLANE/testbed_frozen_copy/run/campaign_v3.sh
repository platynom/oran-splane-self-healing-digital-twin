#!/bin/bash
# campaign_v3: randomized campaign over ALL software scenarios (existing 11 + 3 coverage),
# scored by BOTH the frozen rule (decision.json) and frozen v2 (decision_v2.json).
# Usage: campaign_v3.sh <reps> <first_rep>. Resumable: a run with decision_v2.json is skipped.
# Existing scenarios keep DUR=45 (their failover/onset timing needs it); C scenarios shorter.
set -uo pipefail
cd /opt/sptb
REPS="${1:-12}"; FIRST="${2:-1}"
EXIST="baseline A1_rogue_master A2_sync_spoof A3_replay A5_dos_flood A8_rogue_bc B2_gm_failover B3_pdv_congestion B7_topology_change B_unplanned_failover B_bc_replacement"
COVER="C1_removal C2_malformed C3_wholesecond"
LOG=results/campaign_v3.log
mkdir -p results
hard_clean(){ pkill -f "ptp4l -f /opt/sptb" 2>/dev/null; pkill -f "tcpdump -i br" 2>/dev/null; sleep 1; }
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a $LOG; }

log "=== campaign_v3 start: reps ${FIRST}..$((FIRST+REPS-1)) ==="
for rep in $(seq $FIRST $((FIRST+REPS-1))); do
  # ---- existing scenarios (topology + scenarios.sh) ----
  for s in $EXIST; do
    RUN="${s}__r${rep}"
    [ -f cap/$RUN/decision_v2.json ] && { log "skip $RUN (done)"; continue; }
    ATT=0
    while [ $ATT -lt 2 ]; do
      ATT=$((ATT+1)); hard_clean
      ./run/topology.sh >/dev/null 2>&1
      rm -rf cap/$s cap/$RUN
      ./run/pmc_log.sh $s 40 >/dev/null 2>&1 & PMC=$!
      ./run/scenarios.sh $s 45 $rep >/dev/null 2>&1
      kill $PMC 2>/dev/null; wait $PMC 2>/dev/null
      mkdir -p cap/$RUN && cp -r cap/$s/. cap/$RUN/ 2>/dev/null
      PKTS=$(python3 ptp_deep_extract.py cap/$RUN/dn.pcap cap/$RUN/${RUN}.dn.deep.csv 2>/dev/null | grep -oE 'ptp=[0-9]+' | cut -d= -f2)
      if [ -z "$PKTS" ] || [ "$PKTS" -lt 100 ]; then
        rm -rf cap/$RUN
        [ $ATT -lt 2 ] && { log "  $RUN infra-fail (${PKTS:-0} pkts) retry"; continue; }
        log "  $RUN FAILED after retry (${PKTS:-0} pkts) - discarded"; break
      fi
      python3 run/decision_rule.py cap/$RUN >/dev/null 2>&1
      python3 run/score_v2.py cap/$RUN >/dev/null 2>&1
      fv=$(python3 -c "import json;print(json.load(open('cap/$RUN/decision.json'))['verdict'])" 2>/dev/null||echo ERR)
      vv=$(python3 -c "import json;print(json.load(open('cap/$RUN/decision_v2.json'))['verdict'])" 2>/dev/null||echo ERR)
      log "  $RUN frozen=$fv v2=$vv (${PKTS}p)"; break
    done
  done
  # ---- coverage scenarios (run_gap.sh is self-contained) ----
  for s in $COVER; do
    RUN="${s}__r${rep}"
    [ -f cap/$RUN/decision_v2.json ] && { log "skip $RUN (done)"; continue; }
    D=40; [ "$s" = "C1_removal" ] && D=44
    ATT=0
    while [ $ATT -lt 2 ]; do
      ATT=$((ATT+1))
      rm -rf cap/$s            # HARDENING: never let a stale capture satisfy the guard
      bash ./run/run_gap.sh $s $D $rep >/dev/null 2>&1
      RC=$?
      PKTS=$(python3 -c "import csv;print(sum(1 for _ in open('cap/$s/${s}.dn.deep.csv')))" 2>/dev/null||echo 0)
      if [ $RC -ne 0 ] || [ "$PKTS" -lt 100 ]; then
        [ $ATT -lt 2 ] && { log "  $RUN infra-fail rc=$RC pkts=$PKTS - retry"; continue; }
        log "  $RUN FAILED after retry - discarded"; break
      fi
      rm -rf cap/$RUN; mkdir -p cap/$RUN && cp -r cap/$s/. cap/$RUN/ 2>/dev/null
      python3 run/decision_rule.py cap/$RUN >/dev/null 2>&1
      python3 run/score_v2.py cap/$RUN >/dev/null 2>&1
      fv=$(python3 -c "import json;print(json.load(open('cap/$RUN/decision.json'))['verdict'])" 2>/dev/null||echo ERR)
      vv=$(python3 -c "import json;print(json.load(open('cap/$RUN/decision_v2.json'))['verdict'])" 2>/dev/null||echo ERR)
      log "  $RUN frozen=$fv v2=$vv (${PKTS}r)"; break
    done
  done
  log "=== rep $rep complete ==="
done
hard_clean
log "=== campaign_v3 DONE ==="
