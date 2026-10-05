#!/bin/bash
# G.8275.1 software S-plane testbed - TWO-SEGMENT topology with a Boundary Clock.
#
#   [gma]--+                      +--[ru1]
#          |  brUP   [bc]   brDN  |
#   [gmb]--+--(v-bc-up)  (v-bc-dn)+--[ru2]
#                                 +--[ru3]
#
# The BC is slave upstream / master downstream, so RUs see stepsRemoved=2 (GM->BC->RU),
# which makes A8 (rogue BC) and B7 (topology change) observable. Two bridges = two segments.
set -euo pipefail
NODES="gma gmb bc ru1 ru2 ru3"
teardown(){ for n in $NODES; do ip netns del $n 2>/dev/null||true; done
  ip link del brUP 2>/dev/null||true; ip link del brDN 2>/dev/null||true; }
teardown
for BR in brUP brDN; do ip link add $BR type bridge; ip link set $BR up
  echo 0 > /sys/class/net/$BR/bridge/multicast_snooping 2>/dev/null||true; done
mkport(){ # $1 netns $2 ifname $3 bridge $4 mac
  ip link add $2 type veth peer name p-$2
  ip link set p-$2 master $3; ip link set p-$2 up
  ip link set $2 netns $1
  ip netns exec $1 ip link set lo up
  ip netns exec $1 ip link set $2 address $4
  ip netns exec $1 ip link set $2 up; }
for n in $NODES; do ip netns add $n; done
# GM segment (brUP)
mkport gma v-gma brUP 02:00:00:00:00:0a
mkport gmb v-gmb brUP 02:00:00:00:00:0b
mkport bc  v-bc-up brUP 02:00:00:00:00:01
# RU segment (brDN)
mkport bc  v-bc-dn brDN 02:00:00:00:00:02
mkport ru1 v-ru1 brDN 02:00:00:00:00:0c
mkport ru2 v-ru2 brDN 02:00:00:00:00:0d
mkport ru3 v-ru3 brDN 02:00:00:00:00:0e
echo "=== topology up (2 segments, BC in the middle) ==="
for n in $NODES; do echo -n "$n: "; ip netns exec $n ip -br link show | grep -E "v-" | tr '\n' ' '; echo; done
