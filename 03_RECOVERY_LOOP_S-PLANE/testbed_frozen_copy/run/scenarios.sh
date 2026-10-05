#!/bin/bash
# Scenario library (RANDOMISED). Usage: scenarios.sh <scenario> <dur> <rep>
# Each scenario writes a context manifest + captures + per-node logs. All faults are
# produced ON THE WIRE against the real linuxptp testbed - none simulated.
#
# RANDOMISATION: run/randparams.py <rep> yields per-rep attacker identities, priorities,
# timings, burst sizes and jitter magnitudes, seeded reproducibly from the rep number.
# This makes each replicate a genuinely different instance of the same attack CLASS.
set -uo pipefail
SC="$1"; DUR="${2:-60}"; REP="${3:-0}"; OUT=/opt/sptb/cap/$SC; mkdir -p $OUT
eval "$(python3 /opt/sptb/run/randparams.py $REP | python3 -c '
import json,sys
d=json.load(sys.stdin)
for k,v in d.items(): print(f"P_{k}={v!r}".replace("'\''",""))
')"
# clamp a jittered sleep to >=5s
J(){ local base=$1 j=${P_onset_jitter_s:-0}; local v=$((base+j)); [ $v -lt 5 ] && v=5; echo $v; }

manifest(){ cat > $OUT/context.json <<J
{ "scenario":"$SC", "class":"$1", "fault_id":"$2",
  "rep":$REP,
  "gm_allowlist":["020000fffe00000a","020000fffe00000b"],
  "provisioned_backup_gm":"020000fffe00000b",
  "expected_bc_identity":"020000fffe000001",
  "expected_client_identities":["020000fffe00000c","020000fffe00000d","020000fffe00000e"],
  "expected_steps_removed_at_ru":1,
  "maintenance_window_open":$3,
  "randomised_params_seed":$REP,
  "description":"$4" }
J
}
start_clean(){ /opt/sptb/run/start.sh $SC >/dev/null 2>&1; }
stop_all(){ /opt/sptb/run/stop.sh $SC >/dev/null 2>&1; }

