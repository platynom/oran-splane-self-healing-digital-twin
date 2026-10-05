#!/usr/bin/env bash
# Two-path mechanism feasibility spike harness.
# Tests whether one slave ptp4l instance can hold two ports to a bridge,
# and how the port state machine and traffic behave under single-path impairment.
# This is a capability check only; no closed-loop recovery is performed.
set -euo pipefail

OUT="${1:-outputs/empirical_software_network_pilot_v1/spike_two_path}"
RUN_ID="${2:-spk1}"
SETTLE_DURATION="${SPIKE_SETTLE_SECONDS:-8}"
IMPAIR_DURATION="${SPIKE_IMPAIR_SECONDS:-12}"

die() { echo "ERROR: $*" >&2; exit 2; }
need() { command -v "$1" >/dev/null 2>&1 || die "required command unavailable: $1"; }
utc() { date -u +%FT%TZ; }
mono() { awk '{print $1}' /proc/uptime; }
valid_id() { [[ "$1" =~ ^[a-z0-9]{1,4}$ ]]; }

# Preflight check
[ "$(id -u)" = 0 ] || die "requires root inside isolated Linux testbed"
for x in ip tc ptp4l tcpdump sha256sum; do need "$x"; done
VERSION="$(ptp4l -v | head -n1)"
[ "$VERSION" = "3.1.1" ] || die "requires audited linuxptp 3.1.1; found $VERSION"

valid_id "$RUN_ID" || die "RUN_ID must be 1-4 lowercase alphanumeric chars"
[ ! -e "$OUT" ] || die "OUT directory must not already exist: $OUT"

P="ptp${RUN_ID}"
BR="${P}br"
NS_A="${P}a"
NS_B="${P}b"
NS_S="${P}s"

AR="${P}ar"; AN="${P}an"
BR_IF="${P}cr"; BN="${P}bn"
S1R="${P}s1r"; S1N="${P}s1n"
S2R="${P}s2r"; S2N="${P}s2n"

resource_exists() { ip link show "$1" >/dev/null 2>&1 || ip netns list | awk '{print $1}' | grep -Fxq "$1"; }
for x in "$BR" "$NS_A" "$NS_B" "$NS_S" "$AR" "$AN" "$BR_IF" "$BN" "$S1R" "$S1N" "$S2R" "$S2N"; do
  resource_exists "$x" && die "resource collision: $x"
done

CREATED_BR=0; CREATED_A=0; CREATED_B=0; CREATED_S=0

stop_owned() {
  set +e
  for pid in "${A_PID:-}" "${B_PID:-}" "${S_PID:-}" "${PMC_PID:-}"; do
    [ -n "$pid" ] && kill -TERM "$pid" 2>/dev/null
  done
  for pid in "${TCP1_PID:-}" "${TCP2_PID:-}"; do
    [ -n "$pid" ] && kill -INT "$pid" 2>/dev/null
  done
  for pid in "${A_PID:-}" "${B_PID:-}" "${S_PID:-}" "${PMC_PID:-}" "${TCP1_PID:-}" "${TCP2_PID:-}"; do
    [ -n "$pid" ] && wait "$pid" 2>/dev/null
  done
  [ "$CREATED_A" = 1 ] && ip netns del "$NS_A" 2>/dev/null
  [ "$CREATED_B" = 1 ] && ip netns del "$NS_B" 2>/dev/null
  [ "$CREATED_S" = 1 ] && ip netns del "$NS_S" 2>/dev/null
  [ "$CREATED_BR" = 1 ] && ip link del "$BR" 2>/dev/null
}
trap stop_owned EXIT

mkdir -p "$OUT"
: > "$OUT/events.log"
event() {
  printf 'run_id=%s phase=%s event=%s utc=%s monotonic_s=%s status=%s\n' \
    "$RUN_ID" "$1" "$2" "$(utc)" "$(mono)" "$3" >> "$OUT/events.log"
}

printf 'run_id=%s\nlinuxptp=%s\nmode=two_path_mechanism_feasibility_spike\nhost_clock_adjustment=disabled_by_free_running_1\nstarted_utc=%s\n' \
  "$RUN_ID" "$VERSION" "$(utc)" > "$OUT/run_environment.txt"

# Create bridge
ip link add "$BR" type bridge; CREATED_BR=1; ip link set "$BR" up

# Create Master A
ip netns add "$NS_A"; CREATED_A=1
ip link add "$AR" type veth peer name "$AN"
ip link set "$AN" netns "$NS_A"
ip link set "$AR" master "$BR"; ip link set "$AR" up
ip netns exec "$NS_A" ip link set lo up; ip netns exec "$NS_A" ip link set "$AN" up

# Create Master B
ip netns add "$NS_B"; CREATED_B=1
ip link add "$BR_IF" type veth peer name "$BN"
ip link set "$BN" netns "$NS_B"
ip link set "$BR_IF" master "$BR"; ip link set "$BR_IF" up
ip netns exec "$NS_B" ip link set lo up; ip netns exec "$NS_B" ip link set "$BN" up

