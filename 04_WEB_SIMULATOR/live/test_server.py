"""Tests for the live service's refusal gates (no linuxptp needed)."""
import importlib, os, sys
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
from fastapi.testclient import TestClient  # noqa: E402


def load(tmp_sptb):
    os.environ["SPTB"] = str(tmp_sptb)
    import server
    return importlib.reload(server)


def test_refuses_on_non_linux(tmp_path):
    s = load(tmp_path)
    with mock.patch.object(s.platform, "system", return_value="Darwin"):
        pf = s.preflight()
    assert not pf["ready"]
    assert next(c for c in pf["checks"] if c["name"] == "Linux host")["ok"] is False


def test_refuses_when_not_root(tmp_path):
    s = load(tmp_path)
    with mock.patch.object(s.os, "geteuid", return_value=1000):
        pf = s.preflight()
    assert not pf["ready"]
    assert next(c for c in pf["checks"] if c["name"] == "Running as root")["ok"] is False


def test_refuses_when_freeze_verify_fails(tmp_path):
    rl = tmp_path / "recovery"
    rl.mkdir()
    (rl / "freeze.py").write_text("print('MISMATCH', ['run/decision_rule.py']); raise SystemExit(1)\n")
    s = load(tmp_path)
    with mock.patch.object(s.platform, "system", return_value="Linux"), mock.patch.object(s.os, "geteuid", return_value=0), \
            mock.patch.object(s.shutil, "which", return_value="/usr/bin/x"):
        pf = s.preflight()
    fv = next(c for c in pf["checks"] if c["name"] == "freeze.py --verify")
    assert fv["ok"] is False and "MISMATCH" in fv["detail"]
    assert not pf["ready"]


def test_accepts_when_all_gates_pass(tmp_path):
    rl = tmp_path / "recovery"
    rl.mkdir()
    (rl / "freeze.py").write_text("import sys; sys.exit(0)\n")
    s = load(tmp_path)
    with mock.patch.object(s.platform, "system", return_value="Linux"), mock.patch.object(s.os, "geteuid", return_value=0), \
            mock.patch.object(s.shutil, "which", return_value="/usr/bin/x"):
        assert s.preflight()["ready"]


def test_post_runs_returns_409_when_preflight_fails(tmp_path):
    s = load(tmp_path)  # no harness installed under tmp_path
    c = TestClient(s.app)
    r = c.post("/runs", json={"scenario": "A1_rogue_master", "rep": 201, "arm": "loop"})
    assert r.status_code == 409
    assert "refusing" in r.json()["detail"]["message"]


def test_rejects_evaluation_replicates_and_unknown_scenarios(tmp_path):
    s = load(tmp_path)
    c = TestClient(s.app)
    assert c.post("/runs", json={"scenario": "A1_rogue_master", "rep": 13, "arm": "loop"}).status_code == 422
    assert c.post("/runs", json={"scenario": "rm -rf /", "rep": 300, "arm": "loop"}).status_code == 400
    assert c.post("/runs", json={"scenario": "A1_rogue_master", "rep": 300, "arm": "sideways"}).status_code == 400
