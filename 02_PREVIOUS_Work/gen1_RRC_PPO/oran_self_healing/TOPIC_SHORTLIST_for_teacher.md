# Candidate Project Topics — AI-Native Self-Healing O-RAN + Digital Twin
Shortlist from research session. Each: Title | What it does | Honest status.

## A. Closest to the given topic (self-healing + digital twin + AI)

1. **AI-Native Cell-Outage Self-Healing for O-RAN — Digital-Twin-Driven RL xApp for Automatic Coverage Compensation**
   - Kill a failed cell → twin predicts the dead-zone → RL reconfigures neighbours (power/tilt/steer users) to fill the hole, revert on recovery.
   - Status: REAL, debuggable, textbook 3GPP self-healing. Well-studied (classic SON COD/COC) but strong, buildable thesis. Keeps every word of the topic.

2. **Open-World / Competence-Aware Self-Healing** — agent that "knows what it doesn't know"; on an unseen fault it defers, an LLM proposes a fix, the twin validates it, and it's distilled back into the RL policy (self-expanding).
   - Status: Higher research novelty (medium-high); ingredients exist (Voyager, OOD-RL). Great thesis / possible workshop paper. No patent.

3. **Adversarial-Aware, Twin-Verified LLM Governor for RRC Self-Healing** — tells a real fault from a spoofed/attacked KPM before acting; physics-guard + LLM governor + twin veto. (Already prototyped this session.)
   - Status: Integration-level novelty. Good demo/thesis; not patentable; security angle is crowded.

## B. Self-healing, but different fault type

4. **Twin-Based Timing/Sync Self-Healing** — detect a failing/spoofed timing source (GNSS vs PTP vs SyncE) by cross-source consistency; predict holdover drift; switch before the cell drops.
   - Status: Real, hardware-flavoured. Crowded (TIMESAFE, GNSS-spoofing patents). Thesis-viable.

5. **Twin-Refereed xApp Conflict Self-Healing** — use the twin to catch conflicting xApp control actions (esp. implicit conflicts) before they destabilise the network.
   - Status: Real, O-RAN-Alliance-recognised. Already published (COMIX) AND patented (US 12,556,972). Thesis only, not patent.

## C. Hardware + AI (patent-shaped; needs a lab/department)

6. **Digital-Twin-Trained Self-Healing RIS for O-RAN Coverage Restoration** — when a cell fails, an AI (twin-trained) re-aims a Reconfigurable Intelligent Surface (smart radio "mirror") to bounce a neighbour's signal into the dead zone.
   - Status: Best patent odds we found (still Low-Med; US 12,483,315 nearby). Hardware, "wow", India-relevant (rural). Bigger build.

7. **Hardware Safety-Interlock for the RIC** — an FPGA apparatus that physically blocks unsafe/conflicting E2 control commands before they reach the radio.
   - Status: Apparatus-claim patentable-ish; abstract; overlaps zero-trust/conflict work.

## D. Biggest real-world problem (but NOT "healing")

8. **Green O-RAN: Twin-Verified, QoS-Safe Energy Minimisation Beyond Radio-Unit Sleep** — save base-station energy (carrier shutdown + user steering) with the twin guaranteeing QoS.
   - Status: HUGE real problem (energy = ~90% of OPEX, big carbon/India-grid impact). Hot & crowded (Kairos INFOCOM'25, hybrid-xApp+DT '25). NOT self-healing. Strong thesis if theme can change.

---

## Honest guidance for the discussion
- **Most on-topic + safest thesis:** #1 (Cell-Outage Self-Healing) or #3 (already built).
- **Most research novelty (paper potential):** #2 (Open-World).
- **Best patent shot (needs hardware/lab):** #6 (RIS).
- **Biggest real-world impact (but drops "self-healing"):** #8 (Energy).
- Reality check for all: this whole space is IP-heavy and fast-moving; a clean patent is hard, but any of these makes a strong **project/thesis**. In India, pure-software/AI methods face **Section 3(k)** (algorithms not patentable) — only the **hardware** ones (#6, #7) are realistically patentable.
