# Copy‑paste prompts for your LOCAL machine (Claude Code / Cowork)

Run these on your own machine, inside the project folder `oran_self_healing`.
They do the environment‑dependent work I could not do in the sandbox (PyTorch
install is network‑blocked here, and big real datasets need registration/bandwidth).
Do them in order. Each is self‑contained — safe to paste even in a fresh session.

---

## Prompt 1 — Install the full (deep‑learning) runtime
```
In the oran_self_healing project, install the full runtime so the real models work:
pip install -r product/requirements-full.txt
Then verify: python -c "import torch, stable_baselines3; print('ok', torch.__version__)".
If torch install is slow, use the CPU wheel: pip install torch --index-url https://download.pytorch.org/whl/cpu
Report the versions and confirm imports succeed.
```

## Prompt 2 — Re‑run the full experiment with the REAL LSTM‑AE + trained PPO
```
In oran_self_healing, run: python main_governed.py
Confirm the log shows "gate: LSTM autoencoder (torch)" and "agent: PPO (rrc_ppo_agent.zip)"
(NOT the surrogates). Then paste me the full security-evaluation table, the confusion
matrix, and the real-data validation line. Compare these numbers to the surrogate run in
GOVERNED_SELF_HEALING.md and tell me what changed.
```

## Prompt 3 — Pull a LARGER, real multi‑cell O‑RAN dataset
```
Clone a real multi-cell O-RAN KPM dataset for training/validation:
  git clone https://github.com/wineslab/colosseum-oran-coloran-dataset
  git clone https://github.com/wineslab/colosseum-oran-commag-dataset
Inspect the CSV schema (columns, #cells, #UEs, #rows). Then write
src/real_kpm_adapter.py that maps its columns onto our feature space
(rsrp, rsrq, sinr, cqi, latency_ms, packet_loss, network_load, neighbor_rsrp_1)
and produces a dataframe with the same schema as data/rrc_dataset_adversarial.csv.
Save the adapted CSV to data/real/coloran_adapted.csv and print summary stats.
```

## Prompt 4 — Retrain + evaluate the whole governor on the REAL dataset
```
Point product/config.yaml data.train_csv at data/real/coloran_adapted.csv.
Then: python product/pipeline.py train   (fits gate+guard on real benign data)
Then re-run the 3-config evaluation on the real data by adapting main_governed.py to
load data/real/coloran_adapted.csv instead of generating synthetic data. Keep the
adversarial injector and fault_coupling steps. Paste me the new security table and tell
me honestly how much the attack-success-rate / false-heal / cause-accuracy move versus
the synthetic run. This is the key credibility step toward "product".
```

## Prompt 5 — Turn on the real Claude‑API governor
```
Set an env var ANTHROPIC_API_KEY to my key, then in main_governed.py change
LLMGovernor(backend="offline") to LLMGovernor(backend="claude"). Run a SMALL slice
(e.g. first 500 steps) so the API cost is low, and compare the Claude governor's
cause-classification accuracy and example reasons against the offline governor.
Report cost per 1k decisions and latency.
```

## Prompt 6 — Launch the decision service and load‑test it
```
In oran_self_healing:  python product/pipeline.py train  then  python product/pipeline.py serve
The FastAPI service starts on :8080. POST a few KPM snapshots to /decide (healthy,
spoofed RSRP collapse, fake congestion, real RLF) and confirm the verdicts
(veto / commit / hold). Then run a quick load test (e.g. 5k requests) and report
throughput and p95 latency. Everything is defined in product/governor_service.py.
```

## Prompt 7 (advanced) — Wire it to a live Near‑RT RIC (real product step)
```
Research how to receive E2SM-KPM indications from a Near-RT RIC (FlexRIC or OSC RIC)
as an xApp, and write an adapter that converts each KPM indication into the dict schema
our product/engine.py GovernanceEngine.decide() expects, then sends the returned RRC
action back over E2 as a control message. Produce a design doc first (message formats,
per-UE state, failure modes), then a prototype adapter. Do NOT connect to production;
target a local FlexRIC + OpenAirInterface testbed.
```

---

### If a usage limit expires mid‑task, paste this to resume
```
Resume the O-RAN self-healing productization in oran_self_healing. Read
GOVERNED_SELF_HEALING.md and PRODUCTIZATION.md for context. The governance layer
(src/aml_guard.py, src/llm_governor.py, src/twin_verifier.py, product/engine.py) and the
decision service (product/governor_service.py) are already built and tested. Tell me which
of Prompts 1–7 in LOCAL_CLAUDE_PROMPTS.md is not yet done, and continue from there.
```
