#!/usr/bin/env bash
# Legitimate two-master BMCA re-parenting experiment over a software L2 bridge.
set -euo pipefail

PRE_SECONDS="${1:-90}"
POST_SECONDS="${2:-90}"
OUT_PCAP="${3:-results/live/planned_gm_failover.pcap}"
TIMELINE="${4:-results/live/planned_gm_failover_harness.txt}"
BR="gmbridge"
NS_A="gm_master_a"
NS_B="gm_master_b"
NS_S="gm_slave"

cleanup() {
  set +e
  kill "${A_PID:-}" "${B_PID:-}" "${S_PID:-}" "${TCP_PID:-}" 2>/dev/null
  for ns in "$NS_A" "$NS_B" "$NS_S"; do ip netns del "$ns" 2>/dev/null; done
  ip link del "$BR" 2>/dev/null
}
trap cleanup EXIT
[ "$(id -u)" -eq 0 ] || { echo "ERROR: run as root" >&2; exit 2; }
for tool in ip ptp4l tcpdump; do command -v "$tool" >/dev/null || { echo "ERROR: missing $tool" >&2; exit 2; }; done
cleanup
trap cleanup EXIT
mkdir -p "$(dirname "$TIMELINE")"
exec > >(tee "$TIMELINE") 2>&1

ip link add "$BR" type bridge
ip link set "$BR" up
for spec in "$NS_A:gmar:gmaa" "$NS_B:gmbr:gmbb" "$NS_S:gmsr:gmss"; do
  IFS=: read -r ns root_if ns_if <<<"$spec"
  ip netns add "$ns"
  ip link add "$root_if" type veth peer name "$ns_if"
  ip link set "$ns_if" netns "$ns"
  ip link set "$root_if" master "$BR"
  ip link set "$root_if" up
  ip netns exec "$ns" ip link set lo up
  ip netns exec "$ns" ip link set "$ns_if" up
done

mkdir -p "$(dirname "$OUT_PCAP")"
tcpdump -i gmsr -w "$OUT_PCAP" --time-stamp-precision=nano "ether proto 0x88f7" &
TCP_PID=$!

write_master_config() {
  local path="$1" priority="$2" socket="$3"
  cat >"$path" <<EOF
[global]
network_transport L2
time_stamping software
delay_mechanism E2E
logSyncInterval -3
logMinDelayReqInterval -3
logAnnounceInterval -2
announceReceiptTimeout 3
priority1 $priority
clockClass 248
uds_address $socket
[gmaa]
masterOnly 1
EOF
}

write_master_config /tmp/gm_a.conf 100 /var/run/ptp4l-gm-a
# Replace the interface section for master B.
sed 's/\[gmaa\]/[gmbb]/' /tmp/gm_a.conf | sed 's/priority1 100/priority1 150/' | sed 's#ptp4l-gm-a#ptp4l-gm-b#' >/tmp/gm_b.conf
cat >/tmp/gm_slave.conf <<'EOF'
[global]
network_transport L2
time_stamping software
delay_mechanism E2E
logSyncInterval -3
logMinDelayReqInterval -3
logAnnounceInterval -2
announceReceiptTimeout 3
uds_address /var/run/ptp4l-gm-slave
EOF

ip netns exec "$NS_A" ptp4l -f /tmp/gm_a.conf -i gmaa -m -q >/tmp/ptp4l_gm_a.log 2>&1 & A_PID=$!
ip netns exec "$NS_B" ptp4l -f /tmp/gm_b.conf -i gmbb -m -q >/tmp/ptp4l_gm_b.log 2>&1 & B_PID=$!
ip netns exec "$NS_S" ptp4l -f /tmp/gm_slave.conf -i gmss -s -m -q >/tmp/ptp4l_gm_slave.log 2>&1 & S_PID=$!

echo "phase=master_a_active seconds=$PRE_SECONDS utc=$(date -u +%FT%TZ)"
sleep "$PRE_SECONDS"
kill "$A_PID" 2>/dev/null || true
wait "$A_PID" 2>/dev/null || true
echo "phase=master_a_stopped_master_b_failover seconds=$POST_SECONDS utc=$(date -u +%FT%TZ)"
sleep "$POST_SECONDS"
echo "phase=complete utc=$(date -u +%FT%TZ) pcap=$OUT_PCAP"
