# Research Proposal — Twin-Verified Open-World Self-Healing in O-RAN

**Project:** AI-Native Self-Healing O-RAN Network using a Digital Twin
**Sub-direction:** Recovering from fault classes the model was never trained on, verified in a digital twin and demonstrated on a real Radio Unit (RU).
**Author:** Tanmay
**Status:** proposal / build plan. Honest about maturity, sources, and risk.

> **Source-access note.** Open-access papers (arXiv, MDPI) below were read in full. IEEE Xplore and Elsevier/ScienceDirect items were read at **abstract/metadata level only** — my web access does **not** route through your campus `.edu` network, so paywalls do not open for me. The papers I need in full text are listed in `papers/PAPERS_NEEDED.md`; drop the PDFs in `papers/` and I will read them directly.

---

## 1. Topic

**Twin-verified open-world self-healing:** a Near-RT RIC control loop that detects when an incoming fault does **not** match any fault class it was trained on, synthesises a candidate recovery action by reasoning over the live KPMs (rather than selecting a memorised policy), **verifies that action inside a calibrated digital twin before it touches the live network**, commits only if the twin confirms improvement, and folds the outcome back so the new class becomes "known" next time.

It sits exactly where the parent project sits: **Near-RT RIC xApp**, **RRC layer (3GPP L3)** in the O-CU-CP, over the **E2** interface — with the injected demonstrator fault originating one layer down at the **fronthaul (O-DU↔O-RU, eCPRI)**, which is what makes it invisible to a radio-KPM-trained model.

---

## 2. Problem statement

**Formal:**
> Every published AI self-healing agent is *closed-world*: it can only act on the fault classes present in its training distribution. Confronted with a genuinely new fault — one whose KPM signature is out-of-distribution — a closed-world agent must still map it onto its nearest known class and therefore applies a **wrong, potentially harmful** action (e.g. a needless handover that drops a live session), or fails silently. There is no established, packaged method for **safely recovering** from an unseen fault class **inside the near-real-time RRC loop** with **twin-verified** actions, validated on **real** RAN hardware.

**Plain-language:**
The AI healer is a doctor trained on ten diseases. Show it an eleventh and it confidently prescribes one of its ten — and on a live network a confident wrong fix is worse than doing nothing. We want a healer that recognises *"this is outside what I know,"* reasons out a candidate fix, tests it in a safe simulated copy of the network first, and only then applies it — learning the new disease for next time.

**The active pain point we solve (why now, why it matters):**
- Faults are **constant** in production — short-time cell outages hit every operator daily, mostly in high-load cells, often auto-recovering before anyone reacts (Ref E1). Known faults are frequent; that's the easy part.
- The costly, unsolved part is the **novel-fault tail**. Recent 5G/6G fault work states plainly that operators encounter "unlabeled anomalous sequences that fit no known category" and that **labeled fault data for novel modes is scarce or non-existent** (Ref M1, I1). Supervised healers cannot be trained on faults nobody has labeled yet.
- So the live pain point is: **when the rare new fault hits, today's automation either misacts or defers to a human — and in a millisecond RRC loop there is no human.** That is the gap this project targets.

---

## 3. Literature review — how much is already done

The field has solved three of the four sub-problems. The fourth — *safe recovery* from the unknown in the RRC loop — is open. Below, grouped by sub-problem, with what is done and what is missing.

### 3.1 Detecting / diagnosing the unknown — **largely done**
- **Hy-LIFT (MDPI Computers, 2025, open-access, read in full — Ref M1).** A hybrid rule-engine + semi-supervised classifier + **LLM augmentation engine** that produces "zero-shot hypotheses for novel faults" and surfaces "potential unknown/novel faults without altering classifier labels." Explicitly frames novel-fault handling as the hard problem and addresses **diagnosis and explanation** of it — *not closed-loop healing*. Reports per-class precision/recall ≈0.85–0.93. **This is the strongest evidence that detection/diagnosis of the unknown is done; healing is not.**
- **Simba — GNN + Transformer RCA (arXiv 2406.15638, read in full — Ref A1).** Spatio-temporal anomaly detection + root-cause analysis on 5G RAN using a calibrated Simu5G simulator. States labeled failure data is "uncommon." Detects and localises; **does not act/heal**.
- IDS-Agent / LogGPT / fine-tuned LLMs (cited within M1): improve **zero-day/unseen detection recall** (e.g. 0.61 vs ~0.45). Again detection, not recovery.

### 3.2 Self-healing of **known** faults — **done (classical + RL)**
- Classical **SON COD/COC** (cell-outage detection & compensation): heals known outage patterns with fixed policies.
- **RL/PPO handover & parameter agents** (IEEE VTC/GLOBECOM lines — Ref I2): optimise *how* to heal a **known** fault. Closed-world by construction.
- **Failure Management in 5G RAN: Challenges and Open Research Lines (Ref I3):** a survey that *itself lists* novel/unseen failure handling as an open research line — useful to cite as evidence the gap is acknowledged.

