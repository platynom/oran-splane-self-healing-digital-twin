# OAI/FlexRIC Option 2 Setup

This setup is for real OAI/FlexRIC telemetry in simulation mode.

Target flow:

```text
OAI gNB / RF simulator
-> OAI E2 agent
-> FlexRIC Near-RT RIC
-> E2SM-KPM xApp telemetry
-> this project telemetry adapter
-> digital twin + AI/self-learning + dashboard
```

## Current Machine Status

Checked from this workspace:

- Git for Windows is installed.
- WSL is not installed.
- Docker is not installed.

Therefore the first required step is WSL2 Ubuntu.

## Step 1: Install WSL2 Ubuntu

Open **PowerShell as Administrator** and run:

```powershell
wsl --install -d Ubuntu-22.04
```

Restart if Windows asks for it.

After restart, open **Ubuntu** from the Start menu and create the Linux username/password.

Verify:

```powershell
wsl --list --verbose
```

Expected: Ubuntu should show as WSL version 2.

If it shows version 1:

```powershell
wsl --set-version Ubuntu-22.04 2
```

## Step 2: Copy This Project Into WSL-Friendly Path

Inside Ubuntu:

```bash
mkdir -p ~/projects
cp -r "/mnt/c/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin" ~/projects/oran-digital-twin
cd ~/projects/oran-digital-twin
```

Reason: OAI/FlexRIC builds are much more reliable in the Linux filesystem than inside `/mnt/c`.

## Step 3: Bootstrap OAI/FlexRIC Sources

Inside Ubuntu:

```bash
chmod +x scripts/wsl_oai_flexric_bootstrap.sh
./scripts/wsl_oai_flexric_bootstrap.sh
```

This downloads:

- OpenAirInterface 5G RAN from `https://gitlab.eurecom.fr/oai/openairinterface5g`
- FlexRIC from `https://gitlab.eurecom.fr/mosaic5g/flexric`
- OAI 5G Core federation from `https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed`

## Step 4: What We Need From OAI/FlexRIC

For our project, we do not need full radio hardware first.

We need KPI telemetry such as:

- PRB utilization
- throughput
- latency
- packet loss
- BLER
- SINR or radio quality proxy
- UE/cell identifier
- service/slice identifier where available

The first integration target is E2SM-KPM telemetry from FlexRIC.

## Step 5: Integration With Our Project

Once FlexRIC produces KPM output, we connect it to:

```text
scripts/start_oai_metric_bridge.ps1 / future Linux bridge
-> our telemetry normalization
-> OranDecisionEngine
-> dashboard/report/model artifact
```

If FlexRIC produces logs first instead of a socket/API stream, we will parse logs/CSV first. That still counts as real OAI/FlexRIC telemetry replay.

## Current FlexRIC Build Notes

On Ubuntu 22.04, FlexRIC must be built with GCC/G++ 12 because the current source rejects GCC 11.

```bash
sudo apt install -y gcc-12 g++-12 asn1c
cd ~/oran-lab/flexric
rm -rf build
mkdir build
cd build
CC=gcc-12 CXX=g++-12 cmake ..
make nearRT-RIC emu_agent_gnb test_kpm_sm test_near_ric -j"$(nproc)"
```

The full `make -j"$(nproc)"` may fail on the optional `examples/xApp/c/monitor/RRC_MESSAGES` target because Ubuntu's packaged `asn1c` does not support the `-gen-UPER` flag expected by that example. This is not blocking for our immediate KPM telemetry objective.

To smoke-test the built RIC and GNB emulator:

```bash
cd ~/projects/oran-digital-twin
chmod +x scripts/wsl_flexric_kpm_smoke.sh
./scripts/wsl_flexric_kpm_smoke.sh
```

Expected successful signs:

- `nearRT-RIC` loads `ORAN-E2SM-KPM`.
- `emu_agent_gnb` sends `E2 SETUP-REQUEST`.
- `nearRT-RIC` receives E2 setup from `ngran_gNB`.
- `nearRT-RIC` accepts RAN function ID `2` with definition `ORAN-E2SM-KPM`.
- `emu_agent_gnb` receives `E2 SETUP RESPONSE`.

This proves the local FlexRIC Near-RT RIC and an emulated E2 node can talk. It is not yet live OAI gNB telemetry, but it is the correct RIC/E2/KPM foundation.

## Next Step: OAI RAN Build

After FlexRIC smoke test succeeds:

```bash
cd ~/oran-lab/openairinterface5g/cmake_targets
./build_oai -I
./build_oai --gNB --nrUE -w SIMU
./build_oai --gNB --nrUE -w SIMU --build-e2
```

This prepares OAI gNB/nrUE in RF simulator mode with E2 agent support.

To smoke-test OAI gNB against FlexRIC:

```bash
cd ~/projects/oran-digital-twin
chmod +x scripts/wsl_oai_flexric_rfsim_smoke.sh
./scripts/wsl_oai_flexric_rfsim_smoke.sh
```

This starts FlexRIC Near-RT RIC, starts OAI `nr-softmodem` with the FlexRIC RF simulator config, waits briefly, then prints logs from both sides.

## Important Notes

- This is not a small Python package install; OAI/FlexRIC are telecom stacks.
- WSL2 Ubuntu is required on this Windows laptop.
- Real RF requires SDR hardware later, but simulation mode does not.
- The current project remains usable while the telecom stack is being prepared.