case "$SC" in
 baseline)
   manifest healthy none false "All nodes nominal, GM-A grandmaster via BC to RUs"
   start_clean; sleep $DUR; stop_all ;;

 A1_rogue_master)
   manifest attack A1 false "Rogue ptp4l on RU segment, off-allow-list id ${P_rogue_id}, superior priority2=${P_rogue_priority2}"
   start_clean; sleep $(J 25)
   cat /opt/sptb/cfg/g87251.base > /opt/sptb/cfg/rogue.cfg
   printf "\npriority2                       %s\nclockClass                      %s\n[v-rogue]\nserverOnly                      1\n" "$P_rogue_priority2" "$P_rogue_clockclass" >> /opt/sptb/cfg/rogue.cfg
   ip netns add rogue 2>/dev/null||true
   ip link add v-rogue type veth peer name p-rogue; ip link set p-rogue master brDN; ip link set p-rogue up
   ip link set v-rogue netns rogue; ip netns exec rogue ip link set lo up
   ip netns exec rogue ip link set v-rogue address "$P_rogue_mac"; ip netns exec rogue ip link set v-rogue up
   ip netns exec rogue ptp4l -f /opt/sptb/cfg/rogue.cfg -i v-rogue -m --uds_address=/var/run/p.rogue --uds_ro_address=/var/run/pr.rogue >$OUT/rogue.log 2>&1 & echo $! >$OUT/rogue.pid
   sleep $((DUR-25)); [ -f $OUT/rogue.pid ] && kill $(cat $OUT/rogue.pid) 2>/dev/null
   stop_all; ip netns del rogue 2>/dev/null||true; ip link del v-rogue 2>/dev/null||true ;;

 A2_sync_spoof)
   manifest attack A2 false "Forged Sync from off-allow-list ${P_inject_id}, burst ${P_inject_burst}, never Announce"
   start_clean; sleep $(J 25)
   ip netns exec ru3 python3 /opt/sptb/run/inject.py v-ru3 sync $((DUR-25)) "$P_inject_id" "$P_inject_burst" "$P_inject_gap_ms" "$P_inject_seconds" >$OUT/inject.log 2>&1 &
   IJ=$!; sleep $((DUR-25)); kill $IJ 2>/dev/null; stop_all ;;

 A3_replay)
   manifest attack A3 false "Captured frames retransmitted, loop=${P_replay_loops} (stale timestamps, reused sequenceId)"
   start_clean; sleep $(J 20)
   timeout 10 tcpdump -i brDN -w $OUT/replay_src.pcap -s0 -c "$P_replay_count" 2>/dev/null || true
   sleep 5
   ip netns exec ru3 tcpreplay -i v-ru3 --loop="$P_replay_loops" $OUT/replay_src.pcap >$OUT/replay.log 2>&1 || true
   sleep $((DUR-40)); stop_all ;;

 A5_dos_flood)
   manifest attack A5 false "PTP flood on RU segment, burst ${P_flood_burst}/${P_flood_gap_ms}ms from ${P_flood_src}"
   start_clean; sleep $(J 25)
   ip netns exec ru3 python3 /opt/sptb/run/flood.py v-ru3 $((DUR-25)) "$P_flood_burst" "$P_flood_gap_ms" "$P_flood_src" >$OUT/flood.log 2>&1 &
   FL=$!; sleep $((DUR-25)); kill $FL 2>/dev/null; stop_all ;;

 A8_rogue_bc)
   manifest attack A8 false "Rogue BOUNDARY CLOCK ${P_rbc_id_up} priority2=${P_rbc_priority2}, relays real GM with stepsRemoved incremented"
   start_clean; sleep $(J 25)
   cat /opt/sptb/cfg/g87251.base > /opt/sptb/cfg/rbc.cfg
   printf "\npriority2                       %s\n[v-rbc-up]\nserverOnly                      0\n[v-rbc-dn]\nserverOnly                      1\n" "$P_rbc_priority2" >> /opt/sptb/cfg/rbc.cfg
   ip netns add rbc 2>/dev/null||true
   ip link add v-rbc-up type veth peer name p-rbc-up; ip link set p-rbc-up master brUP; ip link set p-rbc-up up
   ip link add v-rbc-dn type veth peer name p-rbc-dn; ip link set p-rbc-dn master brDN; ip link set p-rbc-dn up
   ip link set v-rbc-up netns rbc; ip link set v-rbc-dn netns rbc; ip netns exec rbc ip link set lo up
   ip netns exec rbc ip link set v-rbc-up address "$P_rbc_up_mac"; ip netns exec rbc ip link set v-rbc-dn address "$P_rbc_dn_mac"
   ip netns exec rbc ip link set v-rbc-up up; ip netns exec rbc ip link set v-rbc-dn up
   ip netns exec rbc ptp4l -f /opt/sptb/cfg/rbc.cfg -i v-rbc-up -i v-rbc-dn -m --uds_address=/var/run/p.rbc --uds_ro_address=/var/run/pr.rbc >$OUT/rbc.log 2>&1 & echo $! >$OUT/rbc.pid
   sleep $((DUR-25)); [ -f $OUT/rbc.pid ] && kill $(cat $OUT/rbc.pid) 2>/dev/null
   stop_all; ip netns del rbc 2>/dev/null||true; ip link del v-rbc-up 2>/dev/null||true; ip link del v-rbc-dn 2>/dev/null||true ;;

 B2_gm_failover)
   manifest benign B2 true "PLANNED: GM-A withdrawn (maintenance open), GM-B (on allow-list) takes over"
   start_clean; sleep $(J 30)
   [ -f $OUT/gma.pid ] && kill $(cat $OUT/gma.pid) 2>/dev/null
   sleep $((DUR-30)); stop_all ;;

 B_unplanned_failover)
   # CRITICAL BENIGN GAP #1: GM-A dies with NO maintenance window. Provisioned GM-B takes
   # over. From packets alone this is INDISTINGUISHABLE from an attack that suppressed GM-A;
   # the honest verdict is UNKNOWN, not BENIGN. Tests that the rule does not over-claim.
   manifest benign B_UNPLANNED false "UNPLANNED: GM-A crashes, NO maintenance window; GM-B (provisioned) elected"
   start_clean; sleep $(J 30)
   [ -f $OUT/gma.pid ] && kill -9 $(cat $OUT/gma.pid) 2>/dev/null
   sleep $((DUR-30)); stop_all ;;

 B_bc_replacement)
   # CRITICAL BENIGN GAP #2: the in-path boundary clock is swapped for a NEW unit during an
   # open maintenance window. The replacement's identity is added to the provisioned
   # inventory (that is what "planned" means). Tests that a legitimate BC swap is not
   # mistaken for A8 (rogue BC). The new BC id is provisioned via context.json below.
   manifest benign B_BCREPL true "PLANNED BC swap during maintenance; replacement id 020000fffe0000b1 is provisioned"
   # provision the replacement BC into the allow context
   python3 - "$OUT/context.json" <<'PJ'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
