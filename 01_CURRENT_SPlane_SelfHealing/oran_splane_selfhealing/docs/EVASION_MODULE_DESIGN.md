# Evasion Module — Research Design

Status: scoping (no code yet). Goal: turn the project from a *defence* paper into an
*attack-and-defence* paper by asking a question no one in the timing-security literature has asked —
**can an adaptive attacker defeat an ML-based S-plane detector while its attack still works?**

Novelty basis (checked 2026-08-16): the full "cited by" list of TIMESAFE and the authors' own
thesis contain no evasion/adversarial attack on the timing detector, and none is listed as planned
future work. See `docs/reference_papers/README.md`.

---

## 1. Contribution claim (what the paper asserts)

> ML-based S-plane attack detectors (TIMESAFE-class, and our own RF + open-set + persistence
> pipeline) are evaluated only against *naive* attacks. We construct the first **realizable evasion
> attacks** against such detectors — attacks constrained to remain effective on the wire — and
> measure the effectiveness-vs-stealth trade-off. We then show which evasions the **fail-closed
> provenance defence** stops and which it does not.

This is deliberately falsifiable. It is publishable whether the attack succeeds (detectors are
fragile → here is the fix) or fails (first evidence that realizable evasion is hard in the timing
domain → engages the Apruzzese critique positively).

---

## 2. Threat model (state precisely — reviewers kill vague ones)

**Adversary goal.** Cause served time error to exceed the O-RAN budget (≈100 ns), i.e. the attack
must *still work*, **while** the detector labels the window benign/healthy.

**What the adversary is NOT.** Not a kernel/host adversary (that is a different paper — *Breaking
Precision Time*, ISPCS 2025). Our adversary manipulates only **network-observable PTP traffic** and,
for the suppression variant, the **management-query channel**. This keeps us orthogonal to existing
work.

**Capability tiers (evaluate a spectrum, anchor on grey/black — most realistic):**

| Tier | Detector knowledge | Realism | Use |
|---|---|---|---|
| White-box | full model + params | low | upper bound on evasion power |
| Grey-box | features + architecture, not weights | medium | main result |
| Black-box (transfer) | trains a surrogate, transfers | high | headline realism claim |

**Adversary actions:** observe benign traffic; forge/inject Announce, Sync, Follow-Up, Delay-Resp;
control injection timing and rate; (suppression variant) flood/suppress so `pmc`/management queries
return nothing.

**Knowledge of the defence:** stated per experiment. For the retraining robustness test the defender
re-trains continuously; the attacker does not see post-retraining weights.

---

## 3. Two evasion primitives

**A. Perturbation-based evasion (the hard, interesting one).**
Reshape an attack so its *feature signature* looks benign while the attack still moves the clock.
Not free-space perturbation — every change must be a legal, injectable PTP packet sequence.
Formulated as constrained optimisation (Section 5).

**B. Telemetry-suppression evasion (the novel primitive — our strongest card).**
Do not perturb features at all: suppress the telemetry channel so the monitor goes blind and consumes
stale/last-known values, reporting "healthy" through an active attack. This is an **availability-based
evasion**, categorically different from the adversarial-ML literature (which assumes the detector
still receives input) and immune to the "continuous retraining defeats evasion" critique
(retraining defends nothing when the model sees no data). We already demonstrated the mechanism
(stale-`pmc`); here it is framed as a deliberate attack primitive.

---

## 4. Which attack to reshape first

**First target: Announce / BMCA spoofing.** Rationale:

- It is the family the detectors are **best** at (BMCA transition features push our detection from
  23.9% → ~100%). Evading the strong case is the publishable claim; evading a weak case is not.
- It is **realizable** — the attack is literally forged Announce fields, so perturbations map to real
  packets.
- The tension is scientifically interesting: the attack wins the master election by forging
  *attributes*, so the evasion must preserve the election-win while masking the very BMCA-transition
  features that give it away.

**Pilot first on Replay** (weaker detection, simpler) purely to validate the attack harness and
evaluation loop end-to-end before attempting the hard Announce target. This de-risks the timeline.

---

## 5. Attacker algorithm (perturbation variant)

Constrained search over injectable PTP packet sequences:

```
maximise    Stealth(x)          # 1 - detector_score(features(x))
subject to  Effectiveness(x) ≥ τ   # served time error ≥ 100 ns  (attack still works)
            x ∈ RealizablePTP      # x decodes to a legal, injectable packet sequence
```

- **Effectiveness** is measured by replaying `x` through the existing simulator / ingest pipeline and
  reading the resulting offset — we already have this machinery.
- **Realizable set** is enforced by construction: the optimiser edits *attack parameters*
  (Announce field values, injection cadence, magnitude ramp) rather than raw feature vectors, so every
  candidate is a real attack by definition. This is the problem-space (not feature-space) discipline
  that answers the practicality critique.
- **Search:** start with black-box/gradient-free (the detector is RF + IsolationForest — non-diff):
  random/evolutionary search over the parameter set, or Bayesian optimisation. White-box variant only
  if we add a differentiable surrogate.

