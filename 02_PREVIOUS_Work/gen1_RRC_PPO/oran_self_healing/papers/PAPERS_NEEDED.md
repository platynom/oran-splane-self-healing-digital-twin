# Papers I need in full text (drop the PDFs in this `papers/` folder)

**Why:** my web access does not route through your campus `.edu` network, so IEEE Xplore and Elsevier/ScienceDirect paywalls return empty for me. Open-access ones (arXiv, MDPI) I already read in full. For the paywalled items below, please download the PDF from your library and save it here with the filename shown — then tell me and I'll read them directly and tighten the literature review + differentiation.

---

## Priority 1 — must have (differentiation depends on it)

1. **KDN-driven Zero-Shot Self-Healing for 6G Small Cells** — Elsevier
   - Link (you have access): https://www.sciencedirect.com/science/article/pii/S157087052500232X
   - Save as: `E2_KDN_zero_shot_self_healing.pdf`
   - Why: **nearest published prior to our topic.** I must read the full method to write an honest, precise "how we differ" paragraph (loop type, verification, hardware).

## Priority 2 — strengthens problem statement & baselines

2. **A Measurement Study of Short-Time Cell Outages in Mobile Cellular Networks** — Elsevier Computer Communications
   - Link: https://www.sciencedirect.com/science/article/abs/pii/S0140366415004661
   - Save as: `E1_short_time_cell_outages.pdf`
   - Why: real operator statistics on how frequently faults occur — quantifies the pain point.

3. **Failure Management in 5G RAN: Challenges and Open Research Lines**
   - Search title on IEEE Xplore / ResearchGate 367384546
   - Save as: `I1_failure_management_5G_RAN_open_lines.pdf`
   - Why: a survey that explicitly lists novel/unseen fault handling as *open* — direct citation that our gap is real.

4. **A recent (2023–2025) IEEE RL-based self-healing / handover paper** (VTC, GLOBECOM, ICC, or Access)
   - Any concrete recent one you can pull; e.g. search IEEE Xplore: "reinforcement learning self-healing O-RAN handover xApp"
   - Save as: `I2_RL_self_healing_recent.pdf`
   - Why: concrete closed-world baseline to contrast against (the "before").

## Priority 3 — security cross-link (for Topic B / the governor)

5. **Open RAN is Open to RIC E2 Subscription DoS** — IEEE EuroS&P 2025 (or the closest RIC/E2 security paper you can access)
   - Save as: `I3_ric_e2_security.pdf`
   - Why: grounds the adversarial-governor threat model in a peer-reviewed source.

---

## Already read in full (no action needed — links for your reference)
- A1 — Simba GNN+Transformer RCA — https://arxiv.org/abs/2406.15638
- A2 — Calibrated 5G Simulator — https://arxiv.org/pdf/2404.10643
- M1 — Hy-LIFT LLM fault diagnosis — https://www.mdpi.com/2073-431X/14/12/551

## Also useful if easy to grab
- Any O-RAN ALLIANCE WG spec on **fronthaul (O-DU↔O-RU) fault management** — supports the injected demonstrator fault as realistic.
- The **VERGE OAI_RAN_KPM** dataset paper/README (real-KPM validation source).
