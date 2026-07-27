# Novelty Assessment — honest, cited, defensible (read before presenting)

**Purpose:** so you can defend the novelty to an expert (e.g., a Samsung
researcher) without overclaiming. The golden rule: **cite the neighbours
yourself, then state the precise gap.** Confidence comes from knowing the
landscape, not from claiming to be first at everything.

---

## 1. What ALREADY EXISTS (do not claim these as ours)

| # | Prior art | What it does | Why it's NOT us |
|---|-----------|--------------|-----------------|
| 1 | **MobiLLM** (arXiv 2509.21634, Sep 2025) | Agentic **LLM** framework for **closed-loop threat mitigation** in 6G O-RAN; agents analyse → classify (RAG over MITRE FiGHT/3GPP) → respond | Runs at the **SMO/orchestration** layer (O1/A1, slow loop). Maps *threats → countermeasures*. Does **not** govern an RL healing agent, **not** fault-vs-spoof KPM discrimination, **not** digital-twin RRC action verification |
| 2 | **Robust Anomaly Detection in O-RAN: LLMs vs Data Manipulation** (arXiv 2508.08029, Aug 2025) | Uses an **LLM as a detector** robust to Unicode ("hypoglyph") message tampering on the SDL | Detection only (Normal/Anomalous). **No** RL, **no** control loop, **no** fault-vs-attack cause, **no** action veto, **no** twin |
| 3 | **Rogue Cell** (arXiv 2505.01816) / **APATE** | Malicious cell **spoofs KPIs** to fool the **traffic-steering** xApp; plus a defense | Targets the steering decision, not an **RRC self-healing** RL loop; no genuine-fault-vs-spoof classifier; no twin verification |
| 4 | **Adversarial attacks on ML xApps** (arXiv 2309.03844); **System-level analysis** (2402.06846) | FGSM/PGD evasion on xApp classifiers; catalog of O-RAN AML attacks/defenses | Attack/analysis side; not a self-healing governor |
| 5 | **Multi-Layer Defence Framework for Near-RT O-RAN** (RG 399394328) | Detection components + policy-driven mitigation in near-RT RIC | Policy/rule mitigation, not RL-action governance with fault-vs-spoof reasoning + twin |
| 6 | **Safe-RL shields / twin action verification** (FOGNITE; DTCF arXiv 2604.01325; "safety shield vetoes low-confidence actions") | Digital twin validates an RL action *before* execution; shields veto unsafe actions | Applied to **performance/safety** constraints — **not** to "is this anomaly a fault or an attack" |
| 7 | **LLM-augmented RL in O-RAN** (ORAN-GUIDE, arXiv 2506.00576) | RAG prompt-learning to help an RL agent in O-RAN **slicing** | Slicing/throughput, not security, not self-healing, not spoof discrimination |
| 8 | **Physical-consistency spoof detection** (PhyScout, CCS'24; CPS cross-feature checks) | Detect sensor spoofing via spatio-temporal/physical consistency | General CPS/sensors; the *principle* we use for the guard is known — we apply it to O-RAN KPMs |

**Takeaway:** RL healing, anomaly detection, xApp attacks & defenses, LLM security
agents, twin action-verification, and physical-consistency spoof detection are
**all published**. Several are 2025 and adjacent. Do **not** claim to invent any.

---

## 2. What is genuinely OUR delta (defensible)

Our contribution is an **integration + one under-addressed decision**, stated precisely:

> **Inside the near-RT RRC self-healing control loop, we classify whether an
> anomaly is a GENUINE fault (to heal) or an ADVERSARIALLY SPOOFED KPM (to veto),
> using physical KPM-consistency, and we gate the RL healing agent's action with a
> digital-twin counterfactual check — producing a human-readable reason per action.**

No single prior work does this *combination in this place*:
- MobiLLM = LLM security agents, but SMO layer, threat→countermeasure, no RL-healing governance, no fault-vs-spoof, no twin gate.
- 2508.08029 = LLM detection robustness, no control/RL/twin.
- Rogue Cell = attack+defense on steering, not self-healing governance.
- Safe-RL/twin shields = verify actions for performance, not for fault-vs-attack.

So the novelty is **systems/integration**, not a new algorithm. That is honest and
still valuable at project / workshop level.

---

## 3. How to SAY it (exact lines)

- **Opening (honest & strong):** "We're not claiming to invent O-RAN security or
  RL healing — both exist. Our contribution is putting a **trust decision inside
  the self-healing loop**: telling a real fault from a spoofed KPM before the RL
  agent acts, and double-checking the action on a digital twin."
- **If they name MobiLLM:** "Yes — MobiLLM is the closest. It's an LLM security
  agent at the SMO/orchestration layer that maps threats to countermeasures. We
  operate one layer down, in the near-RT RRC loop, and our job is different: we
  *govern the RL healing action itself* and specifically separate genuine faults
  from spoofed KPMs. Complementary, not the same."
- **If they say 'this is just integration':** "Agreed — it's a systems
  contribution. The novelty is the specific decision (fault-vs-spoof for
  self-healing) and the layered shield (physics guard + twin verifier) that, to
  our knowledge, hasn't been assembled in the RRC self-healing loop before."
- **If pushed on rigor:** "Our evaluation is on a digital twin plus one real
  O-RAN KPM trace; scaling to large real datasets and a live RIC testbed is our
  stated next step." (Point to the status slide.)

## 4. What would make it STRONGER (say this as future work)
- Reproduce on a large real multi-cell dataset (Colosseum / OpenRAN-Gym).
- Compare directly against MobiLLM-style mitigation and a Rogue-Cell defense.
- Adaptive attacker that tries to fake *all* coupled KPMs (raises attacker cost).
- Formal guarantee from the twin shield (not just empirical).

## 5. Honest confidence statement
This search was targeted, not exhaustive — paywalled/most-recent IEEE venues may
hold closer work. So the correct claim is **"to our knowledge / to the best of our
literature review,"** never "we are the first." That phrasing is standard and
protects you.
