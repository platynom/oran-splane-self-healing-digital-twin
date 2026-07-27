% Final Project Direction — for Review
% Parent project: AI-Native Self-Healing O-RAN Network using a Digital Twin
% Prepared by: Tanmay

# Purpose of this document

This document compares two topics only: (1) the **original topic** already present in the project, with a paper-by-paper literature survey and the reason the literature made us drop it; and (2) the **finally chosen topic**, with its problem statement, our solution, and a paper-by-paper literature survey grouped by IEEE / ScienceDirect / open-source. For every paper we give its **context** — what that paper actually contributes and how it relates to our work — not just a citation.

---

# PART 1 — The ORIGINAL topic (already in the project) — and why we did NOT take it

## Title (as originally built)
**Reinforcement-Learning-Based RRC Self-Healing Agent Trained on a Digital Twin of the O-RAN Network.**

## Problem statement (original)
In a 5G / O-RAN network, devices constantly hit radio failures — radio-link failures (RLF), ping-pong handovers, and congestion. Can an **AI agent, trained by reinforcement learning (RL/PPO) on a digital twin of the network**, autonomously choose the right **RRC action** (handover, threshold change, report-interval change, idle transition, keep-connected) at the right moment to reduce failures **better than a non-intelligent baseline**? This is what the project originally implemented: a PPO agent plus an LSTM anomaly gate, trained and evaluated on a simulated (digital-twin) KPM stream.

## Literature survey — paper by paper (what each provides, and why it closes the door)

### IEEE

**ColO-RAN — "Developing ML-based xApps for O-RAN closed-loop control on programmable experimental platforms," IEEE Transactions on Mobile Computing.**
*What it provides:* a large-scale framework for building RL-based xApps that perform closed-loop RAN control (scheduling, slicing) on the Colosseum + srsRAN testbed, plus large-scale data collection.
*Relation to the original topic:* this is essentially the original topic already done — RL controlling the RAN through xApps — and published in an IEEE **journal**. It shows the idea is mature, not open.

**REAL — "RL-Enabled xApps for Experimental Closed-Loop Optimization in O-RAN with OSC RIC and srsRAN," 2025.**
*What it provides:* an experimental demonstration of RL xApps doing closed-loop optimisation on a real O-RAN stack (OSC RIC + srsRAN).
*Relation:* confirms RL closed-loop self-optimisation on a real stack is already demonstrated — again, the original topic.

**Conflict Mitigation Framework in O-RAN Near-RT RIC, IEEE Communications Magazine (doc 10121578).**
*What it provides:* a framework inside the Near-RT RIC to detect and resolve conflicts between the decisions of multiple xApps.
*Relation:* shows the ecosystem around RL healing agents (multi-xApp coordination, safety) is already standardised-in-spirit — the surrounding problems are also being solved.

**IEEE VTC / GLOBECOM RL-handover and self-optimisation line.**
*What it provides:* repeated conference results applying RL to handover and RRC-parameter self-optimisation.
*Relation:* the specific actions in our original agent (handover, threshold change) are exactly what these papers already optimise with RL.

### ScienceDirect (Elsevier)

**Bilen, "KDN-Driven Zero-Shot Learning for Intelligent Self-Healing in 6G Small Cell Networks," Ad Hoc Networks 178:103984, 2025.**
*What it provides:* a self-healing framework that not only heals known faults but uses semantic **zero-shot learning** to detect and heal **previously unseen** anomalies in a closed loop, "inventing" recovery strategies.
*Relation:* the frontier has already moved **past** plain RL self-healing to unseen-fault healing — so the original topic is not even the current state of the art.

**"A Measurement Study of Short-Time Cell Outages in Mobile Cellular Networks," Computer Communications.**
*What it provides:* a real-operator measurement study showing short-time cell outages occur up to ~30 min/day, mostly in urban high-load cells, and a high share auto-recover before the operator notices.
*Relation:* motivation only — it proves faults are real and frequent, but it does not make our RL re-implementation novel.

### Open-source / open-access

