#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${HOME}/oran-lab"
FLEXRIC_DIR="${LAB_DIR}/flexric"
SDK_BUILD_DIR="${FLEXRIC_DIR}/build-python-xapp"

if [ ! -d "${FLEXRIC_DIR}" ]; then
  echo "Missing FlexRIC checkout: ${FLEXRIC_DIR}"
  exit 1
fi

if ! command -v gcc-12 >/dev/null 2>&1; then
  echo "Missing gcc-12. Install it with: sudo apt install -y gcc-12 g++-12"
  exit 1
fi

if ! command -v g++-12 >/dev/null 2>&1; then
  echo "Missing g++-12. Install it with: sudo apt install -y gcc-12 g++-12"
  exit 1
fi

if ! command -v swig >/dev/null 2>&1; then
  echo "Missing swig. Install it with: sudo apt install -y swig python3-dev"
  exit 1
fi

SWIG_VERSION="$(swig -version | awk '/SWIG Version/ {print $3}')"
SWIG_CMAKE="${FLEXRIC_DIR}/src/xApp/swig/CMakeLists.txt"
if [[ "${SWIG_VERSION}" == 4.0.* ]] && grep -q "FIND_PACKAGE(SWIG 4.1 REQUIRED)" "${SWIG_CMAKE}"; then
  echo "Detected SWIG ${SWIG_VERSION}. FlexRIC asks for 4.1, but Ubuntu 22.04 ships 4.0.2."
  echo "Applying local compatibility patch: SWIG 4.1 -> SWIG 4.0"
  cp -n "${SWIG_CMAKE}" "${SWIG_CMAKE}.orig"
  sed -i 's/FIND_PACKAGE(SWIG 4.1 REQUIRED)/FIND_PACKAGE(SWIG 4.0 REQUIRED)/' "${SWIG_CMAKE}"
fi

echo "Configuring FlexRIC Python xApp SDK build in ${SDK_BUILD_DIR}"
cmake -S "${FLEXRIC_DIR}" -B "${SDK_BUILD_DIR}" \
  -DCMAKE_C_COMPILER=gcc-12 \
  -DCMAKE_CXX_COMPILER=g++-12 \
  -DXAPP_MULTILANGUAGE=ON \
  -DXAPP_TARGET_LANGUAGE=PYTHON_LANG \
  -DE2AP_ENCODING=ASN \
  -DE2AP_VERSION=E2AP_V2 \
  -DBUILDING_LIBRARY=STATIC \
  -DSANITIZER=NONE

if cmake --build "${SDK_BUILD_DIR}" --target help | grep -q '^... xapp_sdk'; then
  echo "Building xapp_sdk target..."
  cmake --build "${SDK_BUILD_DIR}" --target xapp_sdk -j1
else
  echo "xapp_sdk target was not generated. Building all targets to surface the exact CMake error..."
  cmake --build "${SDK_BUILD_DIR}" -j1
fi

PY_SDK_DIR="${SDK_BUILD_DIR}/examples/xApp/python3"
if [ ! -f "${PY_SDK_DIR}/xapp_sdk.py" ] || [ ! -f "${PY_SDK_DIR}/_xapp_sdk.so" ]; then
  echo "Python SDK output not found in ${PY_SDK_DIR}"
  exit 1
fi

echo "Python xApp SDK built successfully:"
echo "${PY_SDK_DIR}/xapp_sdk.py"
echo "${PY_SDK_DIR}/_xapp_sdk.so"
echo
echo "Next test:"
echo "PYTHONPATH=${PY_SDK_DIR} ~/projects/oran-digital-twin/scripts/wsl_flexric_monitor_smoke.sh"
