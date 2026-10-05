#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${HOME}/oran-lab"
FLEXRIC_DIR="${LAB_DIR}/flexric"
OAI_DIR="${LAB_DIR}/openairinterface5g"
FLEXRIC_BUILD="${FLEXRIC_DIR}/build"
OAI_BUILD="${OAI_DIR}/cmake_targets/ran_build/build"
LOG_DIR="${LAB_DIR}/logs"

RIC_BIN="${FLEXRIC_BUILD}/examples/ric/nearRT-RIC"
GNB_BIN="${OAI_BUILD}/nr-softmodem"
FLEXRIC_CONF="${FLEXRIC_DIR}/flexric.conf"
GNB_CONF="${OAI_DIR}/ci-scripts/conf_files/gnb.sa.band78.106prb.rfsim.flexric.conf"
SM_LIB_DIR="${FLEXRIC_BUILD}/flexric-sm-libs"

mkdir -p "${LOG_DIR}" "${SM_LIB_DIR}"
find "${FLEXRIC_BUILD}/src/sm" -name "*.so" -exec ln -sf {} "${SM_LIB_DIR}/" \;

for path in "${RIC_BIN}" "${GNB_BIN}" "${FLEXRIC_CONF}" "${GNB_CONF}" "${SM_LIB_DIR}/libkpm_sm.so"; do
  if [ ! -e "${path}" ]; then
    echo "Missing required file: ${path}"
    exit 1
  fi
done

RIC_LOG="${LOG_DIR}/nearRT-RIC-oai.log"
GNB_LOG="${LOG_DIR}/oai-gnb-flexric-rfsim.log"
rm -f "${RIC_LOG}" "${GNB_LOG}"

echo "Starting FlexRIC Near-RT RIC..."
"${RIC_BIN}" -c "${FLEXRIC_CONF}" -p "${SM_LIB_DIR}/" -a 127.0.0.1 >"${RIC_LOG}" 2>&1 &
RIC_PID=$!
sleep 3

echo "Starting OAI gNB RF simulator with FlexRIC config..."
cd "${OAI_BUILD}"
set +e
ulimit -s 1024
GNB_CMD=("${GNB_BIN}" \
  -O "${GNB_CONF}" \
  --rfsim \
  --sa \
  --noS1 \
  --no-itti-threads \
  --thread-pool N \
  --disable-stats \
  --rfsimulator.serveraddr server)

if [ "${USE_SUDO:-0}" = "1" ]; then
  timeout 25s sudo "${GNB_CMD[@]}" >"${GNB_LOG}" 2>&1
else
  timeout 25s "${GNB_CMD[@]}" >"${GNB_LOG}" 2>&1
fi
GNB_STATUS=$?
set -e

kill "${RIC_PID}" 2>/dev/null || true
wait "${RIC_PID}" 2>/dev/null || true

echo "OAI gNB exit status: ${GNB_STATUS}"
echo
echo "nearRT-RIC log: ${RIC_LOG}"
tail -120 "${RIC_LOG}" || true
echo
echo "OAI gNB log: ${GNB_LOG}"
tail -160 "${GNB_LOG}" || true

if [ "${GNB_STATUS}" -eq 124 ]; then
  echo "Smoke test timed out after 25s, which is acceptable if the gNB stayed running."
fi
