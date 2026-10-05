#!/usr/bin/env python3
"""Live mode service (optional, localhost on Linux only).

Runs ONE recovery-loop run at a time with the project's own harness,
03_RECOVERY_LOOP_S-PLANE/code/run_one.py installed under /opt/sptb/recovery (see README "How to re-run"),
and streams the run's loop.jsonl and observer.jsonl to the web UI over a WebSocket.

Safety gates (all must pass, checked at start-up and again before every run):
  * the host is Linux and the service runs as root (network namespaces, nftables, ptp4l need it);
  * `python3 freeze.py --verify` in /opt/sptb/recovery exits 0 with no output (frozen harness unchanged);
  * the tools the harness needs are on PATH (ptp4l, pmc, ip, nft, tcpdump, tcpreplay).
It never touches the host clock: it only starts run_one.py, whose daemons all use free_running 1 and software
timestamping inside network namespaces. Live runs use replicate numbers 200-999 so they can never overwrite or
mix with the evaluation replicates 13-17 or the development replicate 101.

Start:  sudo SPTB=/opt/sptb uvicorn server:app --host 127.0.0.1 --port 8765   (from this folder)
Then set LIVE_SERVICE_URL=http://127.0.0.1:8765 for the Next.js app.
"""
from __future__ import annotations
import asyncio, json, os, platform, shutil, subprocess, sys, threading, time
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover
    sys.exit("pip install -r requirements.txt")

SPTB = os.environ.get("SPTB", "/opt/sptb")
RL = os.path.join(SPTB, "recovery")
CAP = os.path.join(SPTB, "cap")
SCENARIOS = ["baseline", "A1_rogue_master", "A2_sync_spoof", "A3_replay", "A5_dos_flood", "A8_rogue_bc", "C1_removal",
             "C2_malformed", "C3_wholesecond", "B2_gm_failover", "B3_pdv_congestion", "B7_topology_change",
             "B_bc_replacement", "B_unplanned_failover"]
TOOLS = ["ptp4l", "pmc", "ip", "nft", "tcpdump", "tcpreplay"]
REP_MIN, REP_MAX = 200, 999


def preflight() -> dict:
    """Return {ready: bool, checks: [{name, ok, detail}]}. Never raises."""
    checks = []
    is_linux = platform.system() == "Linux"
    checks.append(dict(name="Linux host", ok=is_linux, detail=platform.system()))
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    checks.append(dict(name="Running as root", ok=is_root, detail=f"euid={os.geteuid() if hasattr(os, 'geteuid') else 'n/a'}"))
    missing = [t for t in TOOLS if shutil.which(t) is None]
    checks.append(dict(name="Harness tools on PATH", ok=not missing, detail="missing: " + ", ".join(missing) if missing else "all present"))
    freeze = os.path.join(RL, "freeze.py")
    if not os.path.isfile(freeze):
        checks.append(dict(name="freeze.py --verify", ok=False, detail=f"{freeze} not found (install the harness under {SPTB})"))
    elif not (is_linux and is_root):
        checks.append(dict(name="freeze.py --verify", ok=False, detail="not attempted: requires Linux and root"))
    else:
        try:
            r = subprocess.run([sys.executable, "freeze.py", "--verify"], cwd=RL, capture_output=True, text=True, timeout=60)
            ok = r.returncode == 0 and not r.stdout.strip()
            checks.append(dict(name="freeze.py --verify", ok=ok, detail=(r.stdout + r.stderr).strip()[:300] or "no output (verified)"))
        except Exception as e:  # noqa: BLE001
            checks.append(dict(name="freeze.py --verify", ok=False, detail=str(e)[:300]))
    return dict(ready=all(c["ok"] for c in checks), checks=checks, sptb=SPTB)


class RunRequest(BaseModel):
    scenario: str
    rep: int = Field(ge=REP_MIN, le=REP_MAX)
    arm: str


class State:
    lock = threading.Lock()
    current: Optional[dict] = None


app = FastAPI(title="S-plane live run service", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/status")
def status():
    pf = preflight()
    cur = State.current
    return dict(**pf, running=cur["run"] if cur and cur["proc"].poll() is None else None, scenarios=SCENARIOS, rep_range=[REP_MIN, REP_MAX])


@app.post("/runs")
def start_run(req: RunRequest):
    if req.scenario not in SCENARIOS:
        raise HTTPException(400, f"unknown scenario {req.scenario}")
    if req.arm not in ("control", "loop"):
        raise HTTPException(400, "arm must be control or loop")
    pf = preflight()
    if not pf["ready"]:
        raise HTTPException(409, dict(message="refusing to run: preflight failed", checks=pf["checks"]))
    with State.lock:
        if State.current and State.current["proc"].poll() is None:
            raise HTTPException(409, f"a run is already in progress: {State.current['run']}")
        run = f"{req.scenario}__r{req.rep}__{req.arm}"
        out = os.path.join(CAP, run)
        if os.path.exists(out):
            raise HTTPException(409, f"{out} already exists; choose another replicate number")
        log = open(os.path.join(SPTB, f"live_{run}.log"), "w")
        proc = subprocess.Popen([sys.executable, os.path.join(RL, "run_one.py"), req.scenario, str(req.rep), req.arm],
                                cwd=RL, stdout=log, stderr=subprocess.STDOUT)
        State.current = dict(run=run, dir=out, proc=proc, started=time.time())
    return dict(run=run, dir=out)


@app.websocket("/ws/runs/{run}")
async def stream(ws: WebSocket, run: str):
    await ws.accept()
    cur = State.current
    if not cur or cur["run"] != run:
        await ws.send_json(dict(stream="error", message="no such active run"))
        await ws.close()
        return
    pos = {"loop.jsonl": 0, "observer.jsonl": 0}
    try:
        while True:
            for name in pos:
                p = os.path.join(cur["dir"], name)
                if not os.path.exists(p):
                    continue
                with open(p) as f:
                    f.seek(pos[name])
                    chunk = f.read()
                    # only forward complete lines
                    cut = chunk.rfind("\n") + 1
                    pos[name] += cut
                    for line in chunk[:cut].splitlines():
                        if line.strip():
                            try:
                                await ws.send_json(dict(stream=name.split(".")[0], data=json.loads(line)))
                            except json.JSONDecodeError:
                                pass
            if cur["proc"].poll() is not None:
                tl = os.path.join(cur["dir"], "timeline.json")
                timeline = json.load(open(tl)) if os.path.exists(tl) else None
                await ws.send_json(dict(stream="done", returncode=cur["proc"].returncode, timeline=timeline))
                break
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return
    await ws.close()
