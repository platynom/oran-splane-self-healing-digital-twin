#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# S-plane realism harness: generate REAL PTP traffic over a veth pair and
# degrade it with `tc netem`, capturing a pcap the ingester can consume.
#
# Runs on any ordinary Linux box with root + linuxptp + tcpdump. NO special
# hardware / PTP NIC required (uses software timestamping over a veth pair).
#
# Usage:
#   sudo ./netem_harness.sh <scenario> <duration_s> <out_pcap>
#   scenario ∈ {baseline, pdv, loss, holdover, reorder}
#
# What each scenario emulates on the fronthaul link:
#   baseline  clean link (reference)
#   pdv       packet-delay variation / congestion  (benign H0-style)
#   loss      packet loss                          (benign H0-style)
#   reorder   packet reordering                    (benign H0-style)
#   holdover  master path blackout (extreme delay) (benign H0-style)
# Malicious spoof/replay (H1) is NOT injected here — that needs an active
# attacker and is out of scope for the netem harness by design.
# ---------------------------------------------------------------------------
set -euo pipefail

SCENARIO="${1:-baseline}"
DURATION="${2:-30}"
OUT_PCAP="${3:-results/tier2/netem_${SCENARIO}.pcap}"

NS="splane_slave"
VETH_M="splanem"   # master side (root ns)
VETH_S="splanes"   # slave side (moved into NS)

require() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' not found. Install it and re-run." >&2; exit 2; }; }
[ "$(id -u)" -eq 0 ] || { echo "ERROR: run as root (netns/tc/ptp4l need privileges)." >&2; exit 2; }
require ip; require tc; require tcpdump; require ptp4l

cleanup() {
  set +e
  kill "${PTP_M_PID:-}" "${PTP_S_PID:-}" "${TCPDUMP_PID:-}" 2>/dev/null
  ip netns del "$NS" 2>/dev/null
  ip link del "$VETH_M" 2>/dev/null
}
trap cleanup EXIT

mkdir -p "$(dirname "$OUT_PCAP")"

# 0) pre-clean any leftover state from a previously aborted run (prevents a
#    stale netns/veth from silently breaking this scenario's capture)
ip netns del "$NS" 2>/dev/null || true
ip link del "$VETH_M" 2>/dev/null || true
sleep 0.3

# 1) veth pair; move slave end into a namespace
ip netns add "$NS"
ip link add "$VETH_M" type veth peer name "$VETH_S"
ip link set "$VETH_S" netns "$NS"
ip addr add 10.99.0.1/24 dev "$VETH_M"; ip link set "$VETH_M" up
ip netns exec "$NS" ip addr add 10.99.0.2/24 dev "$VETH_S"
ip netns exec "$NS" ip link set "$VETH_S" up
ip netns exec "$NS" ip link set lo up

# 2) apply the impairment on the master egress
case "$SCENARIO" in
  baseline) tc qdisc add dev "$VETH_M" root netem delay 250us 20us distribution normal ;;
  pdv)      tc qdisc add dev "$VETH_M" root netem delay 400us 300us distribution normal ;;
  loss)     tc qdisc add dev "$VETH_M" root netem delay 250us 20us loss 5% ;;
  reorder)  tc qdisc add dev "$VETH_M" root netem delay 300us 50us reorder 25% 50% ;;
  holdover) tc qdisc add dev "$VETH_M" root netem delay 5ms 2ms loss 20% ;;
  *) echo "unknown scenario '$SCENARIO'" >&2; exit 2 ;;
esac
echo "netem applied for scenario=$SCENARIO"

# 3) capture PTP-over-Ethernet (Ethertype 0x88F7) on the master link, ns precision
tcpdump -i "$VETH_M" -w "$OUT_PCAP" --time-stamp-precision=nano "ether proto 0x88f7" &
TCPDUMP_PID=$!
sleep 1

# 4) PTP master (root ns) + slave (namespace), L2 + software timestamping
cat > /tmp/splane_ptp.conf <<'EOF'
[global]
network_transport L2
time_stamping     software
delay_mechanism   E2E
logSyncInterval   -3
logMinDelayReqInterval -3
tx_timestamp_timeout 50
EOF

ptp4l -f /tmp/splane_ptp.conf -i "$VETH_M" -m -q > /tmp/ptp4l_master.log 2>&1 &
PTP_M_PID=$!
ip netns exec "$NS" ptp4l -f /tmp/splane_ptp.conf -i "$VETH_S" -s -m -q > /tmp/ptp4l_slave.log 2>&1 &
PTP_S_PID=$!

echo "capturing for ${DURATION}s -> $OUT_PCAP"
sleep "$DURATION"

echo "done. slave servo tail:"; tail -n 3 /tmp/ptp4l_slave.log || true
echo "pcap: $OUT_PCAP"
