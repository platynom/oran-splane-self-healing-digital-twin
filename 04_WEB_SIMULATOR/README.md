# 04_WEB_SIMULATOR — S-plane timing security + recovery loop, interactive

Interactive web app for the Samsung PRISM project *O-RAN Open Fronthaul S-Plane Timing Security + Recovery Loop*.
It replays the 140 recorded recovery-loop runs and the 168-run detection campaign from the project archives, offers a
clearly labelled what-if **model** of the loop's decision flow, and teaches the S-plane in seven short lessons.

Everything outside this folder is untouched. The app reads the evidence from
`03_RECOVERY_LOOP_S-PLANE/results/`, `01_CURRENT_SPlane_SelfHealing/.../corrected_final/` and
`00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/*_2026-10-05.xlsx`.

| Mode | What it is | Where it runs |
|---|---|---|
| **Replay** (default) | Recorded runs animated on the testbed topology: control vs loop side by side, scrubber, 0.5×–4× | everywhere (Vercel too) |
| **Sandbox** | Deterministic MODEL of the decision flow on recorded inputs; always shows the closest real run | everywhere |
| **Live** (optional) | Runs the project's own `run_one.py` (linuxptp in namespaces) and streams its logs | localhost, Linux, root only |

Stack: Next.js 15 (App Router) · TypeScript · Tailwind CSS 4 · Prisma 6 + PostgreSQL · NextAuth 4 · Framer Motion ·
custom SVG topology · Vitest · Playwright · axe-core · FastAPI (live service).

---

## 1. Run locally (Docker, one command)

Requirements: Docker with Compose.

```bash
cd 04_WEB_SIMULATOR
docker compose up --build
# open http://localhost:3000
```

On first start the app container pushes the schema to the bundled PostgreSQL and loads the dataset
(`scripts/ingest.ts --if-empty`, about 30 s); later starts skip the load. If Docker Hub rate-limits you, build from a
mirror: `NODE_IMAGE=mirror.gcr.io/library/node:22-alpine POSTGRES_IMAGE=mirror.gcr.io/library/postgres:16-alpine docker compose up --build`.

## 2. Run locally (Node, for development)

Requirements: Node 22, npm 10, Docker (for PostgreSQL) or any PostgreSQL 14+.

```bash
cd 04_WEB_SIMULATOR
cp .env.example .env                       # set NEXTAUTH_SECRET: openssl rand -base64 32
docker compose up -d db                    # PostgreSQL on localhost:5433
npm ci
npm run db:setup                           # prisma db push + load data/derived into PostgreSQL
npm run dev                                # http://localhost:3000
```

### Rebuilding the derived dataset from the raw archives (optional)

`data/derived/*.json.gz` is committed, so the steps above do not need the archives. To regenerate it from the
original evidence (Python 3.10+, `pip install openpyxl`):

```bash
npm run extract                            # ingest/extract.py: sha256-checks the archives, recomputes every run, cross-checks EVALUATION_RL.json / EVALUATION_V4.json
python3 ingest/rule_windows.py             # re-runs the frozen rule on each control run's capture for W = 2..10 s (about 3 min)
npm run db:ingest                          # reload PostgreSQL
```

`extract.py` exits non-zero and writes `DATA_DISCREPANCIES.md` if any recomputed value differs from the published
evaluation. Result of the last run: no discrepancies (see `DATA_DISCREPANCIES.md` for notes).

## 3. Quality gates

```bash
npm run lint                 # ESLint, 0 warnings allowed
npm run typecheck            # tsc --noEmit
npm test                     # Vitest: numbers vs RESULTS_2026-10-05.md, all 140 runs re-scored from the DB, model, logic
npm run build                # production build
npm run start &              # production server on :3000
npx playwright test          # e2e: home, lesson completion, A1 replay, dashboard vs DB, sandbox, a11y (axe), mobile, reduced motion, console errors
cd live && pip install -r requirements.txt && python3 -m pytest -q   # live-service refusal gates
node scripts/screenshots.mjs # regenerate docs/screenshots/
```

Playwright uses the Chromium that matches `@playwright/test` 1.56 (`npx playwright install chromium` if missing).

