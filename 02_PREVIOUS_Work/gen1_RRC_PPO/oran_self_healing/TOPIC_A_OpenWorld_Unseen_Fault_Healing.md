# Topic A — Open-World Self-Healing: Recovering from Faults the Model Was Never Trained On

*AI-Native Self-Healing O-RAN Network using a Digital Twin — candidate research direction*
*Working document. Written to be honest about what is novel, what is not, and what is provable.*

---

## 1. Problem statement (the most important part)

**In one sentence:**
> Every AI self-healing agent published today can only heal the fault classes it was trained on. When a *genuinely new* fault appears — one whose measurement signature does not match any known class — the agent either misclassifies it as the nearest known fault and applies the **wrong** fix, or fails silently. We ask: **can a self-healing loop, running on a digital twin plus a real Radio Unit, recover from a fault class it has never seen before, without a human retraining it first?**

**Plain-language version (for a layman / for slide 2):**
Think of the network's AI healer like a doctor who was trained on ten diseases. Show it an eleventh disease and it confidently prescribes the wrong medicine, because it *has* to pick one of its ten. In a live network a wrong fix is worse than no fix — a needless handover drops your call, a needless reconfiguration disrupts thousands of users. We want a healer that can say *"this is nothing I know — let me reason about it safely and try a fix I can verify in the twin before I touch the live network."*

**Why this is a real problem (not invented):**
- Operators see faults **constantly** — "short-time cell outages" affect every operator, mostly in high-load urban cells, often auto-recovering before anyone notices. (Ref R1, R2)
- The *hard tail* is **novel** faults. Recent 5G-RAN fault-diagnosis work explicitly reports "unlabeled anomalous sequences that experts said fit no known category — treated as potential novel faults." (Ref R7) The field openly lists **failure management in 5G RAN** as an *open research line*. (Ref R6)
- So known faults are frequent and easy to demo; **unseen** faults are rare, real, and currently handled poorly. That gap is the contribution.

**Where it sits in the architecture / OSI layer:**
- Runs as a **Near-RT RIC xApp** (10 ms–1 s control loop) acting on the **RRC layer (3GPP L3)** in the O-CU-CP, over the **E2** interface — the same slot as the rest of the project. For the manufactured fronthaul fault (see §5) the *cause* lives at the **fronthaul / lower-PHY (O-RU↔O-DU, eCPRI)** layer, which is what makes it "unseen" to a radio-KPM-trained model.

---

## 2. The precise scope of the novelty claim (read this before claiming anything)

Say exactly this and nothing more:

> **"We heal a fault class held out of the model's training set — the agent recovers using twin-verified reasoning instead of a memorised policy."**

**What is honestly novel:**
- Bringing **open-world / zero-shot recovery** *into the RRC self-healing loop* and *validating the recovery on a real RU*, with the **digital twin as the safe sandbox** where candidate fixes are tried before they touch the live network. The twin becomes load-bearing at decision time, not just a data generator — that directly earns the project title.

**What is NOT novel (state this openly so nobody catches you):**
- Novel-fault **detection** exists (open-set / zero-shot anomaly detection; Hy-LIFT; GNN+Transformer RCA — Ref R5). We are not claiming to invent detecting-the-unknown.
- Zero-shot self-healing has at least one close prior: **KDN-driven zero-shot self-healing for 6G small cells** (Elsevier, Ref R8). This is the nearest neighbour — cite it, and differentiate on (a) RRC/E2 loop, (b) twin-verified action shielding, (c) real-RU validation.
- The faults we inject are **novel to our model, not novel to the field** (fronthaul, MIMO, CFO impairments are all studied). The claim is *held-out-class recovery*, never "nobody has seen this fault."

**Honest maturity label:** this is an **emerging** problem, not a wide-open unsolved one. It is defensible as a strong B.Tech/M.Tech capstone and a workshop paper; it is *not* a clean "world-first."

---

## 3. Literature review (what exists, and the gap)

**Detection of the unknown (done):**
- **R5 — Root-Cause Analysis of Anomalies in 5G RAN using GNN + Transformer** (Simba), arXiv 2406.15638 — spatio-temporal anomaly detection + RCA. Detects/localises; does not *heal* an unseen class in the RRC loop.
- **R7 — Hybrid LLM-Assisted Fault Diagnosis for 5G/6G using Real-World Logs**, MDPI Computers 2025 — LLMs flag anomalies that "fit no known category." Diagnosis, not closed-loop recovery.

