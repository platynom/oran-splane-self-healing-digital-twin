from __future__ import annotations

"""Mechanical ground-truth audit of the repository state.

Purpose: agent reports are self-narrated and have repeatedly overstated completion
(a task reported "complete" with no commit made; a stale results file presented as a
fresh run). This script asserts facts from disk and git instead of trusting prose.

Run it after ANY agent session:

    python scripts/audit_state.py                 # human-readable
    python scripts/audit_state.py --max-age-min 60  # flag results older than 60 min

Exit code 1 if any CRITICAL check fails, so it can gate a commit.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

OK, WARN, FAIL = "PASS", "WARN", "FAIL"
_results: list[tuple[str, str, str]] = []


def check(name: str, status: str, detail: str = "") -> None:
    _results.append((status, name, detail))


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO), *args], text=True, stderr=subprocess.DEVNULL, timeout=120
        ).strip()
    except Exception as exc:  # pragma: no cover - environment dependent
        return f"<git error: {exc}>"


def _age_minutes(path: Path) -> float | None:
    if not path.exists():
        return None
    return (time.time() - path.stat().st_mtime) / 60.0


# --------------------------------------------------------------------------- git

def audit_git() -> None:
    head = _git("log", "--oneline", "-1")
    check("git HEAD", OK, head)

    dirty = [ln for ln in _git("status", "--porcelain").splitlines() if ln.strip()]
    check(
        "uncommitted files",
        WARN if dirty else OK,
        f"{len(dirty)} modified/untracked — work is unsaved" if dirty else "clean tree",
    )

    tags = _git("tag", "-l").split()
    restore = [t for t in tags if t.startswith("known-good")]
    check(
        "restore point tag",
        OK if restore else FAIL,
        ", ".join(restore) if restore else "NO known-good tag — no rollback anchor",
    )

    unpushed = _git("rev-list", "--count", "@{u}..HEAD")
    if unpushed.isdigit():
        n = int(unpushed)
        check(
            "unpushed commits",
            WARN if n else OK,
            f"{n} commits exist only on this machine" if n else "in sync with remote",
        )
    else:
        check("unpushed commits", WARN, "no upstream configured")


# ------------------------------------------------------------------- freshness

def audit_freshness(max_age_min: float) -> None:
    """Catch stale artefacts being reported as fresh results."""
    watched = {
        "results/SUMMARY.md": "run_all.py output",
        "results/tier2/TIER2_REPORT.md": "run_tier2.py output",
        "results/tier2/netem/netem_run_status.csv": "live netem harness output",
    }
    for rel, what in watched.items():
        age = _age_minutes(ROOT / rel)
        if age is None:
            check(f"freshness: {rel}", WARN, f"missing ({what})")
        elif age > max_age_min:
            check(
                f"freshness: {rel}",
                WARN,
                f"{age/60:.1f} h old — STALE, do not report as a fresh run ({what})",
            )
        else:
            check(f"freshness: {rel}", OK, f"{age:.0f} min old")


# -------------------------------------------------------------- safety tripwire

def audit_tripwire() -> None:
    """CRITICAL: invalid telemetry must never be labelled healthy."""
    import pandas as pd

    # Only true DECISION files. *_telemetry.csv holds raw ingest rows whose `label`
    # is the scenario tag, not a decision output -- auditing those produces false
    # positives (a healthy-scenario sample with telemetry_valid=False is expected).
    files = [f for f in sorted((ROOT / "results").rglob("*decisions*.csv"))
             if not f.name.endswith("_telemetry.csv")]
    if not files:
        check("fail-closed tripwire", WARN, "no decision CSVs found to audit")
        return

    total, violations, audited = 0, 0, 0
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        # A decision file must carry the decision output columns.
        if "label" not in df.columns or not {"action", "reason"} & set(df.columns):
            continue
        audited += 1
        total += len(df)
        if "telemetry_valid" in df.columns:
            bad = df[(~df["telemetry_valid"].astype(bool)) & (df["label"] == "healthy")]
        elif "reason" in df.columns:
            invalid_reason = df["reason"].astype(str).str.contains("invalid|missing", case=False)
            bad = df[invalid_reason & (df["label"] == "healthy")]
        else:
            continue  # no provenance column to audit against
        if len(bad):
            violations += len(bad)
            check(f"TRIPWIRE VIOLATION in {f.name}", FAIL,
                  f"{len(bad)} windows: invalid telemetry labelled 'healthy'")

    check(
        "fail-closed tripwire",
        FAIL if violations else OK,
        f"{audited} files, {total} decisions, {violations} violations",
    )


# ------------------------------------------------------------------ repo health

def audit_repo_health() -> None:
    git_dir = REPO / ".git"
    if git_dir.exists():
        size_mb = sum(f.stat().st_size for f in git_dir.rglob("*") if f.is_file()) / 1e6
        check(
            ".git size",
            WARN if size_mb > 250 else OK,
            f"{size_mb:.0f} MB" + (" — large blobs in history" if size_mb > 250 else ""),
        )

    lock = git_dir / "index.lock"
    check("git index.lock", FAIL if lock.exists() else OK,
          "STALE LOCK present" if lock.exists() else "none")

    n_tests = len(list((ROOT / "tests").glob("test_*.py")))
    check("test files", OK, f"{n_tests} test modules present")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-min", type=float, default=120.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    audit_git()
    audit_freshness(args.max_age_min)
    audit_tripwire()
    audit_repo_health()

    if args.json:
        print(json.dumps([{"status": s, "check": c, "detail": d} for s, c, d in _results], indent=2))
    else:
        width = max(len(c) for _, c, _ in _results)
        print("\n=== REPOSITORY GROUND-TRUTH AUDIT ===\n")
        for status, name, detail in _results:
            print(f"[{status:4}] {name:<{width}}  {detail}")
        fails = sum(1 for s, _, _ in _results if s == FAIL)
        warns = sum(1 for s, _, _ in _results if s == WARN)
        print(f"\n{fails} failed, {warns} warnings, "
              f"{sum(1 for s,_,_ in _results if s==OK)} passed\n")

    return 1 if any(s == FAIL for s, _, _ in _results) else 0


if __name__ == "__main__":
    sys.exit(main())
