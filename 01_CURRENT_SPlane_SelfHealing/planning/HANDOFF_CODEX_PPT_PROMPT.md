# MASTER PROMPT FOR CODEX — build the full project presentation (paste this whole file; Codex must have folder access)

You are an autonomous presentation engineer. Build a polished, technically-correct **.pptx** that explains this project end to end, from main topic to future hardware. Work in the project folder, verify your output, and do not invent numbers — read them from the repo. Deliver `Project_FullReview_Presentation.pptx` at the project root.

## 0. GROUND RULES (read first)
- **Tooling:** use `pptxgenjs` (Node). Set `pres.layout = "LAYOUT_WIDE"` (13.333×7.5). Hex colors WITHOUT `#`. One `new pptxgen()` only. Put speaker notes on every slide via `slide.addNotes(...)`.
- **Never fabricate numbers.** Pull the real results from these files and use them verbatim:
  - `oran_splane_selfhealing/results/discriminator_metrics.csv`
  - `oran_splane_selfhealing/results/benchmark_results.csv`
  - `oran_splane_selfhealing/dataset/splane_windows.csv` (label counts)
  - `oran_splane_selfhealing/results/SUMMARY.md` and `REALISM_NOTES.md`
- **Honesty:** state clearly that current results are **emulation** (physics-based simulation), not hardware-timestamped PTP. Do not overclaim.
- **Reuse the diagram** already in the repo if present: `arch.png` (system architecture). If missing, generate a clean architecture SVG→PNG (via `cairosvg`) before building slides.
- **QA before finishing:** convert to PDF (`soffice --headless --convert-to pdf`), rasterize (`pdftoppm -jpeg -r 150`), and visually check EVERY slide for overflow/overlap; fix and re-render. Also run the pptx validator if available.

## 1. PROJECT FACTS (authoritative — use these, verify against the repo)
- **Main topic (fixed):** *AI-Native Self-Healing O-RAN Network using a Digital Twin.*
- **Layer/domain:** the O-RAN **Open Fronthaul Synchronization plane (S-plane)** — timing between O-DU and O-RU over PTP (IEEE-1588) + SyncE; ~100 ns time-error budget; a timing attack crashes a base station in ~2 s.
- **Problem statement (specialized):** given passive S-plane timing telemetry, (1) detect a sync anomaly, (2) **discriminate H0 benign fault vs H1 malicious attack**, (3) **verify each candidate recovery action in a digital twin**, (4) commit the best action **before the ~2 s failure window** — minimizing wrong-action rate and recovery time.
- **How it relates to the main topic:** it IS the main topic made concrete — O-RAN (fronthaul), AI-native (learned discrimination), self-healing (autonomous recovery), digital twin (verifies the fix). Say this explicitly.
- **Prior work / gap:** TIMESAFE (ACM ToPS, 2025) proves the attack and builds a 97.5% **detector**, but stops at detection: no recovery action, and no fault-vs-attack separation. Our contribution is exactly that missing **response step**. Honest scope: **integration + experimental validation + released dataset**, NOT a new algorithm.
- **Provenance nuance (state precisely, do not overclaim):** O-RAN WG11 "Security Threat Modeling and Remediation Analysis" lists PTP master-clock spoofing on the Open Fronthaul as a threat (this is the O-RAN source). The phrase "no comprehensive fronthaul security standard yet" is the *research literature's* assessment (TIMESAFE; arXiv 2304.05513), NOT an official O-RAN quote.
- **The 8 built components (explain each, step by step):**
  1. **S-plane simulator** (`fronthaul_sim/simulator.py`) — clock-servo model producing PTP/SyncE telemetry (offset, path delay, PDV, freq error, SyncE QL, seq id, msg type, GNSS/holdover flags).
  2. **Fault & attack injectors** (`faults/injectors.py`) — H0: GNSS-loss/holdover, PDV/congestion, SyncE-degrade; H1: PTP spoof, replay. Hardened for realism (removed giveaway labels, overlapping magnitudes, evasive mimicry, attacks-during-congestion, sensor noise).
  3. **Feature extraction** (`telemetry/features.py`) — 0.4 s sliding windows (0.2 s step) → 10 features; majority label per window.
  4. **Dataset builder** (`dataset/build.py`) — assembles labelled dataset + datasheet (~2,508 windows: ~1,614 healthy, ~536 H0, ~358 H1 — VERIFY exact counts from the CSV).
  5. **Fault-vs-attack discriminator** (`discriminator/model.py`) — Random Forest (90 trees, depth 6), stratified 65/35 split; vs a detection-only baseline. (VERIFY: ~98.7% acc, ROC-AUC ~0.999, confusion ~[[186,2],[2,123]]; baseline ~40%.)
  6. **Digital twin** (`twin/model.py`) — per-action counterfactual drift forecast (decay/floor model) + a **fidelity score** that lowers trust when telemetry is messy.
  7. **Governed self-healing loop** (`healing/loop.py`) — detect → classify → shortlist actions → twin-verify → commit best if it beats safe default AND fidelity is high, else safe default; records auditable reason + decision time. Action space: isolate_rogue_master, failover_gnss, failover_lls_c1/c2/c3, holdover, reroute_path, safe_default.
  8. **Benchmark** (`benchmark/run.py`) — governed loop vs baselines (detection-only/no-response, always-holdover, always-failover); metrics: recovery success, wrong-action rate, MTTR, peak time error, within-2 s. (VERIFY: governed ≈ 0.95 recovery / 0.05 wrong-action / 0.55 s MTTR / 86 ns peak.)
