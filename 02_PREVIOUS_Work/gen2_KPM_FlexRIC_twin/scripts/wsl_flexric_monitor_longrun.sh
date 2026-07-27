#!/usr/bin/env bash
set -euo pipefail

DURATION_SECONDS="${1:-300}"
MONITOR_MODE="${2:-kpm}"

LAB_DIR="${HOME}/oran-lab"
FLEXRIC_DIR="${LAB_DIR}/flexric"
BUILD_DIR="${FLEXRIC_DIR}/build"
SDK_BUILD_DIR="${FLEXRIC_DIR}/build-python-xapp"
CONF="${FLEXRIC_DIR}/flexric.conf"
SM_LIB_DIR="${BUILD_DIR}/flexric-sm-libs"
LOG_DIR="${LAB_DIR}/logs"

RIC_BIN="${BUILD_DIR}/examples/ric/nearRT-RIC"
AGENT_BIN="${BUILD_DIR}/examples/emulator/agent/emu_agent_gnb"
SDK_KPM_XAPP_BIN="${SDK_BUILD_DIR}/examples/xApp/c/monitor/xapp_kpm_moni"
SDK_MULTI_XAPP_BIN="${SDK_BUILD_DIR}/examples/xApp/c/monitor/xapp_gtp_mac_rlc_pdcp_moni"
KPM_XAPP_BIN="${BUILD_DIR}/examples/xApp/c/monitor/xapp_kpm_moni"
MULTI_XAPP_BIN="${BUILD_DIR}/examples/xApp/c/monitor/xapp_gtp_mac_rlc_pdcp_moni"

mkdir -p "${LOG_DIR}" "${SM_LIB_DIR}"
find "${BUILD_DIR}/src/sm" -name "*.so" -exec ln -sf {} "${SM_LIB_DIR}/" \;

for path in "${RIC_BIN}" "${AGENT_BIN}" "${CONF}" "${SM_LIB_DIR}/libkpm_sm.so"; do
  if [ ! -e "${path}" ]; then
    echo "Missing required file: ${path}"
    exit 1
  fi
done

if [ "${MONITOR_MODE}" = "multi" ] && [ -x "${SDK_MULTI_XAPP_BIN}" ]; then
  XAPP_BIN="${SDK_MULTI_XAPP_BIN}"
elif [ "${MONITOR_MODE}" = "multi" ] && [ -x "${MULTI_XAPP_BIN}" ]; then
  XAPP_BIN="${MULTI_XAPP_BIN}"
elif [ -x "${SDK_KPM_XAPP_BIN}" ]; then
  XAPP_BIN="${SDK_KPM_XAPP_BIN}"
elif [ -x "${SDK_MULTI_XAPP_BIN}" ]; then
  XAPP_BIN="${SDK_MULTI_XAPP_BIN}"
elif [ -x "${KPM_XAPP_BIN}" ]; then
  XAPP_BIN="${KPM_XAPP_BIN}"
elif [ -x "${MULTI_XAPP_BIN}" ]; then
  XAPP_BIN="${MULTI_XAPP_BIN}"
else
  echo "No monitor xApp binary found. Run scripts/wsl_build_flexric_python_xapp_sdk.sh first."
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
RIC_LOG="${LOG_DIR}/nearRT-RIC-longrun-${STAMP}.log"
AGENT_LOG="${LOG_DIR}/emu_agent_gnb-longrun-${STAMP}.log"
XAPP_LOG="${LOG_DIR}/xapp-monitor-longrun-${STAMP}.log"
LATEST_LOG="${LOG_DIR}/xapp-monitor-longrun-latest.log"

cleanup() {
  set +e
  if [ -n "${XAPP_PID:-}" ]; then kill "${XAPP_PID}" 2>/dev/null; fi
  if [ -n "${AGENT_PID:-}" ]; then kill "${AGENT_PID}" 2>/dev/null; fi
  if [ -n "${RIC_PID:-}" ]; then kill "${RIC_PID}" 2>/dev/null; fi
  wait "${XAPP_PID:-}" 2>/dev/null
  wait "${AGENT_PID:-}" 2>/dev/null
  wait "${RIC_PID:-}" 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "Starting nearRT-RIC for ${DURATION_SECONDS}s..."
"${RIC_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${RIC_LOG}" 2>&1 &
RIC_PID=$!
sleep 3

echo "Starting emu_agent_gnb..."
"${AGENT_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${AGENT_LOG}" 2>&1 &
AGENT_PID=$!
sleep 4

echo "Starting monitor xApp mode=${MONITOR_MODE}: ${XAPP_BIN}"
timeout "${DURATION_SECONDS}s" "${XAPP_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${XAPP_LOG}" 2>&1 &
XAPP_PID=$!
wait "${XAPP_PID}" 2>/dev/null || true
XAPP_PID=""

ln -sf "${XAPP_LOG}" "${LATEST_LOG}"

echo "Long-run complete."
echo "RIC log: ${RIC_LOG}"
echo "Agent log: ${AGENT_LOG}"
echo "xApp log: ${XAPP_LOG}"
echo "Latest xApp symlink: ${LATEST_LOG}"
echo
echo "xApp log tail:"
tail -80 "${XAPP_LOG}" || true
