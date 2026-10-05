# Codex / agent handoff — continue the O-RAN Self-Healing Governor

Paste this whole file to Codex (or any coding agent) if my session hits a limit.
It is self-contained: it explains the project, what is done, and the exact next tasks.

---

## Context
Project root: `oran_self_healing`. Goal: productise an **adversarial-aware,
digital-twin-verified LLM governor** for O-RAN RRC self-healing. The governor sits
above a PPO healing agent and, for every anomaly, decides cause =
**benign / genuine_fault / adversarial(spoofed KPM)**, then either heals, holds, or
vetoes — with a digital-twin counterfactual check and an auditable reason.

Read these first: `GOVERNED_SELF_HEALING.md` (novelty + results),
`PRODUCTIZATION.md` (service architecture), `LOCAL_CLAUDE_PROMPTS.md` (env steps).

## What is already DONE and tested
- Novelty layer in `src/`: `adversarial_injector.py`, `fault_coupling.py`,
  `aml_guard.py`, `twin_verifier.py`, `llm_governor.py` (offline + Claude backend),
  `governed_healing_loop.py`, `governed_evaluation.py`, `real_kpm_validation.py`,
  `lite_components.py` (torch-free surrogates).
- Experiment: `python main_governed.py` → Attack-Success 65%→0%, False-Heal 10%→0%,
  genuine-fault reward improves, cause-accuracy ~0.90; plot in `outputs/`.
- Product service in `product/`: `engine.py` (streaming `decide`), `governor_service.py`
  (FastAPI /decide,/decide_batch,/health,/metrics, API-key auth), `pipeline.py`
  (train|evaluate|serve), `persistence.py`, `monitoring.py` (audit log, drift, metrics),
  `benchmark.py` (~2,800 dec/s, p95 0.5 ms), `e2_kpm_adapter.py` (live-RIC stub),
  `Dockerfile`, `requirements*.txt`. Tests: `tests/test_governance.py` (4 pass).
- Fitted artifacts persisted in `artifacts/` (gate.pkl, guard.pkl).

## Environment reality
The build sandbox could NOT install PyTorch (CUDA wheel host blocked) so the runs used
torch-free surrogates for the LSTM-AE gate and PPO agent. The governance logic is
identical; it auto-uses the real models when torch/SB3 are present.

## YOUR TASKS (in order) — do them, report numbers after each
1. **Full runtime**: `pip install -r product/requirements-full.txt`; verify
   `python -c "import torch, stable_baselines3"`.
2. **Real-model run**: `python main_governed.py`; confirm the log says
   "gate: LSTM autoencoder (torch)" and "agent: PPO (rrc_ppo_agent.zip)". Paste the
   security table + confusion matrix; compare to the surrogate numbers in
   `GOVERNED_SELF_HEALING.md`.
3. **Real multi-cell dataset**: clone `github.com/wineslab/colosseum-oran-coloran-dataset`.
   Write `src/real_kpm_adapter.py` mapping its columns to our feature schema
   (rsrp,rsrq,sinr,cqi,latency_ms,packet_loss,network_load,neighbor_rsrp_1). Save
   `data/real/coloran_adapted.csv`; print schema + stats.
4. **Retrain + evaluate on real data**: set `product/config.yaml:data.train_csv` to the
   adapted CSV; `python product/pipeline.py train`; adapt `main_governed.py` to load the
   real CSV (keep adversarial_injector + fault_coupling). Report how ASR / false-heal /
   cause-accuracy change vs synthetic. NOTE: on real data the benign SINR/CQI are NOT
   saturated, so re-enable the linear residual couplings in `aml_guard.py` (they were
   disabled only because the synthetic SINR/CQI were constant) and re-tune the rule
   thresholds in `_rule_flags`.
5. **Claude governor**: set `ANTHROPIC_API_KEY`, use `LLMGovernor(backend="claude")` on a
   500-step slice; compare cause-accuracy + example reasons + cost/latency vs offline.
6. **Serve + load test**: `python product/pipeline.py serve`; POST the 4 canonical KPMs
   (healthy, spoof RSRP, fake congestion, real RLF); confirm veto/commit/hold; run
   `python product/benchmark.py -n 50000` and report throughput/p95.
7. **Live RIC (stretch)**: implement `receive_indications()` / `send_control()` in
   `product/e2_kpm_adapter.py` against a FlexRIC + OpenAirInterface testbed (NOT
   production). Deliver a design doc first, then a prototype.

## Guardrails
- Keep the 3-way honest metrics (ASR, false-heal, cause-accuracy); don't overfit to make
  them look perfect — partial adversarial recall with 0% attack success is the true story.
- Don't touch the user's original pipeline files' behaviour; add, don't break.
- Every new module must stay importable without torch (graceful fallback).