d["expected_bc_identity_secondary"]="020000fffe0000b1"
json.dump(d,open(p,"w"),indent=2)
PJ
   start_clean; sleep $(J 25)
   # bring down the real BC downstream port, stand up a provisioned replacement BC
   [ -f $OUT/bc.pid ] && kill $(cat $OUT/bc.pid) 2>/dev/null
   cat /opt/sptb/cfg/g87251.base > /opt/sptb/cfg/bc2.cfg
   printf "\npriority2                       120\n[v-bc2-up]\nserverOnly                      0\n[v-bc2-dn]\nserverOnly                      1\n" >> /opt/sptb/cfg/bc2.cfg
   ip netns add bc2 2>/dev/null||true
   ip link add v-bc2-up type veth peer name p-bc2-up; ip link set p-bc2-up master brUP; ip link set p-bc2-up up
   ip link add v-bc2-dn type veth peer name p-bc2-dn; ip link set p-bc2-dn master brDN; ip link set p-bc2-dn up
   ip link set v-bc2-up netns bc2; ip link set v-bc2-dn netns bc2; ip netns exec bc2 ip link set lo up
   ip netns exec bc2 ip link set v-bc2-up address 02:00:00:00:00:b1; ip netns exec bc2 ip link set v-bc2-dn address 02:00:00:00:00:b2
   ip netns exec bc2 ip link set v-bc2-up up; ip netns exec bc2 ip link set v-bc2-dn up
   ip netns exec bc2 ptp4l -f /opt/sptb/cfg/bc2.cfg -i v-bc2-up -i v-bc2-dn -m --uds_address=/var/run/p.bc2 --uds_ro_address=/var/run/pr.bc2 >$OUT/bc2.log 2>&1 & echo $! >$OUT/bc2.pid
   sleep $((DUR-25)); [ -f $OUT/bc2.pid ] && kill $(cat $OUT/bc2.pid) 2>/dev/null
   stop_all; ip netns del bc2 2>/dev/null||true; ip link del v-bc2-up 2>/dev/null||true; ip link del v-bc2-dn 2>/dev/null||true ;;

 B3_pdv_congestion)
   manifest benign B3 false "Congestion on the BC->RU timing path: 1mbit tbf bottleneck with competing non-PTP background traffic (burst-intensity from pdv params ${P_pdv_delay_ms}/${P_pdv_jitter_ms}); real queueing delay + PDV, no loss, no protocol anomaly"
   start_clean; sleep $(J 20)
   # DEFECT FIX 2026-09-20 (v2): this kernel has NO sch_netem ("qdisc kind is unknown") and the
   # original line swallowed that with 2>/dev/null||true, so B3 injected NOTHING for the entire
   # prior campaign - it was a mislabelled baseline (verified: PDV identical to baseline).
   # Replaced with a PHYSICAL congestion model: a token-bucket bottleneck (sch_tbf, verified
   # present) on the BC->RU timing path, plus competing NON-PTP background traffic through that
   # same bottleneck. PTP then queues behind data-plane traffic - which is what fronthaul PDV
   # actually is. Deep limit => packets are DELAYED, not dropped, so this degrades timing
   # WITHOUT starving the message rate (it must stay BENIGN, not become packet removal).
   # Any failure is now FATAL and recorded; it is never silently ignored again.
   B3BURST=$(( (P_pdv_delay_ms+5)/2 ))        # 3,5,8ms -> 4,5,6 frames per burst
   B3GAP=$(( 100 - 15*P_pdv_jitter_ms ))      # 2,3,4ms -> 70,55,40 ms between bursts
   if ip netns exec bc tc qdisc add dev v-bc-dn root tbf rate 1mbit burst 3000 limit 40000 2>>$OUT/impair.log; then
     echo "B3 bottleneck applied: tbf 1mbit limit 40000 on v-bc-dn; bg burst=$B3BURST gap=${B3GAP}ms" >>$OUT/impair.log
     ip netns exec bc python3 /opt/sptb/run/bg_traffic.py v-bc-dn $((DUR-22)) $B3BURST $B3GAP >>$OUT/impair.log 2>&1 &
     BG=$!
     sleep $((DUR-20)); kill $BG 2>/dev/null
     ip netns exec bc tc -s qdisc show dev v-bc-dn >>$OUT/impair.log 2>&1
   else
     echo "B3 RUN INVALID - bottleneck not applied" >>$OUT/impair.log
     sleep $((DUR-20))
   fi
   stop_all ;;

 B7_topology_change)
   manifest benign B7 true "PLANNED: RU3 link bounced and re-homed (maintenance) - stepsRemoved/path re-measured"
   start_clean; sleep $(J 25)
   ip netns exec ru3 ip link set v-ru3 down; sleep 8; ip netns exec ru3 ip link set v-ru3 up
   sleep $((DUR-33)); stop_all ;;

 *) echo "unknown scenario $SC"; exit 1 ;;
esac
echo "scenario $SC (rep $REP) complete -> $OUT"
