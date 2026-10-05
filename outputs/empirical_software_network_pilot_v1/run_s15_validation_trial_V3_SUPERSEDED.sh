#!/usr/bin/env bash
# S14 broader software experiment trial runner with direct-child drain-and-seal.
# S15 independent validation trial (graded jitter sweep).
# Frozen by S15_INDEPENDENT_VALIDATION_PROTOCOL_V3.json. Supersedes run_s15_validation_trial_V2_SUPERSEDED.sh.
# Usage: bash run_s15_validation_trial.sh OUT_DIR RUN_TOKEN CONDITION ARM
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$HERE/seal_owned_writers_v2.sh"
die() { echo "FATAL: $*" >&2; exit 1; }
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
# CLOCK_MONOTONIC at microsecond precision. This is the SAME clock that linuxptp print.c reads
# (clock_gettime(CLOCK_MONOTONIC), printed as %lld.%03ld, i.e. truncated to 1 ms) and the same clock
# the detector records via time.monotonic(). The previous /proc/uptime source was CLOCK_BOOTTIME at
# 10 ms resolution, which is both a different clock and coarser than the 1 ms exclusion band the
# evaluator applied. Recorded to 6 dp; the real limit is this shell's call latency, which is why
# every phase command is bracketed by a before and an after timestamp.
mono() { python3 -c 'import time;print("%.6f"%time.clock_gettime(time.CLOCK_MONOTONIC))'; }

OUT="${1:-}"; RUN_ID="${2:-}"; CONDITION="${3:-}"; ARM="${4:-}"
[ -n "$OUT" ] || die "usage: $0 OUT_DIR RUN_TOKEN CONDITION ARM"
echo "$RUN_ID" | grep -Eq '^[a-z0-9]{1,6}$' || die "RUN_TOKEN must be 1-6 lowercase letters/digits"
case "$CONDITION" in j020|j060|j100|j140|j200) ;; *) die "unsupported CONDITION: $CONDITION" ;; esac
case "$ARM" in action|no_action) ;; *) die "ARM must be action or no_action";; esac
[ "$(id -u)" = "0" ] || die "must run as root"
for c in ip tc ptp4l tcpdump pmc python3; do command -v "$c" >/dev/null || die "missing $c"; done
[ ! -e "$OUT" ] || die "OUT_DIR must not already exist"

ROOT="$(cd "$HERE/../.." && pwd)"
PILOT="$ROOT/outputs/empirical_software_network_pilot_v1"
DET="$PILOT/live_detect_and_act.py"
[ -f "$DET" ] || die "live detector not found: $DET"

P="s15${RUN_ID}"
BR1="${P}b1"; BR2="${P}b2"; NS_A="${P}a"; NS_B="${P}b"; NS_S="${P}s"
AR="${P}ar"; AN="${P}an"; BRT="${P}br"; BN="${P}bn"
S1R="${P}x1"; S1N="${P}y1"; S2R="${P}x2"; S2N="${P}y2"
for x in "$BR1" "$BR2" "$NS_A" "$NS_B" "$NS_S" "$AR" "$AN" "$BRT" "$BN" "$S1R" "$S1N" "$S2R" "$S2N"; do
  ip link show "$x" >/dev/null 2>&1 && die "resource collision: $x"
  ip netns list | awk '{print $1}' | grep -Fxq "$x" && die "resource collision: $x"
done

CREATED=0
STREAM_FIFO="/tmp/${P}_detector_stream.fifo"
cleanup() {
  set +e
  local pid
  for pid in ${A_PID:-} ${B_PID:-} ${S_PID:-} ${DET_PID:-} ${PMC_PID:-}; do
    s11_owned_running_pid_v2 "$pid" && kill -TERM -- "$pid" 2>/dev/null
  done
  for pid in ${T1F_PID:-} ${T2F_PID:-} ${CAPTURE_PID:-}; do
    s11_owned_running_pid_v2 "$pid" && kill -INT -- "$pid" 2>/dev/null
  done
  for pid in ${A_PID:-} ${B_PID:-} ${S_PID:-} ${DET_PID:-} ${PMC_PID:-} ${T1F_PID:-} ${T2F_PID:-} ${CAPTURE_PID:-}; do
    s11_owned_running_pid_v2 "$pid" && wait "$pid" 2>/dev/null
  done
  if [ "$CREATED" = 1 ]; then
    ip netns del "$NS_A" 2>/dev/null; ip netns del "$NS_B" 2>/dev/null; ip netns del "$NS_S" 2>/dev/null
    ip link del "$BR1" 2>/dev/null; ip link del "$BR2" 2>/dev/null
  fi
  [ -n "${STREAM_FIFO:-}" ] && rm -f "$STREAM_FIFO" 2>/dev/null
}
trap cleanup EXIT