**Self-healing / SON (done for KNOWN faults):**
- **R3 — A Measurement Study of Short-Time Cell Outages**, Elsevier Computer Communications (S0140366415004661) — establishes that outages are frequent and often auto-recover. Motivation, not method.
- **R6 — Failure Management in 5G RAN: Challenges and Open Research Lines** — names novel/unseen failure handling as *open*.
- Classical COD/COC (cell-outage detection & compensation) heals *known* outage patterns with fixed policies.

**Zero-shot / open-world healing (the nearest prior — the thing to beat):**
- **R8 — KDN-driven zero-shot self-healing for 6G small cells**, Elsevier (S157087052500232X) — closest published idea. Differentiate hard: RRC/E2 near-RT loop + twin counterfactual verification + real-RU demo.

**Digital twin for RAN (enabler):**
- **R4 — A Calibrated and Automated Simulator for Innovations in 5G**, arXiv 2404.10643 — supports twin-calibration-against-real-data methodology (our validation plan, §6).

**The gap, stated precisely:**
> Detection of unknown faults is solved; healing *known* faults is solved; **twin-verified recovery from an unseen fault class inside the near-RT RRC loop, demonstrated on a real RU, is not an established, packaged result.** That is the slot we fill.

*(Access caveat: refs gathered from abstracts / open-access versions via public search, not paywalled IEEE Xplore / ScienceDirect full text. A proper thesis lit-review must pull the full texts from the college library.)*

---

## 4. The building idea (approach)

**Core loop:**
```
Real RU (or twin)  ──►  KPM stream
        │
        ▼
  Anomaly gate  ──► not anomalous ──► keep_connected (safe default)
        │ anomalous
        ▼
  Competence check:  "Does this match a fault class I know?"
        │                         │
   known class                unknown class  (open-world path)
        │                         │
        ▼                         ▼
  trained policy          LLM/reasoning synthesises a CANDIDATE fix
        │                         │
        └──────────┬──────────────┘
                   ▼
     DIGITAL-TWIN VERIFIER  (try the fix in the twin first)
                   │   fix helps ──► COMMIT to real RU
                   │   fix worse ──► reject, fall back to safe default / defer
                   ▼
        Action executed  +  natural-language justification logged
        +  outcome distilled back so the new class becomes "known" next time
```

**The four moving parts:**
1. **Competence gate** — decide *"is this in-distribution or out-of-distribution?"* (twin-disagreement + visitation/novelty score). This is the trigger for the open-world path.
2. **Candidate synthesiser** — for an unknown fault, propose a fix by reasoning over the KPM signature (offline deterministic reasoner by default; Claude API drop-in), *not* by picking a memorised label.
3. **Twin verifier** — the safety net. No unverified action reaches the live RU: the candidate fix is simulated in the calibrated twin; commit only if it beats the safe default.
4. **Distillation** — after a verified recovery, fold the new class into the policy so deferral/uncertainty drops over time (open-world → closed-world for that class).

**Prototype status (already have surrogate versions in `src/openworld/`):** vanilla agent = 100% harm on unseen faults; open-world loop = 0% harm / 100% recovery on the synthetic bench, with deferral declining across episodes. This is the *simulation* proof; the RU is what makes it real.

---

## 5. Manufacturing a "new" fault to inject into the RU

A fault is *novel to the model* when its KPM signature lands outside every trained class. The model learns **radio-power** faults (RLF = RSRP collapse; congestion = load + packet-loss; ping-pong). So the trick is a fault where **the radio looks healthy but service still breaks** — no known class fits.

**Injectable candidates (best first):**

| # | Fault | How to inject | Signature (why it's unseen) | Layer |
|---|-------|---------------|------------------------------|-------|
| 1 | **Fronthaul degradation** *(top pick)* | `tc qdisc add dev <fh-iface> root netem delay 8ms 4ms loss 1%` on the O-DU↔O-RU link | Throughput ↓, latency ↑, **RSRP/SINR/CQI stay healthy** — "good radio, bad service" | Fronthaul / eCPRI (O-RAN-specific) |
| 2 | **Partial MIMO branch failure** | Disable one TX chain / antenna port in RU config | Rank + throughput ~halve, **RSRP barely moves** | Lower-PHY |
| 3 | **Oscillator / carrier-frequency drift** | Inject small CFO / ppm clock error on SDR RU | **BLER + retransmissions rise, RSRP nominal** | PHY / RF |

