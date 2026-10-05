#!/bin/bash
# Live on-wire runner for the three coverage-gap scenarios (items 1-3).
# Usage: run_gap.sh <C1_removal|C2_malformed|C3_wholesecond> <dur>
# All faults produced ON THE WIRE against the real linuxptp G.8275.1 testbed.
# Clock-safe: netns only, software timestamping, host clock never touched.
set -uo pipefail
SC="$1"; DUR="${2:-34}"; REP="${3:-0}"; cd /opt/sptb
GMID="020000fffe00000a"
# per-rep randomised parameters (reproducible from rep number)
eval "$(python3 /opt/sptb/run/randparams.py $REP 2>/dev/null | python3 -c '
import json,sys
d=json.load(sys.stdin)
for k in ("c1_down_pct","c2_gap_ms","c3_gap_ms"): print(f"P_{k}={d[k]}")
' 2>/dev/null)"
P_c1_down_pct="${P_c1_down_pct:-65}"; P_c2_gap_ms="${P_c2_gap_ms:-125}"; P_c3_gap_ms="${P_c3_gap_ms:-125}"

case "$SC" in
  C1_removal)     CLASS=attack; FID=C1; DESC="On-path selective interception: BC downstream port (v-bc-dn) blackholed for a sustained sub-window - RUs starved of Sync/Announce below the rate the BC declares (netem unavailable in this kernel, so realised as a link blackhole)" ;;
  C2_malformed)   CLASS=attack; FID=C2; DESC="Malformed/fuzzed PTP injected on RU segment (spoofed GM id): versionPTP=3, messageLength=20, messageType=0xF, controlField=0x63 - O-RAN WG11 24.2.1.2" ;;
  C3_wholesecond) CLASS=attack; FID=C3; DESC="Whole-second field abuse: forged Announce (spoofed GM id) leap61=1, currentUtcOffset=0 (true=37), timeTraceable/UTCvalid stripped - IEEE 1588-2019 timePropertiesDS 8.2.4; leap-second handling 9.4" ;;
  *) echo "unknown scenario $SC"; exit 1 ;;
esac

bash ./run/clean_all.sh >/dev/null 2>&1
bash ./run/topology.sh >/dev/null 2>&1
rm -rf cap/$SC; mkdir -p cap/$SC
cat > cap/$SC/context.json <<J
{ "scenario":"$SC", "class":"$CLASS", "fault_id":"$FID", "rep":901,
  "gm_allowlist":["020000fffe00000a","020000fffe00000b"],
  "provisioned_backup_gm":"020000fffe00000b",
  "expected_bc_identity":"020000fffe000001",
  "expected_client_identities":["020000fffe00000c","020000fffe00000d","020000fffe00000e"],
  "expected_steps_removed_at_ru":1, "maintenance_window_open":false, "leap_window_open":false,
  "description":"$DESC" }
J

bash ./run/start.sh $SC >/dev/null 2>&1
sleep 8
REMAIN=$((DUR-8)); [ $REMAIN -lt 5 ] && REMAIN=5

case "$SC" in
  C1_removal)
    # sustained blackhole of the BC->RU timing path for a randomised fraction of the
    # post-warmup window, then restore so re-lock is observable. Suppresses BC Sync below declared.
    DOWN=$((REMAIN*P_c1_down_pct/100)); TAIL=$((REMAIN-DOWN)); [ $TAIL -lt 4 ] && TAIL=4
    echo "blackhole v-bc-dn for ${DOWN}s (${P_c1_down_pct}%), restore for ${TAIL}s" >cap/$SC/inject.log
    ip netns exec bc ip link set v-bc-dn down 2>>cap/$SC/inject.log
    sleep $DOWN
    ip netns exec bc ip link set v-bc-dn up 2>>cap/$SC/inject.log
    sleep $TAIL ;;
  C2_malformed)
    ip netns exec ru3 python3 run/inject_malformed.py v-ru3 $REMAIN $GMID $P_c2_gap_ms >cap/$SC/inject.log 2>&1 &
    IJ=$!; sleep $REMAIN; kill $IJ 2>/dev/null ;;
  C3_wholesecond)
    ip netns exec ru3 python3 run/inject_wholesecond.py v-ru3 $REMAIN $GMID $P_c3_gap_ms >cap/$SC/inject.log 2>&1 &
    IJ=$!; sleep $REMAIN; kill $IJ 2>/dev/null ;;
esac

bash ./run/stop.sh $SC >/dev/null 2>&1
bash ./run/clean_all.sh >/dev/null 2>&1
python3 ptp_deep_extract.py cap/$SC/dn.pcap cap/$SC/${SC}.dn.deep.csv 2>&1 | tail -1
echo "run_gap $SC (dur $DUR) complete"
