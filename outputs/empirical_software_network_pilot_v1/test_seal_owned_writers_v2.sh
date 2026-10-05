#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$HERE/seal_owned_writers_v2.sh"

cleanup_pid() {
  local pid=${1:-}
  kill -TERM "$pid" 2>/dev/null || :
  wait "$pid" 2>/dev/null || :
}

OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
FIFO="$OUT/stream.fifo"
mkfifo "$FIFO"
( cat "$FIFO" >"$OUT/data.log" ) & det=$!
(
  trap 'printf tail >&3; exec 3>&-; exit 0' INT
  exec 3>"$FIFO"
  printf head >&3
  while :; do sleep 0.05; done
) & cap=$!
sleep 0.1
s11_drain_and_seal_v2 "$OUT" "$cap" "$det"
test "$(cat "$OUT/data.log")" = headtail
test ! -p "$FIFO"
test ! -e "$OUT/.source_manifest.tmp.${BASHPID}"
! grep -Fq 'source_manifest.sha256' "$OUT/source_manifest.sha256"
! grep -Fq 'stream.fifo' "$OUT/source_manifest.sha256"
grep -Eq "^${cap}[[:space:]]+0$" "$OUT/writer_exit_status.tsv"
grep -Eq "^${det}[[:space:]]+0$" "$OUT/writer_exit_status.tsv"

# A producer failure must be recorded and must not seal the directory.
BAD=$(mktemp -d)
BAD_FIFO="$BAD/stream.fifo"
mkfifo "$BAD_FIFO"
( cat "$BAD_FIFO" >"$BAD/data.log" ) & bad_det=$!
(
  trap 'exit 7' INT
  exec 3>"$BAD_FIFO"
  while :; do sleep 0.05; done
) & bad_cap=$!
sleep 0.1
set +e
s11_drain_and_seal_v2 "$BAD" "$bad_cap" "$bad_det"
bad_rc=$?
set -e
test "$bad_rc" -eq 7
grep -Eq "^${bad_cap}[[:space:]]+7$" "$BAD/writer_exit_status.tsv"
test ! -e "$BAD/source_manifest.sha256"
rm -rf "$BAD"

# A producer which ignores INT hits the bounded path and cannot seal.
HUNG=$(mktemp -d)
HUNG_FIFO="$HUNG/stream.fifo"
mkfifo "$HUNG_FIFO"
( cat "$HUNG_FIFO" >"$HUNG/data.log" ) & hung_det=$!
(
  trap '' INT
  exec 3>"$HUNG_FIFO"
  while :; do sleep 0.05; done
) & hung_cap=$!
sleep 0.1
set +e
S11_DRAIN_TIMEOUT_SECONDS=1 s11_drain_and_seal_v2 "$HUNG" "$hung_cap" "$hung_det"
hung_rc=$?
set -e
test "$hung_rc" -eq 124
grep -Eq "^${hung_cap}[[:space:]]+124$" "$HUNG/writer_exit_status.tsv"
test ! -e "$HUNG/source_manifest.sha256"
cleanup_pid "$hung_cap"
cleanup_pid "$hung_det"
rm -rf "$HUNG"

# Preflight rejects a non-child before it can signal the legitimate child.
NONCHILD=$(mktemp -d)
sleep 30 & own=$!
set +e
s11_drain_and_seal_v2 "$NONCHILD" 1 "$own"
nonchild_rc=$?
set -e
test "$nonchild_rc" -eq 2
kill -0 "$own"
test ! -e "$NONCHILD/source_manifest.sha256"
cleanup_pid "$own"
rm -rf "$NONCHILD"

echo PASS
