# Environment Capability Audit

Audit date: 2026-08-06 (Asia/Calcutta)

## Verdict

WSL2 Ubuntu 22.04 is the best available live-validation environment. Network namespaces, veth pairs, `tc netem`, software-timestamped `linuxptp`, and nanosecond-precision `tcpdump` capture were exercised successfully. Tier-3 hardware validation is blocked because no physical NIC PTP hardware clock or GNSS receiver is exposed to WSL.

## Environment

| Item | Measured result |
|---|---|
| Host | Windows 11 Home Single Language 10.0.26200 (build 26200) |
| Linux | Ubuntu 22.04.5 LTS under WSL2 |
| WSL kernel | `6.18.33.1-microsoft-standard-WSL2` |
| CPU | 12 logical host cores; 6 exposed to WSL |
| RAM | 23.91 GiB host; 15 GiB exposed to WSL |
| Free RAM at audit | 5.61 GiB host; about 14 GiB WSL available |
| Free disk | 83.64 GiB on C:; about 929 GiB reported in WSL root filesystem |
| Python | 3.12.13 in validated Windows venv; 3.10.12 in Ubuntu |
| Existing venvs | `.venv`, `.venv-codex`, `.venv-codex-priv`; only `.venv-codex-priv` has the pinned runtime dependencies |
| Requirement install | PASS on Python 3.12; **FAIL on Python 3.10** because `numpy==2.4.1` requires Python >=3.11 (and `pandas==3.0.0` also exceeds the stated 3.10 support) |
| Full test suite | Windows rerun uses a project-local pytest base temp because the host global pytest temp has an ACL error; final result is recorded in `docs/LIVE_VALIDATION.md` |

The initial Windows test invocation reached all 39 pre-increment tests: 32 passed and seven failed during fixture setup because `C:\Users\Admin\AppData\Local\Temp\pytest-of-Admin` denied directory enumeration. Project-local Windows temp directories later inherited the same restriction. This is an environment ACL failure, not an application assertion failure; the native-`/tmp` WSL rerun is the valid regression gate.

Post-audit resolution: `requirements-py310.txt` installed cleanly into `/home/oranuser/.venvs/oran-live` (`pip check`: no broken requirements), and the expanded **42-test** suite passed in WSL using a native `/tmp` base directory. Windows project-local temp directories inherited the same ACL problem, so the WSL result is the authoritative gate.

## Tooling

| Tool | Status | Version / note |
|---|---|---|
| `ptp4l` | INSTALLED | linuxptp 3.1.1 |
| `pmc` | INSTALLED | linuxptp 3.1.1 |
| `phc2sys` | INSTALLED | linuxptp 3.1.1 |
| `synce4l` | MISSING / INSTALLABLE | Not in the Ubuntu 22.04 apt index; requires a source build. Live collection must degrade explicitly until built/configured. |
| `tcpdump` | INSTALLED | 4.99.1, libpcap 1.10.1 |
| `ip`, `tc` | INSTALLED | iproute2 5.15.0 |
| `ethtool` | INSTALLED during audit | 5.16 (`apt-get install -y ethtool`) |
| `gcc` | INSTALLED | 11.4.0 |
| `make` | INSTALLED | 4.3 |

The proposal assumed linuxptp v4.x field names, but this laptop has v3.1.1. Live parsers must be verified against the actual v3.1.1 output rather than assuming v4.x formatting.

## Privileges And Kernel Features

| Probe | Result | Evidence |
|---|---|---|
| Passwordless `sudo` as `oranuser` | NO | `sudo -n true` reports that a password is required |
| Unattended root from Windows | YES | `wsl -d Ubuntu-22.04 -u root` succeeds; use this for controlled harness runs |
| Network namespace | PASS | Created and removed `caudns` |
| veth pair | PASS | Created `caud0`/`caud1`, moved peer into namespace, brought both links up |
| `tc netem` | PASS | Applied 1 ms delay, 200 us variation, and 1% loss; qdisc was observable |
| Nanosecond tcpdump | PASS | Captured a packet at `20:48:38.155187753` using `--time-stamp-precision=nano` |
| Probe cleanup | PASS | Follow-up showed no audit namespace or veth interface remained |

## Hardware Checks

| Interface/device | Timestamp capability |
|---|---|
| `lo` | Software transmit/receive/system timestamping only; no PTP Hardware Clock |
| `eth0` | Software transmit/receive/system timestamping only; no PTP Hardware Clock |
| `docker0` | Software receive/system timestamping only; no PTP Hardware Clock |
| `/dev/ptp0` | Present as Hyper-V synthetic `ptp_hyperv`; `clock_name=hyperv`, `max_adjustment=0`. This is not a NIC PHC. |
| GNSS serial devices | No `/dev/ttyACM*` or `/dev/ttyUSB*` found |
| GPS daemon | `gpsd` absent/not running |

## Phase 1 Feasibility

| Work item | Status | Requirement / blocker |
|---|---|---|
| Live `pmc` collection | READY | linuxptp 3.1.1 and software-timestamped veth harness available; parser compatibility must be tested live |
| Live `synce4l` collection | NEEDS-INSTALL | Source build and a real SyncE-capable interface/configuration are required. Collector will record unavailable QL without crashing. |
| netem + ptp4l harness | READY | Root, netns, veth, netem, ptp4l, and tcpdump probes passed |
| Two-hour unattended baseline | READY WITH CONTROLS | Run through `wsl -u root`, keep Windows awake, and stream artifacts. Passwordless `sudo` is unavailable but not required through the root WSL launch path. |
| Planned GM change | READY | Two software-timestamped ptp4l masters can be created in namespaces; no special NIC required |
| Hardware-timestamped Tier 3 | BLOCKED | No physical NIC PHC/hardware timestamp mode and no GNSS receiver |

### Two-hour disk projection

The existing 90-second real baseline artifacts measured 205,092 bytes for pcap and 70,317 bytes for ingested telemetry. Linear projection to two hours is approximately 16.4 MB pcap plus 5.6 MB telemetry (22.0 MB total). Allowing 10x overhead for rolling CSV, logs, and run metadata is still below 250 MB, far inside the measured 83.64 GiB free on C:. This is a projection from measured files; the final achieved run size will be reported separately.

## Blocked Items

- **Live SyncE QL:** `synce4l` is not installed and the virtual WSL interfaces are not SyncE-capable hardware. Parser/collector behavior can be fixture-tested, but a meaningful live QL measurement is blocked pending Tier-3 hardware and source-built/configured `synce4l`.
- **Hardware timestamps and physical GNSS:** blocked by absent devices, not by software.
