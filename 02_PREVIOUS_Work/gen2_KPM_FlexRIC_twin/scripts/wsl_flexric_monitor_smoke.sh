#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${HOME}/oran-lab"
FLEXRIC_DIR="${LAB_DIR}/flexric"
BUILD_DIR="${FLEXRIC_DIR}/build"
SDK_BUILD_DIR="${FLEXRIC_DIR}/build-python-xapp"
CONF="${FLEXRIC_DIR}/flexric.conf"
SM_LIB_DIR="${BUILD_DIR}/flexric-sm-libs"
LOG_DIR="${LAB_DIR}/logs"

RIC_BIN="${BUILD_DIR}/examples/ric/nearRT-RIC"
AGENT_BIN="${BUILD_DIR}/examples/emulator/agent/emu_agent_gnb"
KPM_XAPP_BIN="${BUILD_DIR}/examples/xApp/c/monitor/xapp_kpm_moni"
MULTI_XAPP_BIN="${BUILD_DIR}/examples/xApp/c/monitor/xapp_gtp_mac_rlc_pdcp_moni"
SDK_KPM_XAPP_BIN="${SDK_BUILD_DIR}/examples/xApp/c/monitor/xapp_kpm_moni"
SDK_MULTI_XAPP_BIN="${SDK_BUILD_DIR}/examples/xApp/c/monitor/xapp_gtp_mac_rlc_pdcp_moni"
PY_XAPP="${FLEXRIC_DIR}/examples/xApp/python3/xapp_mac_rlc_pdcp_gtp_moni.py"
PY_SDK_DIR="${SDK_BUILD_DIR}/examples/xApp/python3"

mkdir -p "${LOG_DIR}" "${SM_LIB_DIR}"
find "${BUILD_DIR}/src/sm" -name "*.so" -exec ln -sf {} "${SM_LIB_DIR}/" \;

for path in "${RIC_BIN}" "${AGENT_BIN}" "${CONF}" "${SM_LIB_DIR}/libkpm_sm.so"; do
  if [ ! -e "${path}" ]; then
    echo "Missing required file: ${path}"
    exit 1
  fi
done

RIC_LOG="${LOG_DIR}/nearRT-RIC-monitor.log"
AGENT_LOG="${LOG_DIR}/emu_agent_gnb-monitor.log"
XAPP_LOG="${LOG_DIR}/xapp-monitor.log"
rm -f "${RIC_LOG}" "${AGENT_LOG}" "${XAPP_LOG}"

echo "Starting nearRT-RIC..."
"${RIC_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${RIC_LOG}" 2>&1 &
RIC_PID=$!
sleep 3

echo "Starting emu_agent_gnb..."
"${AGENT_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${AGENT_LOG}" 2>&1 &
AGENT_PID=$!
sleep 4

XAPP_PID=""
if [ -x "${SDK_KPM_XAPP_BIN}" ]; then
  echo "Starting SDK-build xapp_kpm_moni..."
  timeout 18s "${SDK_KPM_XAPP_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${XAPP_LOG}" 2>&1 &
  XAPP_PID=$!
elif [ -x "${SDK_MULTI_XAPP_BIN}" ]; then
  echo "Starting SDK-build xapp_gtp_mac_rlc_pdcp_moni..."
  timeout 18s "${SDK_MULTI_XAPP_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${XAPP_LOG}" 2>&1 &
  XAPP_PID=$!
elif [ -x "${KPM_XAPP_BIN}" ]; then
  echo "Starting xapp_kpm_moni..."
  timeout 18s "${KPM_XAPP_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${XAPP_LOG}" 2>&1 &
  XAPP_PID=$!
elif [ -x "${MULTI_XAPP_BIN}" ]; then
  echo "Starting xapp_gtp_mac_rlc_pdcp_moni..."
  timeout 18s "${MULTI_XAPP_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${XAPP_LOG}" 2>&1 &
  XAPP_PID=$!
elif PYTHONPATH="${PY_SDK_DIR}:${PYTHONPATH:-}" python3 - <<'PY' >/dev/null 2>&1
import xapp_sdk
PY
then
  echo "Starting Python MAC/RLC/PDCP/GTP xApp..."
  timeout 18s env PYTHONPATH="${PY_SDK_DIR}:${PYTHONPATH:-}" python3 "${PY_XAPP}" >"${XAPP_LOG}" 2>&1 &
  XAPP_PID=$!
else
  echo "No built C monitor xApp and no Python xapp_sdk module found." >"${XAPP_LOG}"
fi

if [ -n "${XAPP_PID}" ]; then
  wait "${XAPP_PID}" 2>/dev/null || true
fi

echo "Stopping processes..."
kill "${AGENT_PID}" "${RIC_PID}" 2>/dev/null || true
wait "${AGENT_PID}" 2>/dev/null || true
wait "${RIC_PID}" 2>/dev/null || true

echo "nearRT-RIC monitor log: ${RIC_LOG}"
tail -80 "${RIC_LOG}" || true
echo
echo "emu_agent_gnb monitor log: ${AGENT_LOG}"
tail -80 "${AGENT_LOG}" || true
echo
echo "xApp monitor log: ${XAPP_LOG}"
tail -120 "${XAPP_LOG}" || true
