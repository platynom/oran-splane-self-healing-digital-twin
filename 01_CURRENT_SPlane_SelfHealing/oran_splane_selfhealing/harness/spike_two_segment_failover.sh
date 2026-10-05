#!/usr/bin/env bash
# S11 mechanism probe: two INDEPENDENT L2 segments, commanded failover.
# Feasibility probe only. No closed-loop experiment, no recovery claim.
# Usage: bash spike_two_segment_failover.sh OUT_DIR RUN_TOKEN
set -euo pipefail
die() { echo "FATAL: $*" >&2; exit 1; }
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
mono() { awk '{printf "%.2f", $1}' /proc/uptime; }

OUT="${1:-}"; RUN_ID="${2:-}"
[ -n "$OUT" ] || die "usage: $0 OUT_DIR RUN_TOKEN"
echo "$RUN_ID" | grep -Eq '^[a-z0-9]{1,6}$' || die "RUN_TOKEN must be 1-6 lowercase letters/digits"
[ "$(id -u)" = "0" ] || die "must run as root"
for c in ip tc ptp4l tcpdump pmc; do command -v "$c" >/dev/null || die "missing $c"; done
[ ! -e "$OUT" ] || die "OUT_DIR must not already exist"

P="s2${RUN_ID}"
BR1="${P}b1"; BR2="${P}b2"
NS_A="${P}a"; NS_B="${P}b"; NS_S="${P}s"
AR="${P}ar"; AN="${P}an"        # master A <-> bridge1
BR_="${P}br"; BN="${P}bn"       # master B <-> bridge2
S1R="${P}x1"; S1N="${P}y1"      # slave port 1 <-> bridge1
S2R="${P}x2"; S2N="${P}y2"      # slave port 2 <-> bridge2
for x in "$BR1" "$BR2" "$NS_A" "$NS_B" "$NS_S" "$AR" "$AN" "$BR_" "$BN" "$S1R" "$S1N" "$S2R" "$S2N"; do
  ip link show "$x" >/dev/null 2>&1 && die "resource collision: $x"
  ip netns list | awk '{print $1}' | grep -Fxq "$x" && die "resource collision: $x"
done

CREATED=0
cleanup() {
  set +e
  for pid in ${A_PID:-} ${B_PID:-} ${S_PID:-}; do [ -n "$pid" ] && kill -TERM "$pid" 2>/dev/null; done
  [ -n "${T1_PID:-}" ] && kill -INT "$T1_PID" 2>/dev/null
  [ -n "${T2_PID:-}" ] && kill -INT "$T2_PID" 2>/dev/null
  [ -n "${PMC_PID:-}" ] && kill -TERM "$PMC_PID" 2>/dev/null
  for pid in ${A_PID:-} ${B_PID:-} ${S_PID:-} ${T1_PID:-} ${T2_PID:-} ${PMC_PID:-}; do [ -n "$pid" ] && wait "$pid" 2>/dev/null; done
  if [ "$CREATED" = 1 ]; then
    ip netns del "$NS_A" 2>/dev/null; ip netns del "$NS_B" 2>/dev/null; ip netns del "$NS_S" 2>/dev/null
    ip link del "$BR1" 2>/dev/null; ip link del "$BR2" 2>/dev/null
  fi
}
trap cleanup EXIT

mkdir -p "$OUT"; : > "$OUT/events.log"
event() { printf 'run_id=%s phase=%s event=%s utc=%s monotonic_s=%s status=%s\n' "$RUN_ID" "$1" "$2" "$(utc)" "$(mono)" "$3" >> "$OUT/events.log"; }
printf 'run_id=%s\nlinuxptp=%s\ntopology=two_independent_l2_segments\nhost_clock_adjustment=disabled_by_free_running_1\nstarted_utc=%s\n' \
  "$RUN_ID" "$(ptp4l -v 2>&1 | head -n1)" "$(utc)" > "$OUT/run_environment.txt"

# --- topology: two separate bridges, one master per segment, slave on both ---
CREATED=1
ip link add "$BR1" type bridge; ip link set "$BR1" up
ip link add "$BR2" type bridge; ip link set "$BR2" up
ip netns add "$NS_A"; ip netns add "$NS_B"; ip netns add "$NS_S"
ip link add "$AR"  type veth peer name "$AN";  ip link set "$AN"  netns "$NS_A"; ip link set "$AR"  master "$BR1"; ip link set "$AR"  up
ip link add "$BR_" type veth peer name "$BN";  ip link set "$BN"  netns "$NS_B"; ip link set "$BR_" master "$BR2"; ip link set "$BR_" up
ip link add "$S1R" type veth peer name "$S1N"; ip link set "$S1N" netns "$NS_S"; ip link set "$S1R" master "$BR1"; ip link set "$S1R" up
ip link add "$S2R" type veth peer name "$S2N"; ip link set "$S2N" netns "$NS_S"; ip link set "$S2R" master "$BR2"; ip link set "$S2R" up
for ns in "$NS_A" "$NS_B" "$NS_S"; do ip netns exec "$ns" ip link set lo up; done
ip netns exec "$NS_A" ip link set "$AN" up
ip netns exec "$NS_B" ip link set "$BN" up
ip netns exec "$NS_S" ip link set "$S1N" up
ip netns exec "$NS_S" ip link set "$S2N" up
event setup topology_created PASS