**Simba — "Root Cause Analysis of Anomalies in 5G RAN using GNN + Transformer," arXiv 2406.15638.**
*What it provides:* a state-of-the-art anomaly-detection + root-cause-analysis model using graph neural networks and transformers on a calibrated Simu5G simulator; explicitly notes "labelled data for failure scenarios is uncommon."
*Relation:* its detector already surpasses the LSTM gate in the original design — the anomaly-detection half of the original topic is outclassed.

**Calibrated 5G simulator, arXiv 2404.10643; Colosseum: The Open RAN Digital Twin, arXiv 2404.17317.**
*What they provide:* calibrated simulators / emulators used to train and evaluate RAN agents.
*Relation:* using a digital twin as a training/evaluation environment (the "Digital Twin" part of the original topic) is standard practice, not a contribution.

## What the survey concludes (original topic)
Every component is already published and mature: RL/PPO control of RRC actions (ColO-RAN in an IEEE Transactions; REAL; VTC/GLOBECOM), anomaly detection (Simba surpasses LSTM), and the digital twin as a training environment (Colosseum, calibrated simulators). Newer work (Bilen 2025) has already advanced beyond it.

## Why we did NOT take the original topic
Across these papers the original topic is **fully saturated** — it would be a **re-implementation**, not a contribution: no new problem, no new method (PPO + LSTM + twin is the standard recipe), and the same weak simulator-only validation everyone has already improved on. It therefore cannot be published as novel work. We drop it not because the idea is bad, but because the literature has already done it.

---

# PART 2 — The FINALLY CHOSEN topic (what we are developing)

## Title
**Experimental Validation and Benchmarking of AI-Native Self-Healing in O-RAN: A Real-KPM Fault-Injection Dataset and Digital-Twin-Verified Healing Loop.**

## Problem statement
Published AI self-healing methods for O-RAN are almost entirely validated in **pure numerical simulators**, and the literature *explicitly and repeatedly* reports a **lack of real, labeled fault data** and a **lack of experimental testbed validation**. Consequently it is **unknown how a digital-twin-verified self-healing loop actually behaves on a real O-RAN protocol stack** under realistic, reproducible faults. We address this exact gap: build the loop on a real O-RAN stack with real KPMs and injected faults, benchmark it, and **release the labeled fault dataset the community is missing**.

## Our solution (what we build and deliver)
1. **A real O-RAN self-healing testbed** — srsRAN (5G gNB + UE) + FlexRIC (Near-RT RIC) + a KPM xApp over the E2 interface; first on a laptop (software radio), then re-run unchanged on **Colosseum** (real SDR radios, emulated channel) for the hardware tier.
2. **A labeled fault-injection dataset** — real KPM recordings of the network healthy and under injected faults (fronthaul degradation, congestion, interference), auto-labeled by injection timestamps. *This dataset is the primary novel deliverable.*
3. **A digital-twin-verified healing loop** — our existing governed loop (anomaly detection → twin counterfactual verification → RRC action) run on held-out real data as the baseline **benchmark**.
4. **A reproducibility bundle** — injection scripts + xApp config + dataset + baseline code, one-command runnable.

*Contribution type (honest):* integration + **experimental validation** + **dataset/benchmark** — not a new algorithm and not a new fundamental problem. This is the category IEEE conferences/workshops publish.

## Literature survey — paper by paper (what each provides, and how it supports this topic)

### IEEE

**ColO-RAN, IEEE Transactions on Mobile Computing.**
*Context here:* proves experimental O-RAN work on an **emulated-channel testbed** (Colosseum + srsRAN) reaches an IEEE **journal** — direct evidence our contribution *type* is IEEE-publishable, and the closest structural template for our paper.

**REAL, 2025 (OSC RIC + srsRAN).**
*Context here:* a worked example of an **experimental** O-RAN paper (real stack, closed loop) — a second template for structuring results and validation.

**Experimental xApp Conflict-Mitigation testbed (OTIC), 2025.**
*Context here:* shows that **experimental-validation** papers (deploying on a real testbed and measuring) are actively accepted in the O-RAN community.