# Create Slave with TWO veth pairs to bridge
ip netns add "$NS_S"; CREATED_S=1
ip link add "$S1R" type veth peer name "$S1N"
ip link set "$S1N" netns "$NS_S"
ip link set "$S1R" master "$BR"; ip link set "$S1R" up

ip link add "$S2R" type veth peer name "$S2N"
ip link set "$S2N" netns "$NS_S"
ip link set "$S2R" master "$BR"; ip link set "$S2R" up

ip netns exec "$NS_S" ip link set lo up
ip netns exec "$NS_S" ip link set "$S1N" up
ip netns exec "$NS_S" ip link set "$S2N" up

# Write configuration files
cat > "$OUT/master_a.conf" <<EOF
[global]
network_transport L2
time_stamping software
delay_mechanism E2E
free_running 1
logSyncInterval -3
logMinDelayReqInterval -3
logAnnounceInterval -2
announceReceiptTimeout 3
priority1 100
clockClass 248
uds_address /var/run/ptp4l-${P}-a
[$AN]
masterOnly 1
EOF

cat > "$OUT/master_b.conf" <<EOF
[global]
network_transport L2
time_stamping software
delay_mechanism E2E
free_running 1
logSyncInterval -3
logMinDelayReqInterval -3
logAnnounceInterval -2
announceReceiptTimeout 3
priority1 150
clockClass 248
uds_address /var/run/ptp4l-${P}-b
[$BN]
masterOnly 1
EOF

cat > "$OUT/slave.conf" <<EOF
[global]
network_transport L2
time_stamping software
delay_mechanism E2E
free_running 1
slaveOnly 1
priority1 255
logSyncInterval -3
logMinDelayReqInterval -3
logAnnounceInterval -2
announceReceiptTimeout 3
uds_address /var/run/ptp4l-${P}-s

[$S1N]

[$S2N]
EOF

# Start packet captures on BOTH slave root ports
tcpdump -i "$S1R" -w "$OUT/capture_s1.pcap" --time-stamp-precision=nano 'ether proto 0x88f7' >"$OUT/tcpdump_s1.log" 2>&1 & TCP1_PID=$!
tcpdump -i "$S2R" -w "$OUT/capture_s2.pcap" --time-stamp-precision=nano 'ether proto 0x88f7' >"$OUT/tcpdump_s2.log" 2>&1 & TCP2_PID=$!

# Start masters
ip netns exec "$NS_A" ptp4l -f "$OUT/master_a.conf" -i "$AN" -m -q >"$OUT/master_a.log" 2>&1 & A_PID=$!
ip netns exec "$NS_B" ptp4l -f "$OUT/master_b.conf" -i "$BN" -m -q >"$OUT/master_b.log" 2>&1 & B_PID=$!

# Start slave ptp4l with both ports
ip netns exec "$NS_S" ptp4l -f "$OUT/slave.conf" -i "$S1N" -i "$S2N" -s -m -q >"$OUT/slave.log" 2>&1 & S_PID=$!

# Periodic PMC port state sampler in slave namespace
(
  while true; do
    mono_ts="$(mono)"
    utc_ts="$(utc)"
    if [ -S "/var/run/ptp4l-${P}-s" ]; then
      port_data="$(ip netns exec "$NS_S" pmc -u -b 0 -s "/var/run/ptp4l-${P}-s" 'GET PORT_DATA_SET' 2>&1 || true)"
      printf '=== MONO=%s UTC=%s ===\n%s\n' "$mono_ts" "$utc_ts" "$port_data" >> "$OUT/pmc_port_states.log"
    fi
    sleep 1
  done
) & PMC_PID=$!

sleep 3
for item in "tcpdump_s1:$TCP1_PID" "tcpdump_s2:$TCP2_PID" "master_a:$A_PID" "master_b:$B_PID" "slave:$S_PID"; do
  IFS=: read -r n p <<<"$item"
  if kill -0 "$p" 2>/dev/null; then
    event setup "${n}_ready" PASS
  else
    event setup "${n}_ready" FAIL
    die "$n exited before readiness"
  fi
done

event spike phase_settle_started PASS
sleep "$SETTLE_DURATION"

# Record tc counters before impairment
tc -s qdisc show dev "$S1R" > "$OUT/tc_s1_before.txt"
tc -s qdisc show dev "$S2R" > "$OUT/tc_s2_before.txt"
event spike tc_counters_baseline_recorded PASS

# Apply V4 impairment to S1R only (delay 1000us 200us distribution normal loss 1%)
tc qdisc replace dev "$S1R" root netem delay 1000us 200us distribution normal loss 1%
event spike v4_impairment_applied_s1 PASS

sleep "$IMPAIR_DURATION"

# Record tc counters after impairment
tc -s qdisc show dev "$S1R" > "$OUT/tc_s1_after.txt"
tc -s qdisc show dev "$S2R" > "$OUT/tc_s2_after.txt"
event spike tc_counters_impaired_recorded PASS

event spike phase_finished PASS

# Stop processes and clean up
stop_owned
trap - EXIT

printf 'ended_utc=%s\n' "$(utc)" >> "$OUT/run_environment.txt"
sha256sum "$OUT"/* > "$OUT/source_manifest.sha256"
echo "SPIKE_COMPLETE: artifacts in $OUT"