common() { printf '[global]\nnetwork_transport L2\ntime_stamping software\ndelay_mechanism E2E\nfree_running 1\nlogSyncInterval -3\nlogMinDelayReqInterval -3\nlogAnnounceInterval -2\nannounceReceiptTimeout 3\n'; }
{ common; printf 'priority1 100\nclockClass 248\nuds_address /var/run/ptp4l-%s-a\n[%s]\nmasterOnly 1\n' "$P" "$AN"; } > "$OUT/master_a.conf"
{ common; printf 'priority1 150\nclockClass 248\nuds_address /var/run/ptp4l-%s-b\n[%s]\nmasterOnly 1\n' "$P" "$BN"; } > "$OUT/master_b.conf"
{ common; printf 'slaveOnly 1\npriority1 255\nuds_address /var/run/ptp4l-%s-s\n[%s]\n[%s]\n' "$P" "$S1N" "$S2N"; } > "$OUT/slave.conf"

tcpdump -i "$S1R" -w "$OUT/capture_seg1.pcap" --time-stamp-precision=nano 'ether proto 0x88f7' >"$OUT/tcpdump_seg1.log" 2>&1 & T1_PID=$!
tcpdump -i "$S2R" -w "$OUT/capture_seg2.pcap" --time-stamp-precision=nano 'ether proto 0x88f7' >"$OUT/tcpdump_seg2.log" 2>&1 & T2_PID=$!
ip netns exec "$NS_A" ptp4l -f "$OUT/master_a.conf" -i "$AN" -m -q >"$OUT/master_a.log" 2>&1 & A_PID=$!
ip netns exec "$NS_B" ptp4l -f "$OUT/master_b.conf" -i "$BN" -m -q >"$OUT/master_b.log" 2>&1 & B_PID=$!
ip netns exec "$NS_S" ptp4l -f "$OUT/slave.conf" -m -q >"$OUT/slave.log" 2>&1 & S_PID=$!
sleep 3
for item in "tcpdump_seg1:$T1_PID" "tcpdump_seg2:$T2_PID" "master_a:$A_PID" "master_b:$B_PID" "slave:$S_PID"; do
  IFS=: read -r n p <<<"$item"
  if kill -0 "$p" 2>/dev/null; then event setup "${n}_ready" PASS; else event setup "${n}_ready" FAIL; die "$n exited before readiness"; fi
done

# poll port states for the whole run
( while true; do printf '%s %s ' "$(utc)" "$(mono)";
    ip netns exec "$NS_S" pmc -u -b 0 -f "$OUT/slave.conf" 'GET PORT_DATA_SET' 2>/dev/null | tr '\n' ' '; printf '\n'; sleep 1; done ) >"$OUT/pmc_port_states.log" 2>&1 & PMC_PID=$!

SETTLE=12; IMPAIR=12; POST=12

# PHASE 1: clean
event probe phase1_clean_started PASS; sleep "$SETTLE"
tc -s qdisc show dev "$S1R" > "$OUT/tc_seg1_p1.txt"; tc -s qdisc show dev "$S2R" > "$OUT/tc_seg2_p1.txt"
ip netns exec "$NS_S" pmc -u -b 0 -f "$OUT/slave.conf" 'GET PORT_DATA_SET' > "$OUT/portstate_p1.txt" 2>&1 || true
event probe phase1_clean_recorded PASS

# PHASE 2: impair segment 1 with the parameter V5 identified as the driver: jitter magnitude
tc qdisc replace dev "$S1R" root netem delay 100us 200us distribution normal
event probe phase2_jitter_impairment_applied_seg1 PASS; sleep "$IMPAIR"
tc -s qdisc show dev "$S1R" > "$OUT/tc_seg1_p2.txt"; tc -s qdisc show dev "$S2R" > "$OUT/tc_seg2_p2.txt"
ip netns exec "$NS_S" pmc -u -b 0 -f "$OUT/slave.conf" 'GET PORT_DATA_SET' > "$OUT/portstate_p2.txt" 2>&1 || true
event probe phase2_impaired_recorded PASS

# PHASE 3: COMMANDED ACTION - take the impaired segment's slave port administratively down.
# This is an externally commanded action, not autonomous BMCA behaviour.
if ip netns exec "$NS_S" ip link set "$S1N" down; then event probe phase3_commanded_action_port_down PASS; else event probe phase3_commanded_action_port_down FAIL; fi
sleep "$POST"
tc -s qdisc show dev "$S1R" > "$OUT/tc_seg1_p3.txt"; tc -s qdisc show dev "$S2R" > "$OUT/tc_seg2_p3.txt"
ip netns exec "$NS_S" pmc -u -b 0 -f "$OUT/slave.conf" 'GET PORT_DATA_SET' > "$OUT/portstate_p3.txt" 2>&1 || true
event probe phase3_post_action_recorded PASS

event probe phase_finished PASS
cleanup; trap - EXIT
printf 'ended_utc=%s\n' "$(utc)" >> "$OUT/run_environment.txt"
sha256sum "$OUT"/* > "$OUT/source_manifest.sha256"
echo "spike complete: $OUT"
