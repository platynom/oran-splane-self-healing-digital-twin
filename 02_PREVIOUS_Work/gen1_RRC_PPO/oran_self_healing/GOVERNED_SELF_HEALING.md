# Adversarial-Aware, Digital-Twin-Verified LLM Governor for O-RAN RRC Self-Healing

This extends the existing *AI-Native Self-Healing O-RAN Network using a Digital Twin*
project with a defensible research contribution: a governance layer that makes the
self-healing loop **trustworthy under attack**, not just performant.

---

## 1. The novelty in one sentence

> Prior work optimises *how* to heal an RRC fault (RL/PPO handover agents, LSTM
> anomaly gates). We add the missing question — *can the healing loop still be
> trusted when the anomaly itself is a spoofed KPM attack?* — and answer it with an
> **LLM safety governor** that classifies each anomaly as **benign / genuine-fault /
> adversarial**, and a **digital-twin counterfactual verifier** that shields every
> committed action.

Every individual ingredient (PPO handover, LSTM-AE anomaly detection, digital twins,
adversarial attacks on xApps) already exists in the literature. What is **not**
published is the *combination as a trust layer*: an adversarial-anomaly discriminator
plus twin-in-the-loop verification sitting above the RL healer in the O-RAN RRC loop.
This is the delta that makes the work conference-grade rather than a re-implementation.

---

## 2. Why it fits the project title

| Title term | Before | After this work |
|---|---|---|
| **AI-Native** | one AI (PPO) | multi-AI: PPO healer + reasoning **LLM governor** |
| **Self-Healing** | heals real faults | heals faults **and** neutralises attacks that fake faults |
| **Digital Twin** | data generator only | **load-bearing at decision time** (counterfactual verification) |

The title is justified *more* strongly than before — no rename needed.

---

## 3. Architecture (closed loop)

```
KPM stream (digital twin)
      │
      ▼
LSTM / anomaly gate ──► not anomalous ──► keep_connected (safe default)
      │ anomalous
      ▼
AML guard  (physical-invariant consistency check)
      │  {benign? fault? spoof?} evidence
      ▼
LLM GOVERNOR  ── fuses: anomaly score + AML report + twin forecast
      │            ├─ cause = adversarial → VETO, hold connection
      │            ├─ snapshot healthy    → false alarm → hold
      │            └─ cause = genuine_fault
      ▼
Digital-Twin VERIFIER  (counterfactual: proposed action vs safe default)
      │            ├─ proposed action worse → OVERRIDE to safe default
      │            └─ proposed action better → COMMIT the heal
      ▼
RRC action executed  +  auditable natural-language justification logged
```

### New modules (`src/`)
| File | Role |
|---|---|
| `adversarial_injector.py` | Injects spoofed/poisoned KPM attacks (4 attack types) with ground-truth cause labels |
| `fault_coupling.py` | Makes genuine faults physically coherent (coupled KPMs degrade together) so faults are separable from one-feature spoofs |
| `aml_guard.py` | Adversarial-ML guard: physical-invariant rules that fire on spoof signatures but never on genuine-fault signatures |
| `twin_verifier.py` | Digital-twin counterfactual shield (post-decision) — the twin becomes load-bearing |
| `llm_governor.py` | The governor. **Offline** deterministic reasoning by default; **Claude API** drop-in (`backend="claude"`) with the same prompt/JSON contract |
| `governed_healing_loop.py` | Integrated loop, 3 comparable modes |
| `governed_evaluation.py` | Security metrics + plots |
| `real_kpm_validation.py` | Validation on a **real** OAI/FlexRIC KPM trace |
| `lite_components.py` | Torch-free surrogates for the LSTM gate + PPO so the harness runs anywhere |
| `main_governed.py` | Orchestrates the full experiment |

---

## 4. Results (synthetic twin, 9,000 KPM steps, identical data across configs)

Three configurations compared like-for-like:
**RL-only** (no gate) · **Anomaly-Gated** (the original system) · **Governed** (ours).

