# Handoff prompt — paste everything below the line into the new Claude session

---

You are picking up a Samsung PRISM research project mid-stream. Read this whole
brief, then read the files it names before doing anything. **Do not guess, do not
infer numbers, and do not re-derive figures from memory — every number below is
traceable to a file on disk, and if you need one that is not here, open the file.**

## 0. First actions, in this order

1. If this session is not linked to the user's computer (Windows,
   `desktop-7q6ot1v`, user `Admin`), ask them to link it. Most of what follows
   lives on that machine.
2. Read these, newest first. They supersede everything else:
   - `C:\Users\Admin\Documents\AI-Native Self-Healing O-RAN Network using a Digital Twin\outputs\B6_two_machine_2026-10-02\run2\B6_MEASUREMENT_RECORD_run2.md` ← **the current result**
   - `...\outputs\B6_two_machine_2026-10-02\run2\PRE_REGISTRATION_RUN2.md`
   - `...\outputs\B6_two_machine_2026-10-02\B6_MEASUREMENT_RECORD_2026-10-02.md` (run 1, failed)
   - `C:\Users\Admin\Desktop\oran_drift_analysis\PRE_REGISTRATION.md` (run 1 plan)
3. Do not read the whole repo. It is 26,614 files, ~9,283 substantive after
   excluding `.git`, `.venv*`, `node_modules`, `__pycache__`, `site-packages`.
   Most of the bulk is run data (2,599 `.log`, 638 `.csv`, 450 `.pcap`,
   291 `.pth`). The claim-bearing set is 266 `.md`, 110 `.xlsx`, 353 `.py`.

## 1. The project

Security of O-RAN Open Fronthaul **S-plane timing** (PTP / SyncE / GNSS). The
system detects timing anomalies, separates benign faults from attacks, checks
recovery in a digital twin, and picks a response inside ~2 s (figure from
TIMESAFE, ACM TOPS DOI `10.1145/3775060`). CPU only. The stated contribution is
integration, validation and reproducible data — not a new ML algorithm.

**The project's answering standard, which you must obey:** every claim traces to
a file, a standard clause, or explicit reasoning. Keep evidence layers separate —
configured condition / packet observation / independent pre-action impact /
action / outcome. A software testbed is not hardware, is not attack detection,
and is not demonstrated harm. Never overclaim.

**Precedent that governs everything:** S15 ran against a frozen 0.8 specificity
criterion, scored 0.533, and was recorded as **NOT ESTABLISHED** rather than
having the criterion moved. Do not ever relax a criterion to make a result pass.

## 2. What this work is about — fault B6

`deliverables\ORAN_Fault_Detectability_v2026-09-29.xlsx`, sheet DETECTABILITY,
row **B6 "Oscillator drift / thermal"** (BENIGN class). Status in that sheet:
`NO — structurally impossible`, because all testbed namespaces share one kernel
clock from one crystal, so measured inter-node offset is zero by construction.
The same row says: *"A 2nd PC SOLVES THIS. This is the single fault your
procurable hardware unlocks."*

A teammate's laptop supplied the second crystal on 2026-10-02.

**B6 is BENIGN.** The detector's job is to call real oscillator drift benign, not
an attack. The discriminator is temperature correlation — the Parameter Fault
Matrix lists under *L8 Oscillator: temperature*: *"explains benign thermal drift;
absence of correlation implicates attack."*

## 3. What was measured — two runs, both on 2026-10-02

Two laptops, same program, each logging every 10 s: raw `perf_counter`
(QueryPerformanceCounter, undisciplined by Windows), wall clock, and an SNTP
offset from `time.google.com`. Differencing the two arms cancels the reference
and leaves the two crystals. No PTP ran between the machines.

Machines (identical across both runs): arm A `node_hash 720bc97877cf`,
Intel Fam 6 Model 165, Windows 11. Arm B `node_hash 2101a6b98881`,
Intel Fam 6 Model 186, Windows 10.

| | Run 1 (18:00–20:30) | Run 2 (21:13–00:13) |
|---|---|---|
| Arm A vs UTC | −4.189 ppm [−4.306, −4.086] | **−2.877 ppm** [−3.029, −2.736] |
| Arm B vs UTC | −24.351 ppm [−25.134, −23.565] | **−23.891 ppm** [−24.240, −23.532] |
| **Relative A−B** | +20.161 ppm [19.376, 20.969] | **+21.013 ppm** [20.623, 21.403] |
| Retained samples | 348 / 658 | 906 / 846 |
| Verdict | **NOT ESTABLISHED** (C1 failed) | **ESTABLISHED** (all five pass) |