**Why #1 is the strongest:** the fronthaul split *is* what makes O-RAN distinctive, so a fronthaul fault is squarely on-topic; it is pure-software to inject (one `netem` command, no hardware mod); its signature is genuinely orthogonal to every radio fault the model knows; and it needs a **different heal** (reconfigure numerology/MCS or throttle — a handover won't fix it), which is exactly what tests open-world reasoning rather than memorised policy.

**Honest framing for the viva:** "We injected a fronthaul-induced degradation the agent had never trained on. A standard agent misread it as an RLF and triggered a useless handover; our open-world loop recognised it as out-of-distribution, synthesised a candidate reconfiguration, verified it in the twin, and only then applied it to the RU — recovering service." That sentence is defensible end-to-end.

---

## 6. How we validate it honestly (the realism problem, solved by the RU)

The RU is what fixes every "it's only synthetic" criticism. Three tiers of evidence:

1. **Simulation (have it):** twin-only bench — vanilla 100% harm vs open-world 0% harm / 100% recovery on held-out fault classes.
2. **Real KPM data (have a dataset):** VERGE **OAI_RAN_KPM** (real OpenAirInterface + FlexRIC trace). Split it — calibrate the twin so its KPI distributions match VERGE-train; test detection/recovery on held-out VERGE-test the model never saw.
3. **Real RU testbed (the gold standard — what unlocks this topic):** calibrate the twin to the RU's live KPMs → inject the manufactured fault (§5) on the RU → agent detects OOD, synthesises fix, **verifies in twin**, commits to RU → measure real recovery time / throughput restored. Plan in the twin, act on the real thing — the literal definition of a digital twin.

**Metrics:** recovery success rate on held-out classes, wrong-fix rate of the baseline vs ours, mean time-to-recover on the RU, and deferral rate declining as classes are distilled in.

---

## 7. Honest bottom line

- **Praiseworthy?** Yes, *if scoped as stated* — twin-verified recovery from a held-out fault class, proven on a real RU, is a strong, on-title capstone/workshop contribution.
- **Debuggable?** Yes — the manufactured fronthaul fault is one command to inject and one loop to observe; failures are inspectable at every stage (gate → synthesise → verify → commit).
- **Unsolved?** *Emerging*, not wide-open. Detection of the unknown is done; the nearest healing prior is KDN-ZSL (R8). Our delta is the RRC/E2 loop + twin verification + real-RU proof. Never oversell it as a world-first.
- **Biggest risk:** a reviewer says "your 'novel' fault is just a held-out known fault." Pre-empt it: agree openly, and pitch the claim as *held-out-class recovery*, which is the correct and still-valuable framing.

---

## References (abstract-level; pull full text from library)

- **R1** Asentria — *Mobile Network Failures: Causes* — https://www.asentria.com/mobile-network-failures-causes/
- **R2 / R3** *A Measurement Study of Short-Time Cell Outages in Mobile Cellular Networks* — Elsevier Computer Communications — https://www.sciencedirect.com/science/article/abs/pii/S0140366415004661
- **R4** *A Calibrated and Automated Simulator for Innovations in 5G* — arXiv 2404.10643 — https://arxiv.org/pdf/2404.10643
- **R5** *Root Cause Analysis of Anomalies in 5G RAN using GNN + Transformer (Simba)* — arXiv 2406.15638 — https://arxiv.org/pdf/2406.15638
- **R6** *Failure Management in 5G RAN: Challenges and Open Research Lines* — ResearchGate 367384546
- **R7** *Hybrid LLM-Assisted Fault Diagnosis Framework for 5G/6G Networks Using Real-World Logs* — MDPI Computers 14(12):551, 2025 — https://www.mdpi.com/2073-431X/14/12/551
- **R8** *KDN-driven zero-shot self-healing for 6G small cells* — Elsevier — https://www.sciencedirect.com/science/article/pii/S157087052500232X