mkdir -p "$OUT"; : > "$OUT/events.log"
event() { printf 'run_id=%s arm=%s condition=%s phase=%s event=%s utc=%s monotonic_s=%s status=%s\n' "$RUN_ID" "$ARM" "$CONDITION" "$1" "$2" "$(utc)" "$(mono)" "$3" >> "$OUT/events.log"; }
printf 'run_id=%s\narm=%s\ncondition=%s\nlinuxptp=%s\ntopology=two_independent_l2_segments\nhost_clock_adjustment=disabled_by_free_running_1\nstarted_utc=%s\n' \
  "$RUN_ID" "$ARM" "$CONDITION" "$(ptp4l -v 2>&1 | head -n1)" "$(utc)" > "$OUT/run_environment.txt"

CREATED=1
ip link add "$BR1" type bridge; ip link set "$BR1" up
ip link add "$BR2" type bridge; ip link set "$BR2" up
ip netns add "$NS_A"; ip netns add "$NS_B"; ip netns add "$NS_S"
ip link add "$AR"  type veth peer name "$AN";  ip link set "$AN"  netns "$NS_A"; ip link set "$AR"  master "$BR1"; ip link set "$AR"  up
ip link add "$BRT" type veth peer name "$BN";  ip link set "$BN"  netns "$NS_B"; ip link set "$BRT" master "$BR2"; ip link set "$BRT" up
ip link add "$S1R" type veth peer name "$S1N"; ip link set "$S1N" netns "$NS_S"; ip link set "$S1R" master "$BR1"; ip link set "$S1R" up
ip link add "$S2R" type veth peer name "$S2N"; ip link set "$S2N" netns "$NS_S"; ip link set "$S2R" master "$BR2"; ip link set "$S2R" up
for ns in "$NS_A" "$NS_B" "$NS_S"; do ip netns exec "$ns" ip link set lo up; done
ip netns exec "$NS_A" ip link set "$AN" up; ip netns exec "$NS_B" ip link set "$BN" up
ip netns exec "$NS_S" ip link set "$S1N" up; ip netns exec "$NS_S" ip link set "$S2N" up
event setup topology_created PASS

common() { printf '[global]\nnetwork_transport L2\ntime_stamping software\ndelay_mechanism E2E\nfree_running 1\nlogSyncInterval -3\nlogMinDelayReqInterval -3\nlogAnnounceInterval -2\nannounceReceiptTimeout 3\n'; }
{ common; printf 'priority1 100\nclockClass 248\nuds_address /var/run/ptp4l-%s-a\n[%s]\nmasterOnly 1\n' "$P" "$AN"; } > "$OUT/master_a.conf"
{ common; printf 'priority1 150\nclockClass 248\nuds_address /var/run/ptp4l-%s-b\n[%s]\nmasterOnly 1\n' "$P" "$BN"; } > "$OUT/master_b.conf"
{ common; printf 'slaveOnly 1\npriority1 255\nuds_address /var/run/ptp4l-%s-s\n[%s]\n[%s]\n' "$P" "$S1N" "$S2N"; } > "$OUT/slave.conf"

tcpdump -i "$S1R" -w "$OUT/capture_seg1.pcap" --time-stamp-precision=nano 'ether proto 0x88f7' >"$OUT/tcpdump_seg1.log" 2>&1 & T1F_PID=$!
tcpdump -i "$S2R" -w "$OUT/capture_seg2.pcap" --time-stamp-precision=nano 'ether proto 0x88f7' >"$OUT/tcpdump_seg2.log" 2>&1 & T2F_PID=$!
ip netns exec "$NS_A" ptp4l -f "$OUT/master_a.conf" -i "$AN" -m -q >"$OUT/master_a.log" 2>&1 & A_PID=$!
ip netns exec "$NS_B" ptp4l -f "$OUT/master_b.conf" -i "$BN" -m -q >"$OUT/master_b.log" 2>&1 & B_PID=$!
ip netns exec "$NS_S" ptp4l -f "$OUT/slave.conf" -m -q >"$OUT/slave.log" 2>&1 & S_PID=$!
sleep 3
for item in "tcpdump_seg1:$T1F_PID" "tcpdump_seg2:$T2F_PID" "master_a:$A_PID" "master_b:$B_PID" "slave:$S_PID"; do
  IFS=: read -r n p <<<"$item"
  kill -0 "$p" 2>/dev/null && event setup "${n}_ready" PASS || { event setup "${n}_ready" FAIL; die "$n exited before readiness"; }
done

# Declared observation period. The detector lifetime is derived from these two values so the two
# cannot drift apart: a hard-coded --max-seconds 70 previously expired 24 s BEFORE the impaired phase
# ended, truncating observation coverage and leaving the capture FIFO without a reader.
SETTLE=12; IMPAIR=80
# Bounded watchdog: setup margin + both phases + drain margin. It is a ceiling that guarantees the
# detector cannot outlive the run, not a schedule: the detector normally exits when the sealer closes
# the FIFO, well before this bound.
DET_SETUP_MARGIN=20; DET_DRAIN_MARGIN=60
DET_MAX_SECONDS=$(( DET_SETUP_MARGIN + SETTLE + IMPAIR + DET_DRAIN_MARGIN ))