### 3.3 Zero-shot / open-world **healing** — **ALREADY PUBLISHED — this is the prior we must differentiate from, not claim over**
- **Bilen, *KDN-Driven Zero-Shot Learning for Intelligent Self-Healing in 6G Small Cell Networks*, Elsevier Ad Hoc Networks 178:103984, 2025 (full text read — Ref E2).** This is the decisive prior. It already does, in one closed loop: (i) **semantic zero-shot** detection of *new and previously unseen* anomalies **without retraining**; (ii) root-cause analysis via historical data + predefined rules; and (iii) closed-loop self-healing that embeds *both anomalies and healing actions* in a **shared semantic space** and selects a fix by semantic proximity — explicitly able to "**invent appropriate recovery strategies**" when no historical precedent exists.
  - **Consequence for us:** the *concept* "open-world/zero-shot closed-loop self-healing that synthesises recovery for unseen faults" is **no longer novel** — it is published as of July 2025. We must **not** claim it as a first.
  - **What Bilen does NOT do (our surviving, defensible deltas):**
    1. **Not O-RAN.** She uses a generic KDN (knowledge/control/data-plane) architecture. Ours is the standardized **Near-RT RIC / E2 / RRC-L3** loop.
    2. **No pre-commit verification.** She matches anomaly→healing by semantic proximity and **executes directly**. We insert a **digital-twin counterfactual veto** — simulate the candidate action, commit only if it beats the safe default. This safety gate is absent in her method.
    3. **Simulation-only.** She evaluates in a 6G mmWave (28 GHz) simulation, no hardware. Our **real-RU testbed with an injected fronthaul fault** is the empirical differentiator she lacks. (The survey I3 confirms "lack of real data" is an open problem — our RU directly answers it.)
    4. **No adversarial robustness.** She does not consider spoofed/malicious KPMs; our Topic-B governor does.
    5. **Fault design.** She uses generic threshold anomalies (latency/jitter/packet-loss/signal). We inject a **radio-healthy fronthaul fault** specifically constructed to defeat nearest-class/semantic matching — a harder OOD case.

### 3.4 Digital twin as a **safety verifier** — **enabler, under-exploited for healing**
- **Calibrated 5G simulators / twins (arXiv 2404.10643 — Ref A2; Simu5G in M1/A1):** used to *generate data*. Using the twin as a **load-bearing pre-commit action verifier** in the healing loop is the under-used angle we lean on.

### 3.5 The gap, stated precisely (revised after reading E2 in full)
> Detecting the unknown: done. Healing the known: done. **Open-world closed-loop healing of the unknown: now ALSO done in simulation (Bilen/KDN, E2).** What remains genuinely unaddressed is the **specific instantiation**: an **O-RAN-native (RIC/E2/RRC)**, **twin-verified** (action vetoed before it touches the live network), **hardware-validated** (real RU + injected OOD fault), and **adversarially-aware** open-world healer. Our claim is that *instantiation*, explicitly not the concept.

---

## 4. What exactly we are building (this is a new creation, not an add-on)

A closed control loop with four modules. The first three exist as torch-free surrogates in `src/openworld/`; the build turns them into a twin+RU pipeline.

```
Real RU  ─(E2/KPM)─►  KPM stream ──► calibrated Digital Twin (shadow)
      │
      ▼
  (1) COMPETENCE GATE  — "is this in-distribution or OOD?"
      │ in-distribution                 │ OOD (open-world path)
      ▼                                  ▼
  trained policy               (2) CANDIDATE SYNTHESISER
      │                          reason over KPM signature → propose fix
      └───────────┬──────────────────────┘
                  ▼
     (3) TWIN VERIFIER — simulate the proposed fix in the twin
                  │  beats safe-default ──► COMMIT to real RU
                  │  no better         ──► reject → safe-default / defer
                  ▼
        Action on RU  +  natural-language justification logged
                  ▼
     (4) DISTILLER — fold verified recovery back; deferral ↓ over time
```

1. **Competence gate** — OOD trigger from twin-disagreement + a novelty/visitation score. Decides whether to trust the trained policy or open the reasoning path.
2. **Candidate synthesiser** — for an OOD fault, propose an action by reasoning over the raw KPM signature (offline deterministic reasoner by default; Claude API drop-in), **not** by picking a nearest memorised label.
3. **Twin verifier** — the safety net and the element that earns the project title. The candidate fix is executed in the calibrated twin; commit to the real RU only if it beats the safe default.
4. **Distiller** — after a verified recovery, add the new class to the policy so uncertainty/deferral declines (open-world → closed-world for that class).

**The demonstrator fault (the "new" fault we inject):** fronthaul degradation via one command — `tc qdisc add dev <fh-iface> root netem delay 8ms 4ms loss 1%` on the O-DU↔O-RU link. Signature: throughput ↓ and latency ↑ while **RSRP/SINR/CQI stay healthy** — orthogonal to every radio fault the model knows, so it is genuinely OOD, and it requires a *different* heal (reconfigure numerology/MCS, throttle — a handover cannot fix it). Alternates if fronthaul access is hard: partial MIMO-branch failure; carrier-frequency/oscillator drift.

