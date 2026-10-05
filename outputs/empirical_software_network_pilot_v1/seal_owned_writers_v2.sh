#!/usr/bin/env bash
# Source from a v2 runner; it must own every supplied direct-child PID.
# Never use on frozen runs.

s11_owned_running_pid_v2() {
  local pid=${1:-} candidate
  [[ $pid =~ ^[0-9]+$ ]] || return 1
  while IFS= read -r candidate; do
    [[ $candidate == "$pid" ]] && return 0
  done < <(jobs -pr)
  return 1
}

s11_record_exit_v2() {
  local status=$1 pid=$2 rc=$3
  printf '%s\t%s\n' "$pid" "$rc" >>"$status"
}

# Poll before wait so a stuck direct child cannot make sealing block forever.
# The caller has already proved ownership before any signal is sent.
s11_wait_owned_v2() {
  local pid=$1 timeout_s=$2 started=$SECONDS
  while kill -0 "$pid" 2>/dev/null; do
    if (( SECONDS - started >= timeout_s )); then
      kill -TERM -- "$pid" 2>/dev/null || :
      return 124
    fi
    sleep 0.05
  done
  if wait "$pid"; then
    return 0
  else
    return $?
  fi
}

s11_drain_and_seal_v2() {
  # Do not modify the caller's errexit/nounset/pipefail state: callers need to
  # inspect a nonzero drain result and preserve the unsealed failure directory.
  local out=$1 cap=$2 det=$3
  shift 3
  local timeout_s=${S11_DRAIN_TIMEOUT_SECONDS:-15}
  local status="$out/writer_exit_status.tsv" manifest="$out/source_manifest.sha256"
  local tmp="$out/.source_manifest.tmp.${BASHPID}" pid rc first_failure=0
  local -a pids=("$cap" "$det" "$@")

  [[ -d $out && $cap =~ ^[0-9]+$ && $det =~ ^[0-9]+$ && $cap != "$det" ]] || return 2
  [[ $timeout_s =~ ^[1-9][0-9]*$ && ! -e $manifest && ! -e $tmp ]] || return 2
  : >"$status"

  # Check every target before the first signal; jobs -pr is the shell's list
  # of currently running direct children, so arbitrary numeric PIDs are never
  # signalled or waited for.
  for pid in "${pids[@]}"; do
    s11_owned_running_pid_v2 "$pid" || return 2
  done

  # Closing the capture producer first lets the detector consume the delayed
  # tail and exit on EOF rather than being terminated as a pipeline sibling.
  kill -INT -- "$cap"
  if s11_wait_owned_v2 "$cap" "$timeout_s"; then rc=0; else rc=$?; fi
  s11_record_exit_v2 "$status" "$cap" "$rc"
  (( rc == 0 )) || first_failure=$rc

  if s11_wait_owned_v2 "$det" "$timeout_s"; then rc=0; else rc=$?; fi
  s11_record_exit_v2 "$status" "$det" "$rc"
  (( rc == 0 )) || { (( first_failure == 0 )) && first_failure=$rc; }
  (( first_failure == 0 )) || return "$first_failure"

  for pid in "$@"; do
    kill -TERM -- "$pid"
    if s11_wait_owned_v2 "$pid" "$timeout_s"; then rc=0; else rc=$?; fi
    s11_record_exit_v2 "$status" "$pid" "$rc"
    (( rc == 0 )) || return "$rc"
  done

  # FIFO transport is transient; hash exactly the regular evidence files.
  find "$out" -maxdepth 1 -type p -delete
  find "$out" -maxdepth 1 -type f \
    ! -name source_manifest.sha256 \
    ! -name '.source_manifest.tmp.*' \
    -printf '%f\0' | LC_ALL=C sort -z | while IFS= read -r -d '' pid; do
      sha256sum -- "$out/$pid"
    done >"$tmp"
  mv -- "$tmp" "$manifest"
}
