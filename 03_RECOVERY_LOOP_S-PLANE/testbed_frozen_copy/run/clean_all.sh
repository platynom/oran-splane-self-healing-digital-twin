#!/bin/bash
# Full teardown of the S-plane testbed: stop daemons + captures, delete namespaces/bridges.
pkill -f "ptp4l -f /opt/sptb" 2>/dev/null
pkill -f "tcpdump -i br" 2>/dev/null
sleep 1
for n in gma gmb bc ru1 ru2 ru3 rogue rbc bc2; do ip netns del $n 2>/dev/null; done
for l in brUP brDN; do ip link del $l 2>/dev/null; done
for l in $(ip -o link show 2>/dev/null | awk -F': ' '/(v-|p-)/{print $2}' | cut -d@ -f1); do ip link del $l 2>/dev/null; done
sleep 1
echo "clean_all done"