---

## 6. Evaluation (pre-register before running — this is what makes it rigorous)

**Primary metric:** the **effectiveness–stealth Pareto front** — attack success rate (fraction of
episodes with served error ≥ budget) vs detection rate, swept over evasion effort. One curve per
detector, per capability tier.

**Detectors under test:**
1. Our pipeline (RF-H1 + group-wise IsolationForest open-set + 2-of-3 persistence + fail-closed gate).
2. A **TIMESAFE-class transformer**, reimplemented and **first validated to reproduce their published
   ~99%** before we attack it (otherwise "you broke a strawman" sinks the paper).

**Conditions:**
- Baseline naive attack (must be caught — sanity check).
- Perturbation evasion (A), grey- and black-box.
- Suppression evasion (B).
- **Retraining-defence test:** continuously re-train the detector (per Apruzzese et al.) and re-measure
  A. Report honestly whether retraining blunts it. B should be unaffected — that is the point.

**Defence half:** show the fail-closed provenance gate's effect — expected result is that it stops (B)
(suppression → UNKNOWN → safe_default) while (A) needs the feature-space detector. This is what makes
it attack-*and*-defence rather than pure attack.

**Both-outcomes plan (pre-registered):**
- If A succeeds → "realizable evasion breaks SOTA timing detectors; fail-closed + provenance is a
  partial fix; feature-space evasion remains open."
- If A fails → "first evidence realizable evasion is hard against timing detectors, corroborating
  Apruzzese in a new domain; but suppression (B) evades regardless, so availability-integrity is the
  real gap."

Either way there is a contribution. We commit to reporting the negative.

---

## 7. Rigor / leakage controls (reuse what already works)

- **Session-level holdout** (`GroupShuffleSplit` on `capture_id`) — attacker-optimised sessions and
  detector-evaluation sessions are disjoint.
- Black-box surrogate is trained on different sessions than the victim detector.
- No tuning of the detector or the evasion after seeing test results.
- Wilson 95% CIs on all rates; multi-seed where stochastic.
- Explicitly audit against Arp et al.'s pitfall list (sampling bias, data snooping, spurious
  correlations) — we already satisfy several; document each.

---

## 8. Legal / safety scope

Entirely **software**: recorded captures + `tc netem` + simulator. **No over-the-air transmission,
no GNSS RF, no live production network.** The suppression variant is emulated at the
capture/management-query level. Nothing here needs RF or spectrum authorisation. (Hardware, if added
later, only strengthens credibility; it is not required for this module.)

---

## 9. Phased plan with decision gates

| Phase | Work | Gate |
|---|---|---|
| 0 | Reimplement TIMESAFE-class transformer; reproduce its ~99% on the public captures | Must match published accuracy ± small margin, else stop and fix |
| 1 | Build attack harness; pilot **perturbation evasion on Replay** | Harness produces realizable attacks whose effectiveness is measurable |
| 2 | **Perturbation evasion on Announce** (grey-box then black-box) | Produce the Pareto front; decide A-succeeds vs A-fails branch |
| 3 | **Suppression evasion (B)** as a deliberate attack; run fail-closed defence against it | Confirm B evades feature detector but is caught fail-closed |
| 4 | Retraining-robustness test; finalise both-outcomes write-up | — |

Phase 0 is the real risk gate: if we cannot fairly reproduce the victim detector, the whole "we break
SOTA" claim is unsupportable and we pivot to attacking only our own pipeline (weaker but still valid).

---

## 10. Risks

1. **Victim-detector fidelity** (Phase-0 gate above). Mitigation: use the public code
   (`genesys-neu/s-plane_security`); consider contacting the authors for an acknowledged verification.
2. **A may not succeed.** Mitigation: pre-registered both-outcomes design; B is the fallback headline.
3. **Practicality critique (Apruzzese).** Mitigation: problem-space (realizable) attacks by
   construction; the retraining test engages the critique head-on; B sidesteps it entirely.
4. **Scope creep.** Mitigation: the phase gates; ship Replay+Announce+suppression, defer multi-family.
5. **Threat-model disputes.** Mitigation: Section 2 states knowledge/capability explicitly per
   experiment.

---

## 11. Repo reuse vs new code

**Reuse:** `fronthaul_sim/`, `faults/injectors.py` (attack shaping), `telemetry/features.py`,
`discriminator/` (victim #1), `ingest/` (effectiveness measurement), the session-holdout evaluation,
`healing/loop.py` fail-closed gate (defence).

**New:** a TIMESAFE-class transformer (victim #2); an `evasion/` module (attacker optimiser +
realizable-attack encoder); a suppression-attack harness; evaluation scripts producing the Pareto
fronts.

---

## 12. Citation discipline

Peer-reviewed only. Cite TIMESAFE as **ACM ToPS 2025 (10.1145/3775060)**; Biggio (ECML PKDD 2013) and
Arp (USENIX Sec 2022) for evasion/methodology; ISPCS 2025 for the host-adversary boundary. No arXiv
preprints or theses in the reference list (see `docs/reference_papers/README.md`).