| Metric | RL-only | Anomaly-Gated (original) | **Governed (ours)** |
|---|---:|---:|---:|
| Attack Success Rate ↓ | 65.2% | 57.3% | **0.0%** |
| Attack Neutralised ↑ | 34.8% | 42.7% | **100.0%** |
| False-Heal Rate ↓ | 9.9% | 5.2% | **0.0%** |
| Genuine-fault reward ↑ | −2.28 | −1.99 | **−1.61** |
| Mean reward ↑ | 0.58 | 0.68 | **0.76** |
| Cause-classification accuracy ↑ | — | — | **89.5%** |
| Explicit adversarial recall | — | — | 52.2% |

**Reading the numbers.** The governor drives attack success from ~65% to **0%** and
false-heals from ~10% to **0%**, while *improving* healing quality on genuine faults
(reward −2.28 → −1.61) — i.e. governance does not blunt legitimate self-healing, it
sharpens it. Explicit adversarial *labelling* is 52% because the layered design does
not need to label every attack as "adversarial": attacks with a physically-healthy
snapshot are safely held as benign, so **100% of attacks are neutralised** even though
only ~half are named as attacks. This is an honest, defensible separation of
*detection* from *neutralisation*.

### Example governor decisions (auditable reasoning)

| Scenario | RL proposed | Governor verdict | Reason (abridged) |
|---|---|---|---|
| Spoofed RSRP collapse | trigger_handover | **VETO → keep** | "RSRP in outage but SINR/CQI excellent — physically impossible; spoof, not fault." |
| Neighbour spoof | keep_connected | hold (benign) | "Alarm raised but snapshot physically healthy; false alarm." |
| Fake congestion | idle_transition | **VETO → keep** | "Heavy load + high latency but no packet loss — fake congestion." |
| Genuine RLF | trigger_handover | **COMMIT** | "Fault confirmed (KPMs consistently degraded); twin supports handover (−6.05 vs hold −10.0)." |
| Genuine congestion | adjust_report_interval | **COMMIT** | "Fault confirmed; twin supports reconfig (−1.79 vs hold −2.29)." |

---

## 5. Real-data validation (OAI / FlexRIC KPM trace)

Dataset: **VERGE-PROJECT/OAI_RAN_KPM_dataset** — RAN KPMs captured on a bare-metal
OpenAirInterface + FlexRIC + KPM-xApp testbed. We show the *same physical-consistency
principle* separates spoofed from genuine reports on **real** KPMs (native couplings:
throughput ↔ traffic-volume ↔ PRB ↔ RLC-delay):

| Detection recall | Precision | False-positive rate | Accuracy |
|---:|---:|---:|---:|
| 69.4% | 82.7% | 2.3% | **93.9%** |

---

## 6. How to run

```bash
cd oran_self_healing
python main_governed.py          # full experiment + plots + real-data validation
```

Outputs: `outputs/governed_evaluation.png`, `outputs/governed_results.json`,
`outputs/governor_examples.json`, `data/rrc_dataset_adversarial.csv`.

The harness auto-uses your real **LSTM-AE** gate and **PPO** agent when PyTorch /
Stable-Baselines3 are installed, and transparently falls back to lightweight
surrogates otherwise (the governance layer is identical either way).

### Enabling the real Claude API governor
The governor ships with an offline reasoning engine and a drop-in Claude backend that
uses the *same* structured prompt and JSON contract:

```python
export ANTHROPIC_API_KEY=sk-...
# in main_governed.py:
governor = LLMGovernor(backend="claude")   # instead of backend="offline"
```

---

## 7. Honest positioning

- **Not** top-tier-journal novelty on the components — those are public.
- **Is** a genuine, defensible contribution as a *system*: adversarial-anomaly
  discrimination + twin-verified action shielding in the O-RAN RRC self-healing loop,
  with an explainable governor. Suitable for **IEEE VTC / GLOBECOM–ICC workshops / NCC /
  ICMLCN**, and a strong B.Tech/M.Tech capstone or interview centrepiece.
- **Strongest next step** for publishability: replace the surrogate gate/agent with the
  trained LSTM-AE + PPO, add a rule-based SON baseline, and report the same security
  metrics against a stronger adversary.
