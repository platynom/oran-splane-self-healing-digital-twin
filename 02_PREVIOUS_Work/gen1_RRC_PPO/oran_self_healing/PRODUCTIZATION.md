# Productization — O-RAN Self-Healing Governor

This turns the research prototype into a deployable **decision service** (a
Near-RT RIC xApp-style microservice) plus a config-driven training/eval pipeline.

## What is now product-shaped

```
product/
  config.yaml           # single source of truth (backends, thresholds, paths)
  engine.py             # GovernanceEngine: streaming decide(kpm) with per-UE window
  governor_service.py   # FastAPI service: POST /decide, /decide_batch, GET /health
  pipeline.py           # CLI: train | evaluate | serve
  persistence.py        # fit-once, load-fast artifacts (gate + guard)
  requirements.txt      # lite runtime (runs anywhere, no deep learning)
  requirements-full.txt # full runtime (real LSTM-AE + PPO + optional Claude API)
  Dockerfile            # containerised service, fits artifacts at build time
tests/
  test_governance.py    # unit tests for spoof-veto, fault-heal, false-alarm-hold
artifacts/              # persisted fitted gate + guard (created by `train`)
```

## Run it

```bash
# 1. fit + persist the gate and guard
python product/pipeline.py train

# 2. launch the decision service
python product/pipeline.py serve        # -> http://localhost:8080

# 3. ask it for a decision
curl -X POST localhost:8080/decide -H "Content-Type: application/json" \
  -d '{"ue_id":1,"rsrp":-128,"sinr":30,"cqi":15,"neighbor_rsrp_1":-120}'
# -> {"cause":"adversarial","action_name":"keep_connected","verdict":"veto",...}
```

Docker:
```bash
docker build -f product/Dockerfile -t oran-governor .
docker run -p 8080:8080 oran-governor
```

## Verified locally (in this build)
- Streaming decisions from persisted artifacts, **~0.3 ms/decision**.
- Spoofed RSRP collapse and fake congestion → **vetoed** (connection held).
- Genuine RLF → **healed** (handover committed).
- 4/4 unit tests pass.
- Runs with lite surrogates when PyTorch/SB3 absent; auto-uses the real
  LSTM-AE gate and trained PPO when they are installed.

## Honest product-readiness scorecard

| Layer | Status | Evidence |
|---|---|---|
| Decision logic (governor/guard/verifier) | **Product-grade** | tested, deterministic, <1 ms |
| Service API + packaging + Docker | **Product-grade** | FastAPI, config, artifacts, container |
| Anomaly gate + RL agent | Prototype | works with surrogates; real models need `requirements-full` |
| **Data** | **Lab-grade** | synthetic twin + 1 single-UE testbed trace |
| Live RIC (E2/KPM) integration | **Not started** | offline replay only |
| Security hardening / MLOps / monitoring | Not started | no auth, no drift monitoring yet |

**Overall: a deployable prototype service (~30–35% to a real operator product).**
The architecture is production-shaped; the gaps are *data scale* and *live
integration*, both of which require your machine / a testbed — see
`LOCAL_CLAUDE_PROMPTS.md` for the exact steps.

## The critical path to a real product
1. **Real multi-cell data** (Prompt 3–4): retrain on Colosseum/OpenRAN-Gym traces.
   This is the single biggest credibility jump.
2. **Real models** (Prompt 1–2): LSTM-AE gate + trained PPO instead of surrogates.
3. **Live E2/KPM xApp adapter** (Prompt 7): stream real indications in, control out.
4. **MLOps**: auth on the API, drift monitoring on the guard, decision audit log,
   canary/rollback for the RL policy.
```
