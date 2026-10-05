#!/usr/bin/env bash
# Isolated, free-running PTP protocol-observation pilot. It never adjusts a
# clock and only deletes resources it successfully created.
set -euo pipefail
MODE="${1:---preflight}"; OUT="${2:-}"; RUN_ID="${3:-}"; SCENARIO="${4:-}"
DURATION="${PILOT_DURATION_SECONDS:-30}"
die() { echo "ERROR: $*" >&2; exit 2; }
need() { command -v "$1" >/dev/null 2>&1 || die "required command unavailable: $1"; }
utc() { date -u +%FT%TZ; }; mono() { awk '{print $1}' /proc/uptime; }
valid_id() { [[ "$1" =~ ^[a-z0-9]{1,4}$ ]]; }

if [ "$MODE" = "--preflight" ]; then
  [ "$(id -u)" = 0 ] || die "requires root inside the isolated Linux testbed"
  for x in ip tc ptp4l tcpdump sha256sum; do need "$x"; done
  VERSION="$(ptp4l -v | head -n1)"
  [ "$VERSION" = "3.1.1" ] || die "requires audited linuxptp 3.1.1; recalibrate another version"
  printf 'PREFLIGHT_PASS uid=0 linuxptp=%s mode=free_running_protocol_observation host_clock_adjustment=disabled_by_config\n' "$VERSION"
  exit 0
fi
[ "$MODE" = "--execute" ] || die "usage: $0 --preflight | --execute OUT_DIRECTORY RUN_TOKEN SCENARIO"
[ -n "$OUT" ] && valid_id "$RUN_ID" || die "RUN_TOKEN must be 1-4 lowercase letters/digits"
case "$SCENARIO" in baseline_control|netem_delay_jitter_loss|benign_delay_jitter_no_loss|authorized_source_change_no_action_control|authorized_source_change_intervention) ;; *) die "unsupported scenario";; esac
"$0" --preflight
[ ! -e "$OUT" ] || die "OUT_DIRECTORY must not already exist"

# Interface-name limit is 15. Each execution gets an explicit short token.
P="ptp${RUN_ID}"; BR="${P}br"; NS_A="${P}a"; NS_B="${P}b"; NS_S="${P}s"
AR="${P}ar"; AN="${P}an"; BROOT="${P}cr"; BN="${P}bn"; SR="${P}sr"; SN="${P}sn"
resource_exists() { ip link show "$1" >/dev/null 2>&1 || ip netns list | awk '{print $1}' | grep -Fxq "$1"; }
for x in "$BR" "$NS_A" "$NS_B" "$NS_S" "$AR" "$AN" "$BROOT" "$BN" "$SR" "$SN"; do resource_exists "$x" && die "resource collision: $x"; done

CREATED_BR=0; CREATED_A=0; CREATED_B=0; CREATED_S=0
stop_owned() {
  set +e
  for pid in "${A_PID:-}" "${B_PID:-}" "${S_PID:-}"; do [ -n "$pid" ] && kill -TERM "$pid" 2>/dev/null; done
  [ -n "${TCP_PID:-}" ] && kill -INT "$TCP_PID" 2>/dev/null
  for pid in "${A_PID:-}" "${B_PID:-}" "${S_PID:-}" "${TCP_PID:-}"; do [ -n "$pid" ] && wait "$pid" 2>/dev/null; done
  [ "$CREATED_A" = 1 ] && ip netns del "$NS_A" 2>/dev/null
  [ "$CREATED_B" = 1 ] && ip netns del "$NS_B" 2>/dev/null
  [ "$CREATED_S" = 1 ] && ip netns del "$NS_S" 2>/dev/null
  [ "$CREATED_BR" = 1 ] && ip link del "$BR" 2>/dev/null
}
trap stop_owned EXIT
mkdir -p "$(dirname "$OUT")"; mkdir "$OUT"; : > "$OUT/events.log"
event() { printf 'run_id=%s phase=%s event=%s utc=%s monotonic_s=%s status=%s\n' "$RUN_ID" "$1" "$2" "$(utc)" "$(mono)" "$3" >> "$OUT/events.log"; }
printf 'run_id=%s\nlinuxptp=%s\nmeasurement_mode=free_running_protocol_observation\nhost_clock_adjustment=disabled_by_free_running_1\n' "$RUN_ID" "$(ptp4l -v | head -n1)" > "$OUT/run_environment.txt"

