# Topic B — Adversarial-Aware, Twin-Verified Governor for RRC Self-Healing

*AI-Native Self-Healing O-RAN Network using a Digital Twin — the work already built.*
*Companion to Topic A. Written to be honest about where this stands and whether it is worth resolving.*

---

## 1. Problem statement

**In one sentence:**
> A self-healing agent trusts the KPM reports it receives. An attacker can **spoof** those reports (fake a signal collapse, fake congestion) and trick the healer into a harmful action — a needless handover that drops a live call, an idle transition that disrupts service. We ask: **can the self-healing loop tell a GENUINE fault from a SPOOFED KPM report, and refuse to "heal" an attack — without blunting real healing?**

**Plain-language version:**
The healer is a fixer who acts on alarms. A prankster can pull a fake fire alarm; a naive fixer evacuates the building every time. We add a governor that checks *"is this a real fire, or a pulled alarm?"* before acting — and can explain its reasoning for every decision.

**Where it sits:** Near-RT RIC xApp, **RRC layer (L3)** in O-CU-CP, E2 interface — same slot as the rest of the project. The threat surface is the **E2 / KPM reporting path** that RIC xApps trust.

---

## 2. What we built (current situation — this exists and runs)

A governance layer that sits **above** the RL healing agent. For every anomaly, before any RRC action, it decides: **cause** (benign / genuine-fault / adversarial), **whether the proposed action is safe**, and **why** (auditable one-sentence justification).

**Components (in `src/`, all working with torch-free surrogates):**

| File | Role |
|------|------|
| `adversarial_injector.py` | Injects 4 spoof types (RSRP collapse, neighbour spoof, fake congestion, gradient-evasion) with ground-truth cause labels |
| `fault_coupling.py` | Makes genuine faults physically coherent (coupled KPMs degrade together) so real faults separate from one-feature spoofs |
| `aml_guard.py` | Physical-invariant guard: rules that fire on spoof signatures but never on genuine-fault signatures (a real RLF collapses SINR/CQI too; a spoof leaves coupled KPMs inconsistent) |
| `twin_verifier.py` | Digital-twin counterfactual shield — overrides to safe default unless the twin says the action is genuinely better |
| `llm_governor.py` | The governor — offline deterministic reasoning by default; Claude API drop-in with the same prompt/JSON contract |
| `governed_healing_loop.py` / `governed_evaluation.py` | Integrated loop + security metrics + plots |

**Also productised** (`product/`): FastAPI `/decide` service with API-key auth, ~2,800 decisions/s, p95 ~0.5 ms, Dockerfile, tests passing, E2/KPM adapter stub.

---

## 3. Results (synthetic twin, like-for-like across configs)

| Metric | RL-only | Anomaly-Gated (original) | **Governed (ours)** |
|---|---:|---:|---:|
| Attack Success Rate ↓ | 65.2% | 57.3% | **0.0%** |
| False-Heal Rate ↓ | 9.9% | 5.2% | **0.0%** |
| Genuine-fault reward ↑ | −2.28 | −1.99 | **−1.61** |
| Cause-classification accuracy ↑ | — | — | **89.5%** |

Also validated the *same physical-consistency principle* on a **real** KPM trace (VERGE OAI/FlexRIC): detection recall 69%, precision 83%, FPR 2.3%, accuracy 94%.

**Reading it honestly:** the governor drives attack-success and false-heals to zero *while improving* healing on genuine faults — governance sharpens legitimate healing rather than blunting it. Explicit adversarial *labelling* is only ~52% because the layered design does not need to name every attack: physically-healthy spoofs are safely held as benign, so 100% are neutralised even though only half are explicitly labelled "adversarial." That is an honest detection-vs-neutralisation separation, not a hidden weakness.

---

## 4. Honest assessment — is it praiseworthy, debuggable, resolvable?

**Is it a real problem?** Yes. xApp/RIC security is genuine: spoofed measurement reports, rogue cells, and the E2 subscription attack surface are documented (e.g. IEEE EuroS&P 2025 on RIC E2 DoS; Rogue-Cell / MobiLLM lines). Trusting unauthenticated KPMs is a real weakness.

**Is it debuggable?** **Yes — this is its strongest quality.** Every decision is inspectable: you can see the anomaly score, the physical-invariant rule that fired, the twin's counterfactual reward, and a natural-language reason. You can inject a specific spoof and watch exactly why it was vetoed. It demos cleanly and fails legibly.

**Is it resolvable (can we actually finish it)?** **Yes — it is essentially already resolved at prototype level**, which is both good and bad:
- *Good:* it works end-to-end today, has real-data validation, and is productised. Low risk, strong demo, great interview/capstone centrepiece.
- *Bad for a "novelty" pitch:* the individual ingredients (RL healing, LSTM anomaly detection, twin verification, adversarial attacks on xApps) are all **published**, and adjacent combinations are patented (e.g. twin-based xApp conflict handling — COMIX / US 12,556,972; competence-signal patents US 11,320,827 / 11,307,594 / 12,302,162). The contribution is the **integration as a trust layer**, not any single component. That is defensible as a *system* paper, not as a fundamental world-first.

**Is it praiseworthy?** Yes, *scoped correctly*: "an adversarial-anomaly discriminator + twin-verified action shielding inside the O-RAN RRC self-healing loop, with an explainable governor." Suitable for **IEEE VTC / GLOBECOM–ICC workshops / NCC / ICMLCN**, and a strong B.Tech/M.Tech capstone. **Not** top-tier-journal novelty on the components.

---

## 5. Topic A vs Topic B — how they compare

| | **A — Open-world unseen-fault healing** | **B — Adversarial governor (this doc)** |
|---|---|---|
| Maturity | Emerging; more research novelty | Prototype-complete; more of an integration |
| Novelty | Higher (held-out-class recovery + real RU) | Lower (components published; combo is the delta) |
| Risk | Higher (needs RU, careful framing) | Lower (already works, demos cleanly) |
| Debuggability | Good (one-command fault injection) | **Excellent** (every decision explained) |
| Demo readiness today | Partial (synthetic proof; RU pending) | **Ready now** (service + metrics + real-data check) |
| Best framing | "Recovers from a fault it never trained on" | "Refuses to be tricked into a harmful heal" |

**They are complementary, not competing.** The cleanest thesis is: **Topic B is the safety/trust layer; Topic A is the capability layer.** The twin verifier is shared machinery. If the teacher wants a safe, demoable, finish-tonight story → lead with **B**. If they want research novelty and you have the RU → lead with **A** and keep **B** as the "and it's attack-safe too" section.

---

## 6. Honest bottom line

Topic B is the **lower-risk, higher-polish, more-debuggable** option and it is effectively done — its limitation is that it is an *integration* contribution, not a fundamental one, and parts of the neighbourhood are patented. Topic A is the **higher-novelty, higher-effort** option whose credibility now hinges on the **real RU**. Both are on-title and both use the digital twin as the load-bearing element. Recommended: present them as one system with two layers, and let the teacher pick which layer leads.

*(Source caveat: security/patent references gathered from abstracts, public patent text, and open-access search — not paywalled full text. Verify against IEEE Xplore / ScienceDirect and Google Patents before formal submission.)*