## 4. Deploy to Vercel with Neon or Supabase

The app is a standard Next.js project; every page is server-rendered on demand from PostgreSQL. No secrets are in git.

1. **Create the database.**
   - *Neon*: create a project; copy the **pooled** connection string (host contains `-pooler`) and the **direct** one.
   - *Supabase*: Project Settings → Database; copy the **Transaction pooler** string (port 6543) and the **Direct**
     string (port 5432).
2. **Load the data once, from your machine** (Vercel never runs the ingest):
   ```bash
   cd 04_WEB_SIMULATOR
   DATABASE_URL="<direct string>" DIRECT_URL="<direct string>" npm run db:setup
   ```
   The loaded database is about 47 MB.
3. **Create the Vercel project.** Import the GitHub repository, set **Root Directory = `04_WEB_SIMULATOR`**, framework
   Next.js (picked up from `vercel.json`).
4. **Environment variables** (Production and Preview):

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | pooled string. Neon: append `?sslmode=require&pgbouncer=true&connect_timeout=15`; Supabase: append `?pgbouncer=true&connection_limit=1` |
   | `DIRECT_URL` | direct string (used by `prisma db push`) |
   | `NEXTAUTH_SECRET` | `openssl rand -base64 32` |
   | `NEXTAUTH_URL` | `https://<your-deployment-domain>` |
   | `GITHUB_ID`, `GITHUB_SECRET` | optional: GitHub OAuth app, callback `https://<domain>/api/auth/callback/github` |
   | `EMAIL_SERVER`, `EMAIL_FROM` | optional: SMTP for magic-link sign-in, e.g. `smtp://user:pass@smtp.example.com:587` |

   `LIVE_SERVICE_URL` must stay unset on Vercel; the Live page shows that it is disabled there (it also checks the
   `VERCEL` variable).
5. **Deploy.** `npm ci` runs `prisma generate`; `npm run build` builds Next.js. Open `/dashboard` and compare with
   `RESULTS_2026-10-05.md`.

Guest mode works without any auth provider: progress is tied to an httpOnly cookie and merged into the account when the
learner signs in later.

## 5. Live mode (optional, Linux + root, never on Vercel)

```bash
# 1. install the frozen harness exactly as 03_RECOVERY_LOOP_S-PLANE/README.md describes, then:
sudo python3 /opt/sptb/recovery/freeze.py --verify          # must print nothing
# 2. start the service
cd 04_WEB_SIMULATOR/live && pip install -r requirements.txt
sudo SPTB=/opt/sptb uvicorn server:app --host 127.0.0.1 --port 8765
# 3. point the app at it
echo 'LIVE_SERVICE_URL="http://127.0.0.1:8765"' >> ../.env && npm run dev
```

The service refuses to run unless the host is Linux, it runs as root, the harness tools are installed and
`freeze.py --verify` passes; it re-checks before every run. It only starts `run_one.py` (every daemon `free_running 1`,
software timestamping, inside namespaces) and never touches the host clock. Live runs use replicate numbers 200–999,
so they can never overwrite the evaluation replicates (13–17) or the development replicate (101).

## 6. Layout

```
ingest/extract.py        archives -> data/derived (sha256 checks, PREREGISTRATION §4 scoring, cross-checks)
ingest/rule_windows.py   frozen rule re-run on recorded captures for W = 2..10 s (sandbox input)
data/derived/            committed derived dataset + provenance.json
prisma/schema.prisma     evidence tables (Scenario, Run, Sample, Event, PacketSeries, RuleWindow, ...) and learner tables
scripts/ingest.ts        loads data/derived into PostgreSQL and recomputes every metric from the stored rows
src/lib/metrics.ts       PREREGISTRATION §4 metrics (port of analyse.py)    src/lib/hypotheses.ts   H1–H4 + control integrity
src/lib/replay.ts        replay state = lookup into recorded series         src/lib/sandboxModel.ts the MODEL
src/lib/lessons.ts       lesson content with citations                       src/components/...      UI
live/server.py           FastAPI live service (+ test_server.py)
tests/unit, e2e          Vitest and Playwright suites
docs/screenshots, docs/lighthouse
```