- **Reproducibility:** one command `python scripts/run_all.py`; tests pass 3/3.

## 2. REQUIRED SLIDE STRUCTURE (≈ 18–22 slides)
Design: dark title/section dividers, light content slides; one accent color for "timing/danger", one for "good/recovery". Every slide has a visual (diagram, icon row, stat callout, or table) — no plain bullet walls. Vary layouts.

1. **Title** — main topic + subtitle + author + status chips.
2. **The main topic explained** — what "AI-Native Self-Healing O-RAN with a Digital Twin" means, in one clear picture.
3. **Background / why timing matters** — O-DU/O-RU, fronthaul, S-plane, 100 ns budget, 2 s crash (stat callouts).
4. **Where we sit — the layer** — a small OSI/O-RAN-plane map with the S-plane (L1/L2) highlighted; state it's NOT routing and NOT the radio air-interface.
5. **Related work** — a table: TIMESAFE (detect only), OpenTwin (twin for energy/data), conflict-mitigation (xApp conflicts), each with "what it does / what it leaves open". Cite venues.
6. **The problem statement** — formal H0-vs-H1 + twin-verified recovery; and a line mapping it to each word of the main topic.
7. **Contribution & honest scope** — the response step + fault/attack split + dataset; "not a new algorithm."
8. **System architecture** — the `arch.png` diagram with a short caption of each block.
9–16. **Step-by-step, part-by-part build** — ONE slide per component (the 8 above). For each: a plain-language line, the key technical terms, and what it does. Use small sub-diagrams/icons.
17. **The self-healing loop as a FLOW** — a left-to-right pipeline: Detect → Discriminate (H0/H1) → Twin-verify → Commit/Fallback, with the action menu. (See §3 for the "motion" treatment.)
18. **Results — discrimination** — stat callouts + confusion matrix + "why it's believable, not overfit" (from REALISM_NOTES.md).
19. **Results — self-healing benchmark** — the comparison table + a takeaway; note governed loop stays in the 100 ns budget.
20. **What's done vs what's next** — two columns (emulation tier done; linuxptp/netem next; hardware optional).
21. **HARDWARE & COST ESTIMATE (next phase)** — see §4. This is required and detailed.
22. **Close / contribution recap + honest limitations.**

## 3. DIAGRAMS AND "MOTION"
- Build clean **vector diagrams** as SVG then rasterize to PNG (cairosvg) and insert: (a) the architecture (reuse arch.png), (b) the OSI/plane map, (c) the 4-stage loop flow with arrows.
- **"Motion" / animated build:** PowerPoint animations can't be written reliably from a script, so simulate motion two ways: (i) a **progressive build** — 3 consecutive slides that reveal the loop one stage at a time (stage 1 highlighted, then 1–2, then 1–4), giving a "walkthrough" feel when advancing; and (ii) OPTIONALLY embed a short **animated GIF** of the timing recovery: generate frames with matplotlib showing time-error drifting up under an attack, then dropping back within the 100 ns budget after the governed action, save as `results/recovery.gif`, and place it on the benchmark slide. If GIF embedding is unreliable, insert 3 static frames side by side instead.