ip link add "$BR" type bridge; CREATED_BR=1; ip link set "$BR" up
for spec in "$NS_A:$AR:$AN:A" "$NS_B:$BROOT:$BN:B" "$NS_S:$SR:$SN:S"; do
  IFS=: read -r ns rootif nsif flag <<<"$spec"; ip netns add "$ns"; eval "CREATED_${flag}=1"
  ip link add "$rootif" type veth peer name "$nsif"; ip link set "$nsif" netns "$ns"
  ip link set "$rootif" master "$BR"; ip link set "$rootif" up
  ip netns exec "$ns" ip link set lo up; ip netns exec "$ns" ip link set "$nsif" up
done
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
sed "s/priority1 100/priority1 150/; s/${P}-a/${P}-b/; s/\[$AN\]/[$BN]/" "$OUT/master_a.conf" > "$OUT/master_b.conf"
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
EOF
tcpdump -i "$SR" -w "$OUT/capture.pcap" --time-stamp-precision=nano 'ether proto 0x88f7' >"$OUT/tcpdump.log" 2>&1 & TCP_PID=$!
ip netns exec "$NS_A" ptp4l -f "$OUT/master_a.conf" -i "$AN" -m -q >"$OUT/master_a.log" 2>&1 & A_PID=$!
ip netns exec "$NS_B" ptp4l -f "$OUT/master_b.conf" -i "$BN" -m -q >"$OUT/master_b.log" 2>&1 & B_PID=$!
ip netns exec "$NS_S" ptp4l -f "$OUT/slave.conf" -i "$SN" -s -m -q >"$OUT/slave.log" 2>&1 & S_PID=$!
sleep 3
for item in "tcpdump:$TCP_PID" "master_a:$A_PID" "master_b:$B_PID" "slave:$S_PID"; do IFS=: read -r n p <<<"$item"; if kill -0 "$p" 2>/dev/null; then event setup "${n}_ready" PASS; else event setup "${n}_ready" FAIL; die "$n exited before readiness"; fi; done

event "$SCENARIO" phase_started PASS
case "$SCENARIO" in
  baseline_control|authorized_source_change_no_action_control)
    tc -s qdisc show dev "$SR" > "$OUT/qdisc_before.txt"; event "$SCENARIO" qdisc_baseline_observed PASS; sleep "$DURATION" ;;
  netem_delay_jitter_loss)
    tc -s qdisc show dev "$SR" > "$OUT/qdisc_before.txt"
    tc qdisc replace dev "$SR" root netem delay 1000us 200us distribution normal loss 1%
    event "$SCENARIO" netem_command_confirmed PASS; sleep "$DURATION"
    tc -s qdisc show dev "$SR" > "$OUT/qdisc_after.txt" ;;
  benign_delay_jitter_no_loss)
    tc -s qdisc show dev "$SR" > "$OUT/qdisc_before.txt"
    tc qdisc replace dev "$SR" root netem delay 100us 20us distribution normal
    event "$SCENARIO" benign_netem_command_confirmed PASS; sleep "$DURATION"
    tc -s qdisc show dev "$SR" > "$OUT/qdisc_after.txt" ;;
  authorized_source_change_intervention)
    sleep "$DURATION"; kill -TERM "$A_PID"
    event "$SCENARIO" preferred_master_stop_confirmed PASS; sleep "$DURATION" ;;
esac
event "$SCENARIO" phase_finished PASS
stop_owned; trap - EXIT
printf 'ended_utc=%s\n' "$(utc)" >> "$OUT/run_environment.txt"
sha256sum "$OUT"/* > "$OUT/source_manifest.sha256"