Run 1 failed because probe v1 silently switched NTP server after any failed
sample — it thrashed 97 times on arm A, 21 on arm B — so rejection rule R2 threw
out 474 and 160 samples. Probe v2 pinned the reference; in run 2, R2 fired on
**zero** samples and reference homogeneity was 100.0% / 100.0%.

**CRITICAL — do not quote run 2's interval as the answer.** The two runs shift by
**+0.852 ppm**, and their CIs overlap over only 20.623–20.969 ppm (0.347 ppm
wide). Neither point estimate falls inside the other's interval. A run-1
robustness check across NTP-server subsets gave +18.8 to +20.2 ppm. The honest
statement is:

> **The two crystals differ by approximately 19 to 21 ppm.**

The within-run CI measures sampling noise only; run-to-run variation is about
twice as large.

## 4. Acceptance criteria (frozen before any data; identical across both runs)

| ID | Criterion |
|---|---|
| C1 | each arm retains ≥ 600 samples after rejection |
| C2 | common overlap ≥ 120 min |
| C3 | zero discontinuities (sleep / clock step) |
| C4 | both arms on the same reference, ≥ 95% homogeneous, same server |
| C5 | relative-offset 95% CI half-width < 1.0 ppm |

Rejection rules R1–R4: non-modal source, non-modal server, RTT outliers
(median + 3·MAD, hard cap 1 s), discontinuity flagging. ESTABLISHED only if all
five criteria pass.

## 5. What is established and what is NOT

**Established:** two independent physical crystals differ by ~19–21 ppm, measured
on real hardware, under a pre-registered protocol. The offset is **not constant**
over hours (it moved 0.85 ppm between runs) — which is the behaviour B6
describes and which a single-clock testbed cannot exhibit at all.

**NOT established, and must not be claimed:**

1. **Not an end-to-end B6 detection test.** No PTP between the machines; the
   detector never saw this drift. This is a parameter measurement.
2. **No stability figure.** Relative ADEV falls as τ⁻¹ across the whole range in
   both runs (short-τ log-log slope −0.786 run 1, −0.878 run 2, `crossover_tau_s:
   null`, ADEV at τ=10 s 7.80e-04 and 1.50e-03). The pair is **floor-limited**:
   no ADEV, TDEV or MTIE number from either run describes the crystals — they
   describe the NTP-over-WiFi path. **Longer runs will not fix this**; it needs
   hardware timestamping.
3. **No ns-scale or mask-compliance claim.** Floor is milliseconds, ~10⁵ above
   G.8273.2 cTE (50/20/10 ns). Nothing may be compared to a G.8273.2 or G.8261
   wander mask.
4. **Thermal discriminator unevaluated.** `temp_log.py` v1 ran on arm A in both
   runs and captured **0 temperatures out of 1080 samples** — Windows will not
   expose `MSAcpi_ThermalZoneTemperature` to an unprivileged process on that
   machine. Only CPU load (mean 42.9%) and frequency (2592 MHz, flat) recorded.
5. **Not telecom-grade oscillators.** Uncompensated consumer quartz, not
   OCXO/TCXO/Rb — a worst-case consumer envelope, not a G.8273.2 class.
6. **Row B6 in the Fault Detectability workbook is NOT changed** by either run,
   and must not be. That row describes detectability on the software testbed,
   which still has one clock.

## 6. THE NEXT STEP — this is what to do

Close the thermal discriminator. **This needs the user's laptop only. The
teammate is not required.** Temperature is a per-machine property; the second
laptop was only ever needed for the relative offset, which is done.

Step 1 — determine whether temperature is readable at all:

```
cd %USERPROFILE%\Desktop\oran_drift_v2 && python temp_log.py --probe
```

Then **right-click Command Prompt → Run as administrator** and run it again.
`temp_log.py` v2 (sha256 `a57de42543fd7aa627ea60fe2ae3823bec0dd4fde14d46edd174e081c4f80e15`)
tries five sources — ACPI thermal zone via WMI, Win32 perf counters,
OpenHardwareMonitor/LibreHardwareMonitor WMI, LibreHardwareMonitor's web server
on 127.0.0.1:8085, and psutil — and reports which worked.

