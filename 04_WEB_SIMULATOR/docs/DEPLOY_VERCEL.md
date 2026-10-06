# Vercel deployment

The repository is Vercel-ready, but this completion run did not deploy because no `DATABASE_URL`, `DIRECT_URL`, or Vercel authentication was available in the environment.

## 1. Provision PostgreSQL

Create Neon or Supabase PostgreSQL and retain:

- a pooled runtime URL for `DATABASE_URL`;
- a direct URL for `DIRECT_URL`.

Load the deterministic simulator data once from a trusted workstation:

```powershell
cd 04_WEB_SIMULATOR
$env:DATABASE_URL='<direct PostgreSQL URL>'
$env:DIRECT_URL='<direct PostgreSQL URL>'
npm ci
npm run db:setup
```

## 2. Create the Vercel project

Import `platynom/oran-splane-self-healing-digital-twin`, select the `webapp` production branch after the final PR is merged, and set Root Directory to `04_WEB_SIMULATOR`. `vercel.json` selects Next.js and the correct build command.

Add these variables to Production and Preview:

| Variable | Required value |
|---|---|
| `DATABASE_URL` | Pooled PostgreSQL URL; enable TLS and a low connection limit appropriate to the provider |
| `DIRECT_URL` | Direct PostgreSQL URL |
| `NEXTAUTH_SECRET` | A new cryptographically random value, for example `openssl rand -base64 32` |
| `NEXTAUTH_URL` | Final `https://…` production URL |
| `GITHUB_ID`, `GITHUB_SECRET` | Optional GitHub OAuth credentials |
| `EMAIL_SERVER`, `EMAIL_FROM` | Optional email sign-in settings |

Leave `LIVE_SERVICE_URL` unset: privileged live testbed execution is intentionally disabled on Vercel.

## 3. Deploy and verify

```powershell
vercel login
cd 04_WEB_SIMULATOR
vercel link
vercel env add DATABASE_URL production
vercel env add DIRECT_URL production
vercel env add NEXTAUTH_SECRET production
vercel env add NEXTAUTH_URL production
vercel --prod
```

Open `/`, `/dashboard`, `/api/scene/architecture`, and one `/api/runs/<run-id>` endpoint. Confirm the architecture response reports 111 verified, 0 source-needed, 31 primary-confirmed, and 4 primary-not-accessible claims; then compare dashboard totals with `03_RECOVERY_LOOP_S-PLANE/RESULTS_2026-10-05.md`.
