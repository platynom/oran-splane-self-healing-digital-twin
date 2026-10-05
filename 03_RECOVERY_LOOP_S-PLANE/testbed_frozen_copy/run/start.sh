#!/bin/bash
set -uo pipefail
SC="${1:-baseline}"; OUT=/opt/sptb/cap/$SC; mkdir -p $OUT
# Wait until every namespace interface actually exists and is UP. Without this, ptp4l can
# start before the veth is ready and dies with "failed to generate a clock identity",
# producing an empty capture. Reliability fix only - no protocol behaviour changes.
wait_ifaces(){
  for i in $(seq 1 100); do
    ok=1
    for spec in "gma v-gma" "gmb v-gmb" "bc v-bc-up" "bc v-bc-dn" "ru1 v-ru1" "ru2 v-ru2" "ru3 v-ru3"; do
      set -- $spec
      ip netns exec $1 ip link show $2 2>/dev/null | grep -q "state UP\|LOWER_UP" || ok=0
    done
    [ $ok -eq 1 ] && return 0
    sleep 0.1
  done
  echo "WARN: interfaces not ready after 10s" >&2; return 1
}
wait_ifaces
# capture BOTH segments
tcpdump -i brUP -w $OUT/up.pcap -s0 -U 2>$OUT/tcpdump_up.err & echo $! > $OUT/tcpu.pid
tcpdump -i brDN -w $OUT/dn.pcap -s0 -U 2>$OUT/tcpdump_dn.err & echo $! > $OUT/tcpd.pid
sleep 1
ip netns exec gma ptp4l -f /opt/sptb/cfg/gma.cfg -i v-gma -m --uds_address=/var/run/p.gma --uds_ro_address=/var/run/pr.gma >$OUT/gma.log 2>&1 & echo $! >$OUT/gma.pid
ip netns exec gmb ptp4l -f /opt/sptb/cfg/gmb.cfg -i v-gmb -m --uds_address=/var/run/p.gmb --uds_ro_address=/var/run/pr.gmb >$OUT/gmb.log 2>&1 & echo $! >$OUT/gmb.pid
ip netns exec bc  ptp4l -f /opt/sptb/cfg/bc.cfg -i v-bc-up -i v-bc-dn -m --uds_address=/var/run/p.bc --uds_ro_address=/var/run/pr.bc >$OUT/bc.log 2>&1 & echo $! >$OUT/bc.pid
for r in ru1 ru2 ru3; do ip netns exec $r ptp4l -f /opt/sptb/cfg/$r.cfg -i v-$r -m --uds_address=/var/run/p.$r --uds_ro_address=/var/run/pr.$r >$OUT/$r.log 2>&1 & echo $! >$OUT/$r.pid; done
echo "started $SC"