ACTION_CMD="ip netns exec $NS_S ip link set $S1N down"
export PYTHONPATH="$PILOT:$ROOT/01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing"
rm -f "$STREAM_FIFO"
mkfifo "$STREAM_FIFO"
tcpdump -i "$S1R" -w - -U --time-stamp-precision=nano 'ether proto 0x88f7' >"$STREAM_FIFO" 2>"$OUT/tcpdump_stream.log" & CAPTURE_PID=$!
python3 "$DET" --stream-id "seg1-$RUN_ID" --arm "$ARM" --action-command "$ACTION_CMD" \
    --decision-log "$OUT/decision_log.jsonl" --max-seconds "$DET_MAX_SECONDS" <"$STREAM_FIFO" >"$OUT/detector_stdout.log" 2>&1 & DET_PID=$!
sleep 2
kill -0 "$CAPTURE_PID" 2>/dev/null && kill -0 "$DET_PID" 2>/dev/null && event setup live_detector_ready PASS || { event setup live_detector_ready FAIL; die "live detector or capture failed to start"; }

( trap 'exit 0' TERM; while true; do printf '%s %s ' "$(utc)" "$(mono)";
    ip netns exec "$NS_S" pmc -u -b 0 -f "$OUT/slave.conf" 'GET PORT_DATA_SET' 2>/dev/null | tr '\n' ' '; printf '\n'; sleep 1; done ) >"$OUT/pmc_port_states.log" 2>&1 & PMC_PID=$!

# SETTLE and IMPAIR are declared near the top of the script so the detector lifetime can be derived
# from them. See DET_MAX_SECONDS above.
event trial phase1_clean_started PASS; sleep "$SETTLE"
tc -s qdisc show dev "$S1R" > "$OUT/tc_seg1_p1.txt"; tc -s qdisc show dev "$S2R" > "$OUT/tc_seg2_p1.txt"
ip netns exec "$NS_S" pmc -u -b 0 -f "$OUT/slave.conf" 'GET PORT_DATA_SET' > "$OUT/portstate_p1.txt" 2>&1 || true
event trial phase1_clean_recorded PASS

case "$CONDITION" in
  j020|j060|j100|j140|j200)
    JIT="${CONDITION#j}"
    # The apply instant is an INTERVAL, not a point. phase2_apply_begin is taken immediately before
    # the tc command and phase2_graded_jitter_applied_seg1 immediately after it. The true instant at
    # which the qdisc changed lies between them. The evaluator uses the LATER bound for eligibility,
    # which is conservative: it can only reject a window that might straddle, never admit one.
    event trial phase2_apply_begin PASS
    tc qdisc replace dev "$S1R" root netem delay 100us "${JIT}us" distribution normal
    event trial phase2_graded_jitter_applied_seg1 PASS
    ;;
  *) die "unsupported CONDITION in s15: $CONDITION" ;;
esac

sleep "$IMPAIR"
tc -s qdisc show dev "$S1R" > "$OUT/tc_seg1_p2.txt"; tc -s qdisc show dev "$S2R" > "$OUT/tc_seg2_p2.txt"
ip netns exec "$NS_S" pmc -u -b 0 -f "$OUT/slave.conf" 'GET PORT_DATA_SET' > "$OUT/portstate_p2.txt" 2>&1 || true
event trial phase2_end_recorded PASS

event trial phase_finished PASS
printf 'ended_utc=%s\n' "$(utc)" >> "$OUT/run_environment.txt"
printf 'settle_s=%s\nimpair_s=%s\ndetector_max_seconds=%s\nphase_clock=CLOCK_MONOTONIC_via_python_clock_gettime\nptp4l_log_clock=CLOCK_MONOTONIC_truncated_to_1ms\nexpected_summary_cadence_s=16\n' \
  "$SETTLE" "$IMPAIR" "$DET_MAX_SECONDS" >> "$OUT/run_environment.txt"
EXTRA_PIDS=()
[ -n "${A_PID:-}" ] && EXTRA_PIDS+=("$A_PID")
EXTRA_PIDS+=("$B_PID" "$S_PID" "$PMC_PID" "$T1F_PID" "$T2F_PID")
s11_drain_and_seal_v2 "$OUT" "$CAPTURE_PID" "$DET_PID" "${EXTRA_PIDS[@]}"
A_PID=; B_PID=; S_PID=; DET_PID=; PMC_PID=; T1F_PID=; T2F_PID=; CAPTURE_PID=
trap - EXIT
if [ "$CREATED" = 1 ]; then
  ip netns del "$NS_A"; ip netns del "$NS_B"; ip netns del "$NS_S"
  ip link del "$BR1"; ip link del "$BR2"
fi
[ -n "${STREAM_FIFO:-}" ] && rm -f "$STREAM_FIFO" 2>/dev/null
echo "s15 trial complete: $OUT condition=$CONDITION arm=$ARM"
