#!/usr/bin/env bash
set -euo pipefail

FLEXRIC_DIR="${HOME}/oran-lab/flexric"
BUILD_DIR="${FLEXRIC_DIR}/build"
CONF="${FLEXRIC_DIR}/flexric.conf"
SM_LIB_DIR="${BUILD_DIR}/flexric-sm-libs"
RIC_BIN="${BUILD_DIR}/examples/ric/nearRT-RIC"
AGENT_BIN="${BUILD_DIR}/examples/emulator/agent/emu_agent_gnb"
LOG_DIR="${HOME}/oran-lab/logs"

mkdir -p "${LOG_DIR}"

if [ ! -x "${RIC_BIN}" ]; then
  echo "Missing nearRT-RIC binary: ${RIC_BIN}"
  exit 1
fi

if [ ! -x "${AGENT_BIN}" ]; then
  echo "Missing emu_agent_gnb binary: ${AGENT_BIN}"
  exit 1
fi

if [ ! -f "${CONF}" ]; then
  echo "Missing FlexRIC config: ${CONF}"
  exit 1
fi

rm -rf "${SM_LIB_DIR}"
mkdir -p "${SM_LIB_DIR}"
find "${BUILD_DIR}/src/sm" -name "*.so" -exec ln -s {} "${SM_LIB_DIR}/" \;

if [ ! -f "${SM_LIB_DIR}/libkpm_sm.so" ] && [ ! -L "${SM_LIB_DIR}/libkpm_sm.so" ]; then
  echo "Missing KPM service model library in: ${SM_LIB_DIR}"
  exit 1
fi

RIC_LOG="${LOG_DIR}/nearRT-RIC.log"
AGENT_LOG="${LOG_DIR}/emu_agent_gnb.log"
rm -f "${RIC_LOG}" "${AGENT_LOG}"

echo "Starting nearRT-RIC..."
"${RIC_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${RIC_LOG}" 2>&1 &
RIC_PID=$!

sleep 3

echo "Starting emu_agent_gnb..."
"${AGENT_BIN}" -c "${CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${AGENT_LOG}" 2>&1 &
AGENT_PID=$!

sleep 8

echo "Stopping smoke-test processes..."
kill "${AGENT_PID}" "${RIC_PID}" 2>/dev/null || true
wait "${AGENT_PID}" 2>/dev/null || true
wait "${RIC_PID}" 2>/dev/null || true

echo "nearRT-RIC log: ${RIC_LOG}"
tail -80 "${RIC_LOG}" || true
echo
echo "emu_agent_gnb log: ${AGENT_LOG}"
tail -80 "${AGENT_LOG}" || true