- If a source works: run the drift probe and the temp logger together for 180
  min on arm A alone, **across a period where temperature actually changes**
  (a flat-temperature run yields no slope — deliberately load the CPU for a
  stretch, or span a warming/cooling period). Then regress ppm against
  temperature to get the frequency-vs-temperature slope.
- If nothing works even elevated: the machine has no software-readable sensor.
  Options are LibreHardwareMonitor running in the background, a USB temperature
  probe, or recording room temperature by hand every 15 minutes.

**Before that run, freeze and hash a new pre-registration**, exactly as runs 1
and 2 did. Do not reuse run 2's document.

Everything after this needs hardware the project does not have: hardware
timestamping (i210/i226-class NIC) for stability, and PTP between two hosts on
the same LAN — same room, ethernet cable, not over the internet — for an actual
B6 detection experiment.

## 7. Files and freeze hashes

**Probe and analysis** (`C:\Users\Admin\Desktop\`):
- `oran_drift_v2\drift_probe.py` — v2, pinned reference,
  `0f5c04b7268425419c8466208d6f00276bc8093a078ee60beb018156dd94f593`
- `oran_drift_v2\check_setup.py` — v2, strict pre-flight, `aebf8af7e0100ee4e96e205090160c4553bc81cfe1a95f08b6684102aee7e19e`
- `oran_drift_v2\temp_log.py` — v2, multi-source, `a57de42543fd7aa627ea60fe2ae3823bec0dd4fde14d46edd174e081c4f80e15`
- `oran_drift_analysis\pair_drift.py` — the frozen analyser, **unchanged across
  both runs**, `7518898ce878a7c4985506b229212b141f815103cd742c8393a4fa0fec573cb8`
- `oran_drift_analysis\selftest_pair_drift.py` — 25 assertions; synthetic ground
  truth recovered to 0.036 ppm, CI coverage 37/40 = 92%
- `oran_drift_analysis\selftest_probe_v2.py` — 24 assertions on the v2 probe
- `oran_drift\drift_probe.py` — v1, superseded, `703da1a97126a1d24ed3792a562c2e5a2a236a2aed7c8720141a1888dbb07be6`

**Raw data:** run 1 arm A in `Desktop\oran_drift\results\`; run 2 arm A in
`Desktop\oran_drift_v2\results\`; arm B for both runs arrived as zips in
`Downloads\` (`results.zip`, 2026-10-02 19:16 is run 2).

**Analysis command:**
```
python pair_drift.py --a <armA csv or dir> --b <armB csv or dir> --session <tag> --out <dir>
```
Needs numpy and matplotlib. Run `selftest_pair_drift.py` first if you touch anything.

## 8. Traps found in this project — do not repeat these

1. **Never run the drift probe inside WSL.** On Windows `perf_counter` is
   QueryPerformanceCounter, which Windows never disciplines — that is the
   measurement. Inside WSL2 it maps to a hypervisor-synced, NTP-slewed
   `CLOCK_MONOTONIC` and would silently absorb the drift, giving a plausible-
   looking near-zero answer. The testbed runs in WSL; the probe must not.
2. **Two different fault taxonomies are in play.** The workbooks use **A1–A8 /
   B1–B8**. `research\CATALOGUE_benign_faults.md` uses **B-01…B-70** plus
   D-1…D-14, X-01…X-15, R-01…R-12. Catalogue `B-06` is NOT workbook `B6`. No
   mapping table exists. Always say which scheme you mean.
3. **`research\` is untracked and unreviewed.** `git status` reports `?? research/`.
   Both files in it are AI chat transcripts pasted in — the benign catalogue ends
   with *"I did not write any files... say the word"*. Treat as unverified
   reference material, not project record. The entries relevant to B6 are
   **B-47** (oscillator ageing, ppb/day log-law) and **B-48** (temperature
   transient — quartz ~10 ppb/°C, "the ramp reverses when temperature recovers"),
   and discriminator **D-12** (holdover physics check: an attack is "drift that
   does not obey the oscillator model"). **B-29 is holdover entry and maps to
   workbook B1, not B6** — an earlier session got this wrong.
4. **`NEG-1` is mislabelled.** The validation record's conformance-negative suite
   says NEG-1 = clockClass 0; the catalogue's NEG-1 is the DUT's-own-clockIdentity
   test, and no catalogue NEG covers clockClass 0. NEG-2/3/5/11/15 all match.
5. **The coverage summary is wrong.** `outputs\manual_dataset_combined\coverage\
   coverage_summary.json` claims `"unreadable_or_unparsed": 0`. The jsonl shows
   only **956 of 4,604 records parsed (20.8%)**; 3,019 are `parsed: false`, 629
   have no parse field. Unparsed includes 88 `.md`, 91 `.xlsx`, 407 `.txt`,
   435 `.conf`, 338 `.csv`. Separately, `S15_FINAL_ACCEPTANCE_REVIEW.md`
   Amendment 1 wrongly says the script "was specified but never run" — it ran.
6. **linuxptp version is contradictory.** `ENV_CAPABILITY_AUDIT.md` and
   `LIVE_VALIDATION.md` record **3.1.1** installed; the v5/v7 deck claims "six
   genuine **linuxptp 4.0** daemons". Probably two testbeds. Verify with
   `ptp4l -v` before quoting either.
7. **`verify_frozen.sh` does not exist** anywhere in the repo, though the
   2026-09-17 validation record says it passed before every run. 214 `.sha256`
   files do exist.
8. **Environment:** WSL2 Ubuntu 22.04.5; `wsl -d Ubuntu-22.04 -u root` gives
   unattended root but passwordless `sudo` as `oranuser` does not (and root once
   returned `E_ACCESS_DENIED` on 2026-09-10). `requirements.txt` pins
   `numpy==2.4.1`, which needs Python ≥3.11 and **fails on Ubuntu's 3.10.12** —
   use `requirements-py310.txt` into `/home/oranuser/.venvs/oran-live`.
   `C:\Users\Admin\AppData\Local\Temp\pytest-of-Admin` has an ACL fault that
   breaks pytest on Windows; the authoritative gate is WSL with native `/tmp`.
   `/dev/ptp0` under WSL is Hyper-V synthetic `ptp_hyperv`, `max_adjustment=0` —
   not a NIC PHC. No GNSS device, no `gpsd`, `synce4l` absent.

## 9. Wider project state (for context; verify before quoting)

Current figures come from the V5 recomputation in `deliverables\V5_DISAGREEMENTS.md`
and `V5_SELFCHECK.md`, and the authoritative milestone table is the "Current
status" section of `outputs\empirical_software_network_pilot_v1\REMAINING_WORK_ACCEPTANCE_REGISTER.md`:
base sensitivity 0.625; v3 sensitivity 0.9896; overall specificity 0.7833;
attribution 84/96 = 0.875; specificity excluding `B_bc_replacement` 47/48 = 0.979
(not 1.000 — B3 replicate 4 is UNKNOWN); ARM A 51/56, ARM B 24/56, always-BENIGN
20/56 with exact McNemar p = 0.21875, so **ARM B is not distinguishable from
always-BENIGN**; window-level ROC-AUC 0.604 at n = 1,923; C1 crossing 60.54%
(interpolated inside an untested 60–65% bracket, decisive 60% level has n=1).
v7 is the current deck.

Standing limits: no retained PCAPs and no complete runtime config set in the
corrected archive; 130 ns is scoped to 5G FR2 intraband-contiguous CA relative
TAE, Timing Category A — **not** a universal O-RAN limit; ±1.5 µs is G.8271.1
reference point E; v3 is a post-observation fix evaluated on the same captures,
not pre-registered validation; no digital-twin, executed-healing,
fault-prediction or recovery-outcome experiment exists in this campaign.

Note `claude\PROJECT_CONTEXT.md` and `claude\VALIDATION_RECORD_2026-09-17.md`
stop at 2026-09-17 and are superseded in places by the above.

## 10. How to work

Report in short lines. If anything contradicts this brief, stop and say so
rather than working around it — this project has a documented history of defects
caught exactly that way (`gap_coverage_2026-09-20\corrected_final\
AUDIT_AND_CORRECTIONS_2026-09-20.md`: 4 defects found, 2 of them fabricating
data). Ask before editing any deliverable workbook, PDF or deck.

---
