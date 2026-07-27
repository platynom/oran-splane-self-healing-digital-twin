#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${HOME}/oran-lab"
mkdir -p "${LAB_DIR}"

echo "[1/5] Installing Linux build dependencies"
sudo apt update
sudo apt install -y \
  git build-essential cmake ninja-build pkg-config \
  autoconf automake libtool bison flex \
  python3 python3-pip python3-dev python3-venv \
  libsctp-dev lksctp-tools \
  libconfig-dev libssl-dev \
  iproute2 net-tools

echo "[2/5] Cloning OpenAirInterface 5G RAN"
cd "${LAB_DIR}"
if [ ! -d openairinterface5g ]; then
  git clone https://gitlab.eurecom.fr/oai/openairinterface5g.git
else
  git -C openairinterface5g pull --ff-only || true
fi

echo "[3/5] Cloning FlexRIC"
cd "${LAB_DIR}"
if [ ! -d flexric ]; then
  git clone https://gitlab.eurecom.fr/mosaic5g/flexric.git
else
  git -C flexric pull --ff-only || true
fi

echo "[4/5] Cloning OAI 5G Core federation"
cd "${LAB_DIR}"
if [ ! -d oai-cn5g-fed ]; then
  git clone https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed.git
else
  git -C oai-cn5g-fed pull --ff-only || true
fi

echo "[5/5] Preparing Python environment for this project"
PROJECT_DIR="${HOME}/projects/oran-digital-twin"
if [ -d "${PROJECT_DIR}" ]; then
  cd "${PROJECT_DIR}"
  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  python run_demo.py --run-name wsl_smoke_test --duration 10 --seed 42
else
  echo "Project directory not found at ${PROJECT_DIR}."
  echo "Copy it first:"
  echo 'mkdir -p ~/projects'
  echo 'cp -r "/mnt/c/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin" ~/projects/oran-digital-twin'
fi

cat <<'NEXT'

Bootstrap source download completed.

Next build checks to run manually inside Ubuntu:

1) Build FlexRIC:
   cd ~/oran-lab/flexric
   mkdir -p build
   cd build
   cmake ..
   make -j"$(nproc)"
   sudo make install
   sudo ldconfig

2) Install OAI dependencies and build simulator-capable gNB/UE:
   cd ~/oran-lab/openairinterface5g/cmake_targets
   ./build_oai -I
   ./build_oai --gNB --nrUE -w SIMU

After those pass, we wire FlexRIC KPM output into the project telemetry adapter.
NEXT
