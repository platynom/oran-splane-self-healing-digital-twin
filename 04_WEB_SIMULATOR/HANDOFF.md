# HANDOFF — 04_WEB_SIMULATOR

Branch `webapp` (from `full-project-2026-10-05`). All work is inside `04_WEB_SIMULATOR/`; nothing else in the
repository was modified. Built and verified on 5 Oct 2026.

## 1. What was built

**Data layer**
- `ingest/extract.py`: before reading anything, sha256-checks the recovery archive and `EVALUATION_RL.json` against
  `SHA256SUMS.txt`, and the campaign archive against its `.sha256`. It then extracts:
  - 140 recovery runs: observer samples with the PREREGISTRATION §4 healthy flag, `loop.jsonl` events, ptp4l port-state
    lines, per-0.5 s PTP frame counts from the brDN/brUP captures, final nft ruleset, Announce gaps;
  - 168 campaign runs: base, v2 and v3 verdicts;
  - the fault catalogue and look-alike table from the 5 Oct workbooks.

  It re-scores every run, compares each field with `EVALUATION_RL.json` and `EVALUATION_V4.json`, and stops with
  `DATA_DISCREPANCIES.md` on any difference. **None were found** (notes in `DATA_DISCREPANCIES.md`).
- `ingest/rule_windows.py`: re-runs the **frozen** rule (hash-checked) on each control run's recorded capture for
  W = 2, 4, 6, 8, 10 s. At W = 6 s it agrees with the verdicts logged live at 3426/3430 ticks.
- PostgreSQL via Prisma: scenarios, runs, 52 080 samples, 12 055 events, packet series, rule windows, aggregates,
  campaign runs, faults, look-alikes, provenance, and the learner and auth tables.
- `scripts/ingest.ts`: loads the data, then **recomputes every metric from the stored rows** in TypeScript and
  refuses to finish on any mismatch.

**Replay (default, measured).** The GM-A / GM-B / BC / standby BC / RU1–3 / rogue GM / rogue BC / injector topology
on brUP and brDN.
- *Packets:* animated from the run's real frame counts (Sync/Follow_Up, Announce, Delay, other), aligned to the
  loop's clock with an anchor validated to ≤ 1 ms.
- *RU state:* colour, port state and parent arrows come from the pmc observer.
- *Loop actions:* isolated ports (red ✕), standby BC activation, would-act ghosts in the control arm.
- *Controls:* side by side (control vs loop, same scenario and replicate) or single arm; event log, scrubber with
  event markers, 0.5×–4× playback.

**Sandbox (MODEL, labelled).** The decision logic of `recovery_loop.py` replayed over recorded control-run inputs.
- *Parameters:* window W, persistence K of N, service-loss threshold, maintenance grace.
- *Outputs:* the decision-flow path, verdict strip, predicted outcome next to the measured control and the closest
  real loop run, and a sweep over all 70 cases (benign harm, ambiguous-case actions).
- *Calibration:* at the pre-registered parameters it reproduces the loop's logged decisions in 70/70 control runs.

**Learning path.** 7 lessons, each with 2–3 interactive steps and a 3-question check. Every answer has instant
feedback and a citation.
- *Widgets:* planes, timing budget, topology tour, PTP message ladder, t1–t4 offset calculator with asymmetry,
  profile legality check, BMCA arena (drag-and-drop, with keyboard buttons), stepsRemoved (measured A8 counts), and
  look-alikes from the workbook.
- *Real-data steps:* "You are the rule" on real campaign runs, including the rule's own error on B_bc_replacement;
  embedded replays of all 8 attacks, the benign faults and the B3 r17 H3 failure.
- *Loop and limits:* loop stepper, policy table, limits cards.
- *Progress:* XP, streak and per-lesson progress are stored in PostgreSQL per user. Guest mode uses an httpOnly
  cookie; sign-in is NextAuth (GitHub OAuth and/or email magic link, each enabled when configured), and guest
  progress is merged on sign-in.

**Dashboard (measured).**
- H1–H4 and control-integrity cards. **H3 is shown as FAILED** with the B3 r17 explanation and a replay link.
- Per-scenario control-vs-loop bars with exact medians, actions, verification, escalations, detection/action latency
  and RU3.
- Loop timing and the detection-campaign summary (base / v2 / v3 per scenario).
- The Limits panel.

**Fault catalogue.** 22 entries (A1–A8, B1–B8, C1–C3, planned BC replacement, unplanned failover, baseline) with
Source, Destination, Attack devices, Consequence, detectability, WG11 threat ID and citations. Search and filters by
class and testbed requirement.

**Live mode (optional).** `live/server.py` (FastAPI) runs `run_one.py` and streams `loop.jsonl` / `observer.jsonl`
over a WebSocket into the same topology view.
- Refuses unless the host is Linux, it runs as root, the tools are installed and `freeze.py --verify` passes.
- Never touches the host clock; uses replicate numbers 200–999 only.
- Disabled on Vercel, with a message saying so.

**About & limits.** What is measured vs modelled, the testbed limits, and the provenance table with archive hashes.

## 2. How to run locally

```bash
cd 04_WEB_SIMULATOR && docker compose up --build        # http://localhost:3000 (loads data on first start)
```
or, for development: `cp .env.example .env`, then `docker compose up -d db && npm ci && npm run db:setup && npm run dev`.
Full steps, Vercel and live mode: `README.md`.