**IEEE GLOBECOM 2025 Open RAN Summit / track.**
*Context here:* a concrete, current **venue** for exactly this experimental O-RAN work.

**Conflict Mitigation Framework, IEEE Communications Magazine (doc 10121578).**
*Context here:* read in full; provides the Near-RT RIC control/safety context our healing loop operates within (how xApp decisions are governed).

### ScienceDirect (Elsevier)

**Bilen, Ad Hoc Networks 178:103984, 2025.**
*Context here:* read in full; establishes that the **methods** (zero-shot, closed-loop healing) are already saturated — which is precisely why we pivot from "new method" to "real validation + dataset." Also our nearest prior to differentiate from.

**"A Measurement Study of Short-Time Cell Outages," Computer Communications.**
*Context here:* read in full; quantifies real fault frequency/behaviour, grounding the realism and the choice of injected faults in our dataset.

### Open-source / open-access

**Simba, arXiv 2406.15638.**
*Context here:* read in full; explicitly states "labelled failure data is uncommon" — a peer-reviewed statement of the **data gap** we fill.

**Hy-LIFT, MDPI Computers 14(12):551, 2025.**
*Context here:* read in full; a hybrid rule + semi-supervised + LLM fault-diagnosis toolkit that names **label scarcity** and that "novel modes lack examples" — a second independent statement of the data gap, and evidence that zero-shot *diagnosis* is done (so our value is data + validation, not diagnosis).

**Failure Management in 5G RAN — Challenges and Open Research Lines (survey).**
*Context here:* read in full; lists "lack of classified datasets" and "lack of real data" as **open research lines** — the third independent source confirming the gap.

**Colosseum: The Open RAN Digital Twin, arXiv 2404.17317.**
*Context here:* read in full; describes the free, academically-accessible large-scale emulator (real USRP SDRs + hardware channel emulator) that is our **real-radio validation tier**.

**How to Bridge the Sim-to-Real Gap in DT-Aided Telecom Networks, arXiv 2507.07067, 2025.**
*Context here:* read in full; shows sim-to-real / real-data is a live 2025 concern and that twin-trust weighting is already studied — supporting our focus on *real* data rather than another twin-trust method.

**RANGAN, arXiv 2508.20985.**
*Context here:* a GAN + Transformer anomaly detector (F1 ~83% on contention) — a **baseline detector** we can benchmark against on our dataset.

## What the survey concludes (chosen topic)
Three independent peer-reviewed sources (Simba, Hy-LIFT, the Failure-Management survey) state the bottleneck is **real, labeled fault data and experimental validation**, not another algorithm. IEEE itself publishes experimental O-RAN testbed work (ColO-RAN in a Transactions; GLOBECOM Open-RAN track). Therefore this topic is both **genuinely needed** (documented gap) and **IEEE-publishable** (demonstrated venue history) — while the original RL topic is neither.

## Realistic target venues
IEEE GLOBECOM / ICC / WCNC / VTC (main or workshop), IEEE Access, IEEE Networking Letters, possibly IEEE Communications Magazine. (Honest note: a top-tier Transactions would need deeper results; a conference/workshop plus a public dataset is the realistic first target.)

---

# One-line contrast for the reviewer

| Aspect | Original topic (RL RRC self-healing on a twin) | Chosen topic (real-testbed validation + dataset) |
|---|---|---|
| New problem? | No | No (stated honestly) |
| New method? | No — PPO + LSTM + twin is standard | No — integration of known methods |
| New contribution? | None — re-implementation | Yes — real labeled dataset + experimental benchmark |
| Gap in literature? | Already solved and surpassed | Explicitly named open (Simba, Hy-LIFT, survey) |
| IEEE-publishable? | Only as a weak re-run | Yes — proven category (ColO-RAN, GLOBECOM) |

*Source-access note: items marked "read in full" are the PDFs placed in the project `papers/` folder plus open-access sources. IEEE Xplore / ScienceDirect full texts open only via the campus login, not from the assistant's side.*
