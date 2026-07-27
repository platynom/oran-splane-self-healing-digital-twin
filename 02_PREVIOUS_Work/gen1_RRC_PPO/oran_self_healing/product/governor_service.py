"""
Near-RT RIC xApp-style decision microservice (hardened).

  POST /decide         {kpm}          -> governed RRC action + reason  (audited)
  POST /decide_batch   [{kpm}, ...]   -> list of decisions
  GET  /health                        -> liveness + drift status
  GET  /metrics                       -> Prometheus-style metrics

Run:  uvicorn product.governor_service:app --host 0.0.0.0 --port 8080
"""
import os, sys, yaml
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional
from engine import GovernanceEngine
from persistence import load_artifacts
from monitoring import AuditLog, DriftMonitor, Metrics
from llm_governor import LLMGovernor
from twin_verifier import TwinVerifier

CFG = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "config.yaml")))


class KPM(BaseModel):
    ue_id: int = 0
    rsrp: float; rsrq: float = -12; sinr: float = 20; cqi: int = 12
    neighbor_rsrp_1: Optional[float] = None
    network_load: float = 0.4; latency_ms: float = 20; packet_loss: float = 0.02
    rrc_state: str = "RRC_CONNECTED"; traffic_type: str = "Data"
    ue_speed: float = 3.0


def build_engine():
    gate, guard, meta = load_artifacts(CFG["runtime"]["artifacts_dir"])
    try:
        from stable_baselines3 import PPO
        agent = PPO.load("rrc_ppo_agent", device="cpu")
    except Exception:
        from lite_components import LitePolicyAgent
        agent = LitePolicyAgent()
    gov = LLMGovernor(backend=CFG["governor"]["backend"],
                      model=CFG["governor"]["model"],
                      aml_high=CFG["governor"]["aml_high"])
    ver = TwinVerifier(margin=CFG["verifier"]["margin"])
    return GovernanceEngine(gate, guard, agent, gov, ver,
                            seq_len=CFG["gate"]["seq_len"])


app = FastAPI(title="O-RAN Self-Healing Governor", version="1.1")
ENGINE = AUDIT = DRIFT = METRICS = None


@app.on_event("startup")
def _startup():
    global ENGINE, AUDIT, DRIFT, METRICS
    ENGINE = build_engine()
    AUDIT = AuditLog(CFG["observability"]["audit_log"])
    DRIFT = DriftMonitor(baseline_anomaly_rate=CFG["observability"]["baseline_anomaly_rate"])
    METRICS = Metrics()


def _auth(x_api_key: Optional[str]):
    sec = CFG.get("security", {})
    if sec.get("require_api_key") and x_api_key != sec.get("api_key"):
        raise HTTPException(status_code=401, detail="invalid or missing API key")


def _decide(kpm_dict):
    d = ENGINE.decide(kpm_dict)
    AUDIT.write(kpm_dict, d); DRIFT.update(d); METRICS.observe(d)
    return d


@app.get("/health")
def health():
    return {"status": "ok", "backend": CFG["governor"]["backend"],
            "drift": DRIFT.status() if DRIFT else {},
            "stats": dict(ENGINE.stats) if ENGINE else {}}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return METRICS.render()


@app.post("/decide")
def decide(kpm: KPM, x_api_key: Optional[str] = Header(default=None)):
    _auth(x_api_key)
    return _decide(kpm.model_dump())


@app.post("/decide_batch")
def decide_batch(kpms: List[KPM], x_api_key: Optional[str] = Header(default=None)):
    _auth(x_api_key)
    return [_decide(k.model_dump()) for k in kpms]