## 3. What was tested (results from the final run on 5 Oct 2026)

| Gate | Command | Result |
|---|---|---|
| Lint | `npm run lint` (ESLint, 0 warnings allowed) | pass |
| Types | `npm run typecheck` | pass |
| Unit + DB | `npm test` | **38/38 pass**: A1 38.5/2.0, C1 39.0/2.5, C3 38.5/2.0; every scenario/arm median and restored count equal to `EVALUATION_RL.json`; H1/H2/H4/control PASS, H3 FAIL 1/25 Wilson [0.007, 0.195]; 41 would_act; 35/35 isolations in nft and 6/6 standby with bcs.log; detection ≈ 1.1 s, action ≈ 2.1 s; B3 r17 16.5 vs 3.5 s; RESULTS §4 (A8 parent unchanged, C3 forger); **all 140 runs re-scored from the DB rows equal to EVALUATION_RL.json in every outcome field**; campaign v3 95/96, 47/60, 12/12, 84/96, base 60/96, v2 = v3 on all 168; catalogue completeness; provenance hashes; sandbox model 70/70 calibration; no phone numbers anywhere in the folder |
| Production build | `npm run build` | pass |
| E2E | `npx playwright test` against `next start` | **12/12 pass**: home; a lesson completed end to end with progress and XP in the DB; A1 control vs loop replay played to the end, with the isolation logged at the recorded time (T0 + 2.081 s; verification passed at T0 + 3.21 s) and the port turning isolated exactly then, and control showing only would_act; dashboard numbers equal to `/api/aggregates` and RESULTS; sandbox labelled MODEL with 70/70 calibration; catalogue filters; live mode disabled message; **no console errors on 16 pages**; no horizontal scroll at 390 px; reduced motion (no packet animation, state still updates); keyboard (skip link, play/pause); **axe WCAG 2.1 AA (incl. contrast): no serious or critical violations** on 8 pages |
| E2E in Docker | same suite against the `docker compose` stack (fresh DB volume, first-start ingest) | 12/12 pass |
| Lighthouse 12.8 | production build, mobile emulation (`docs/lighthouse/summary.json`) | Performance 92–99, Accessibility 100, Best practices 100, SEO 100 on home, learn, replay, sandbox, dashboard, catalogue; CLS 0; 0 console errors |
| Live service | `cd live && python3 -m pytest -q` | 6/6 pass (refuses on non-Linux, non-root, failing freeze verify; 409 when the preflight fails; rejects evaluation replicates and unknown scenarios) |

## 4. Screenshots (`docs/screenshots/`, regenerate with `node scripts/screenshots.mjs`)

01 home · 02 learning path · 03 BMCA arena · 04 "You are the rule" · 05 offset calculator · 06 A1 replay side by side ·
07 C1 failover · 08 B3 r17 (the H3 failure) · 09–10 dashboard · 11 sandbox (model) · 12 fault catalogue · 13 about &
provenance · 14 live mode disabled · 15 dark mode · 16–17 mobile.

## 5. Deployment status

**Deploy-ready, not deployed.** No Vercel token was available in this environment, so no preview was created.
`vercel.json`, `.env.example` and README §4 cover the setup:

- Vercel *Root Directory* = `04_WEB_SIMULATOR`.
- Neon or Supabase pooled `DATABASE_URL` plus direct `DIRECT_URL`.
- `NEXTAUTH_SECRET` and `NEXTAUTH_URL`; optionally GitHub OAuth or SMTP.
- Load the data once from a workstation with `npm run db:setup`. The database is about 47 MB.

No secrets are in git; `.env` is ignored.

## 6. Remaining limitations

- **Testbed limits apply to every number:** software timestamping; `free_running 1` (clocks never steered, so outcomes
  are parent/GM/port state, not nanosecond time error); namespaces on one host; the nft bridge filter is a stand-in
  for a switch ACL, not Annex P authentication; no digital twin; 5 replicates per arm.
- **Packet animation:** dots are drawn from per-0.5 s counts (scaled, capped). They are not individual frames.
  Attribution is by MAC address, which the UI explains:
  - A3's replayed frames carry the BC's MAC and show up in the BC rate;
  - C2/C3 injectors use GM-A's MAC on brDN;
  - frames dropped by nft do not appear in the bridge capture.
- **The sandbox is a model.** Localisation for W ≠ 6 s is taken from the live 6 s log. Recovery after an action uses
  the median latency measured in the loop runs. It does not model what an action does to radio units that were not
  harmed, a second action, or an attacker that adapts.
- **Live mode was verified only for its refusal gates** (unit tests and this container, which has no linuxptp). A real
  live run needs a Linux host with root and the frozen harness under `/opt/sptb`.
- **Email magic link** needs an SMTP server; **GitHub OAuth** needs an OAuth app. Neither was configured here, so
  e2e covers guest mode only.
- **Docker in this build environment:** Docker Hub rate-limited the base image and the network policy blocks Debian
  mirrors. The image is therefore Alpine-based (no OS packages needed), and `NODE_IMAGE` / `POSTGRES_IMAGE` allow a
  registry mirror. The compose stack was verified here with the image built from `mirror.gcr.io`.
- **Development-replicate archive not ingested:** `recovery_dev_runs_r101.tgz` holds pre-freeze runs that are never
  pooled with the evaluation, and the app does not load it.
