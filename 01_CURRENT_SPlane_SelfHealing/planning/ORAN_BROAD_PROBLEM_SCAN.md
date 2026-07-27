# O-RAN Broad Problem Scan — every layer, looking for a real, novel, hard problem

*Goal: look beyond the RIC across the whole O-RAN stack (O-RU, Open Fronthaul, O-DU, O-CU, interfaces, SMO), find a real/novel/hard problem, and check whether it correlates with what we've already built (physical-consistency discrimination + digital-twin-verified governed self-healing).*

---

## Layer-by-layer findings (ranked within each)

### O-RU / Open Fronthaul — **the hot zone** ★★★ (recommended)
- **S-plane timing security is wide open.** A PTP (IEEE 1588) **spoofing attack crashes a production O-RAN 5G base station within ~2 seconds** and needs manual recovery. Timing error budget is **< 100 ns** — brutally tight. The O-RAN Alliance itself states **no comprehensive fronthaul security standard exists yet**.
- **State of the art = TIMESAFE** (ACM Transactions on Privacy & Security, 2025 — *peer-reviewed*): a **passive ML detector** for PTP attacks, 97.5% accuracy, runs on the O-DU / mirror port.
- **The gap TIMESAFE leaves open (its own limitation):** it **detects**, it does not **recover**, and it does **not separate a malicious timing attack from a benign timing fault** (GNSS holdover loss, packet-delay-variation, SyncE degradation) — both look like "sync is drifting." Config alone can't fix it; the open challenge is security **without** hurting performance.

### O-DU / MAC-PHY — real-time control frontier ★★
- **dApps** (sub-ms apps at the O-DU with IQ/PHY access) are brand new; the architecture is "still lacking." Real-time scheduler + CPU orchestration under strict latency is unsolved — but it's **infrastructure-heavy** and doesn't reuse our asset.

### Interfaces / Security (WG11) ★★
- Fronthaul **C/U-plane DoS**, M-plane MITM, **Zero-Trust for the O-RAN data plane** (Nov 2025) are active. Broad, less specific than the S-plane timing problem.

### Non-RT RIC / SMO / Digital Twin ★
- **Sim-to-real / DT fidelity** is an open problem (O-RAN nGRG has a DT study group). This is a *supporting* problem for us (our twin verifier needs it), not a headline.

### Near-RT RIC / xApp (where we already are) ★
- KPM poisoning, conflict mitigation, anomaly detection — real but **crowded**, and exactly the space we already concluded is saturated.

---

## The recommendation: move the SAME method down to the Fronthaul S-plane

**Problem statement (broader, harder, more novel than the RIC version):**
> On the O-RAN Open Fronthaul, discriminate a **malicious PTP/timing-spoofing attack (H₁)** from a **benign timing fault (H₀)** — GNSS holdover, packet-delay-variation, SyncE degradation — using the physical consistency of synchronization telemetry (PTP offset/path-delay, PDV, SyncE ESMC quality), and trigger a **digital-twin-verified self-healing action** (sync-source failover LLS-C1→C4/GNSS, holdover, or isolate) **before the ~2-second catastrophic base-station failure**.

**Why this is the one to pick:**
- **Broader than the RIC** — it lives at the O-RU / O-DU / fronthaul, exactly the "look wider" the project needed.
- **Harder + higher-stakes** — sub-100 ns budget, 2-second catastrophic failure, no security standard exists. This is not a toy.
- **More novel** — fronthaul security is explicitly unstandardized; the SOTA (TIMESAFE) stops at detection and does not do fault-vs-attack discrimination or self-healing.
- **Peer-reviewed anchor exists** — TIMESAFE (ACM ToPS 2025) proves the problem is real and publishable, and **leaves our exact gap open**.

---

## The correlation to what we already built (this is the key point)

It is **the same problem we already solved, at a harder layer.** One-to-one mapping:

| Our existing asset (RIC/KPM) | Re-targeted to Fronthaul S-plane |
|---|---|
| Anomaly on KPM window | Anomaly on **sync telemetry** (PTP offset, PDV, path delay, SyncE ESMC) |
| Discriminate genuine-fault vs adversarial-spoof (`aml_guard`) | Discriminate **timing fault vs PTP spoof** — same H₀/H₁ test |
| Physical-coupling invariants between KPMs | **Physical/temporal invariants** of a real clock vs a spoofed ANNOUNCE/offset |
| Twin counterfactual gates the healing action (`twin_verifier`) | Twin gates the **sync-recovery action** (source failover / holdover) |
| Governor emits heal/hold/veto + reason | Same governor, actions = sync-plane recovery |
| Metric: attack-success vs false-alarm | Same, plus **time-to-recover before 2 s crash** |

So the intellectual core, the code, and the novelty framing **all transfer**. We are not restarting — we are pointing the same governed-discrimination-and-healing engine at a bigger, harder, less-crowded target. Our RIC/KPM result becomes the *validation-on-easy-layer*; the fronthaul timing loop becomes the *headline contribution*.

**Novelty vs the two nearest works, in one line:** TIMESAFE (ACM ToPS 2025) *detects* PTP attacks but does not separate attack from benign timing fault nor self-heal; our RIC work does discrimination+healing but on E2/KPM, not on the safety-critical sync plane. **Fault-vs-attack timing discrimination with twin-verified sync self-healing on the fronthaul is unoccupied.**

---

## Deep-dive confirmation (TIMESAFE full text + released repo)

Read the ACM ToPS 2025 full text and the released code (`github.com/genesys-neu/s-plane_security`, MIT). Confirmed:

1. **TIMESAFE is detection-only ("Prong D").** It classifies benign-vs-malicious PTP *traffic* (transformer/CNN, 97.5%). It **explicitly states the O-RAN spec "does not specify actions to take upon detecting threats"** — the *response* is undefined. That is our contribution slot.
2. **No fault-vs-attack discrimination.** It separates *normal traffic* from *attack traffic*, not a malicious spoof from a benign timing fault (holdover / PDV / SyncE degradation). Our H₀/H₁ discrimination is unoccupied here.
3. **Their twin ≠ our twin role.** TIMESAFE uses its digital twin to *generate data and stage attacks*; it does **not** use a twin as a counterfactual verifier of a recovery action. Our `twin_verifier` role is different and additive.
4. **Recovery dynamics are quantified** → a ready MTTR metric: spoofing → drift >40,000 ns with ~10 s recovery; replay → >20,000,000 ns, slower recovery. A healing loop is measured by how much of that it removes before the 2 s failure.

**Released artifacts we can build on:** attack scripts (`Testbed/`), data collection + preprocessing (`DataCollectionPTP/`), trained detector models (`DU_model/`) = our **baseline to beat**, monitor/attack GUIs, testbed automation, and a promised `.pcap` trace dataset. We *extend a peer-reviewed artifact*, not start from scratch.

**Verdict: GO.** The problem is real (ACM ToPS 2025, 2 s catastrophic failure, no fronthaul security standard), the gap is explicit (detection without response or fault-vs-attack discrimination), the method is ours (discriminate → twin-verify → heal), and the data/baseline are public.

## Honest caveats
- **Realism/hardware:** true S-plane experiments want PTP-capable NICs/switches and an O-RU; without them we validate on **PTP traces + emulated PDV/holdover/spoof** (analogous to how we use KPM datasets now). TIMESAFE-style passive traces are the data path.
- **Twin fidelity** matters even more at ns timescales — the twin models sync dynamics, not full PHY.
- This is a **re-aim, not a rebuild** — but it does require learning the sync-telemetry schema (PTP/SyncE) the way we just learned the KPM schema.