## 4. HARDWARE & COST ESTIMATE — required detail (this is the part the user most wants)
Produce **two slides or one slide + a backup**: a tiered bill-of-materials table with indicative costs (mark them "indicative, verify with vendors"), a **connection diagram** showing how the hardware attaches to the current software setup, and a "considerations you may not have listed" box.

Frame it around the key insight: **because our problem is the S-plane (timing), the real testbed is mostly networking/timing gear, NOT SDRs. A real O-RU is only needed to physically show the base-station crash.**

**Tier A — Real PTP/SyncE timing lab (no radio; does everything in our proposal for real):**
| Item | Purpose | Indicative cost |
|---|---|---|
| 2–3 PCs/servers with **PTP hardware-timestamping NICs** (Intel I210/I225/E810) | O-DU (PTP slave + monitor), attacker, load generator | NIC $30–$300 each; reuse existing PCs |
| **Timing-aware Ethernet switch** (PTP boundary/transparent clock + SyncE, ITU-T G.8275.1) | carries fronthaul timing | budget managed w/ PTP ~$500; telecom-grade $1,500–$8,000 |
| **PTP Grandmaster** (GNSS-disciplined) OR a PC running `ptp4l` as GM + **GPSDO** | trusted reference clock | appliance $2,000–$10,000; DIY GPSDO+Pi $150–$400 |
| **GNSS receiver + antenna + PPS** | GNSS reference; create GNSS-loss/holdover faults | $50–$300 |
| SFP modules, precision cabling, **network TAP / mirror port** | passive PTP capture | $100–$400 |
| **Time-error tester / reference** (optional, for ns-true validation) | measure real time error vs G.8273.2 | rental/borrow; buy $5k+ |

Tier A total (DIY/budget): **~$800–$3,000** reusing PCs. Professional: **~$6,000–$18,000**.

**Tier B — Add real O-RAN radio realism (optional, to show the actual 2 s crash):**
| Item | Purpose | Indicative cost |
|---|---|---|
| Real **O-RU** (7.2x split) + **O-DU** server (e.g. O-RAN SC / NVIDIA Aerial style) | full base-station demo | O-RU $3,000–$20,000+; server $2,000–$6,000 |
| SDR + GPSDO (only if radio air-interface also wanted) | UE/RF side | USRP $1,500–$5,000 |

**How it connects to our current software setup (draw this):**
- Our `oran_splane_selfhealing` code becomes the **monitor + decision** side: the passive-capture + discriminator + twin + governed-loop run on the O-DU PC, reading **real** PTP telemetry from `linuxptp` (`ptp4l`/`phc2sys`/`ts2phc`) instead of the simulator. The recovery actions map to **real** commands (switch PTP source / enter holdover / block the rogue master via BMCA/allow-list). The attacker PC runs spoof/replay. Same software, real inputs.

**Software still needed on the hardware (list it):** `linuxptp` (ptp4l, phc2sys, ts2phc), SyncE config, `tcpdump`/Wireshark for capture, `tc netem` for controlled PDV, NIC PTP-hardware-clock (`/dev/ptpN`) drivers.

**Considerations you probably haven't listed (include this box):** PTP profile choice (G.8275.1 full timing support), boundary-clock vs transparent-clock switch, MACsec for fronthaul link security, GNSS antenna roof access / sky view, PPS distribution & cabling length/skew, holdover oscillator quality (OCXO vs TCXO), lab power + UPS, thermal stability (timing drifts with temperature), a golden **reference clock** to measure against, RF licensing / shielding if the O-RU transmits, and time to learn `linuxptp`. Note clearly that **Tier A needs no radio and no spectrum licence.**

## 5. WORKING PROTOCOL
Build the deck, generate/reuse diagrams, pull real numbers from the CSVs, render to images, inspect every slide, fix overflow/overlap, re-render, validate, and save `Project_FullReview_Presentation.pptx` at the project root. Report a one-line summary of what you produced.

Begin now.