---

## 5. Methodology to build upon what exists

We do **not** reinvent detection or RL healing; we compose proven pieces and add the missing recovery+verification layer.

**Phase 0 — Baselines (reuse):** take an existing closed-world RL/PPO healer (§3.2) and an anomaly/OOD detector in the spirit of Hy-LIFT/Simba (§3.1). These are the "before."

**Phase 1 — Twin calibration:** calibrate the digital twin so its KPI distributions match a real trace. Use **VERGE OAI_RAN_KPM** (real OAI+FlexRIC KPMs) — split it: calibrate on VERGE-train, hold out VERGE-test the model never sees. Methodology follows calibrated-simulator practice (A2, Simu5G).

**Phase 2 — Open-world loop:** implement the four modules (§4) on top of the twin. Prove on synthetic held-out classes first (already: vanilla 100% harm → open-world 0% harm / 100% recovery, deferral declining).

**Phase 3 — Real-RU validation (the differentiator):** calibrate twin to the live RU → inject the fronthaul fault → agent flags OOD, synthesises fix, **verifies in twin**, commits to RU → measure real recovery. This is the evidence tier that no simulation-only prior (E2, M1, A1) provides.

**Phase 4 — Evaluation / ablations:** report recovery-success on held-out classes, **wrong-fix rate of baseline vs ours**, mean-time-to-recover on the RU, deferral decline after distillation, and an ablation removing the twin verifier (to show it is load-bearing, not decorative).

**Metrics table (target):**

| Metric | Baseline (closed-world) | Ours (open-world + twin) |
|---|---|---|
| Wrong-fix rate on unseen class ↓ | high (must pick a known label) | low |
| Recovery success on unseen class ↑ | low | high |
| Harmful action on unseen class ↓ | ~100% (synthetic) | ~0% (synthetic) |
| Mean time-to-recover on RU ↓ | — | measured |
| Deferral rate over episodes ↓ | n/a | declining |

---

## 6. Honest positioning & risk

- **Maturity:** the *concept* (open-world closed-loop healing) is **published** (Bilen/KDN, E2, 2025). We are an **instantiation/systems** contribution, not a conceptual first. Be explicit about this in the viva — it reads as rigor, not weakness.
- **The claim to make and defend:** *"the first **O-RAN-native, twin-verified, hardware-validated, attack-aware** open-world self-healer — recovering from a fault class held out of its training set, with every action vetoed in a digital twin before it touches a real RU."* Never *"we invented open-world healing."*
- **Biggest reviewer risk (now #1):** "Bilen 2025 already did zero-shot closed-loop self-healing." Pre-empt with the five-point delta in §3.3 — lead with **real-RU validation** and **twin pre-commit verification**, the two things she structurally lacks.
- **Second risk:** "your novel fault is just a held-out known fault." Agree openly; the value is *held-out-class recovery*, still real and useful.
- **Why it's still praiseworthy & debuggable:** on-title (twin is load-bearing), one-command fault injection, every stage inspectable (gate → synthesise → verify → commit), and validated on real hardware — which most cited work is not.

---

## 7. References

**Read in full (open-access):**
- **A1** Hasan et al., *Root Cause Analysis of Anomalies in 5G RAN Using GNN and Transformer (Simba)*, arXiv:2406.15638, 2024 — https://arxiv.org/abs/2406.15638
- **A2** *A Calibrated and Automated Simulator for Innovations in 5G*, arXiv:2404.10643 — https://arxiv.org/pdf/2404.10643
- **M1** *Hy-LIFT: Hybrid LLM-Integrated Fault Diagnosis Toolkit for 5G/6G Networks*, MDPI Computers 14(12):551, 2025 — https://www.mdpi.com/2073-431X/14/12/551

**Now read in full (PDFs in `papers/`):**
- **E1** *A Measurement Study of Short-Time Cell Outages in Mobile Cellular Networks*, Elsevier Computer Communications (S0140366415004661) — real STCO stats: outages up to 30 min/day, >98% uptime, mostly urban, high share auto-recover "faster than the operator becomes aware." Quantifies the pain point.
- **E2** Bilen, *KDN-Driven Zero-Shot Learning for Intelligent Self-Healing in 6G Small Cell Networks*, Elsevier **Ad Hoc Networks 178:103984, 2025** — **the decisive prior** (see §3.3). Simulation-only, generic KDN, no twin-verification, no adversarial handling.
- **I1/I3** *Failure Management in 5G RAN: Challenges and Open Research Lines* — confirms "lack of classified datasets" and "lack of real data" as open lines.
- **I5** *Conflict Mitigation Framework and Conflict Detection in O-RAN Near-RT RIC*, IEEE ComMag — Near-RT RIC conflict detection/resolution (baseline for multi-xApp coordination; cross-link to Topic B).
- **A3** *RANGAN: GAN-empowered Anomaly Detection in 5G Cloud RAN*, arXiv 2508.20985 — GAN+Transformer detection, F1 ~83% on contention (detection baseline).
