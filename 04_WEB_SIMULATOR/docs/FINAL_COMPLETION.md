# Final simulator completion

Date: 2026-10-06

Branch: `webapp-sim-final`

Base: `webapp-sim` at `b3996a3`

## Outcome

The audited 2D O-RAN S-plane simulator is complete for merge into `webapp`. It now exposes primary-source verification in both the architecture API and the sentence UI, restores the four formerly hidden claims only after official-source confirmation, resolves the `stepsRemoved` ambiguity from raw packets, and preserves the frozen experiment artifacts.

## Primary-source verification

Every VERIFIED sentence derived from an external standard now has a `citation.primary` record with `checked`, `result`, `quote`, `url`, and `clause`.

| Result | Count |
|---|---:|
| VERIFIED sentences | 111 |
| SOURCE_NEEDED | 0 |
| Primary CONFIRMED | 31 |
| Primary CONFLICTS | 0 |
| Primary NOT_ACCESSIBLE | 4 |

The four NOT_ACCESSIBLE entries are three IEEE 1588-derived statements whose licensed primary text was not available in this environment and the explanatory IEEE semantics used in the `stepsRemoved` finding. They remain transparent rather than being presented as independently opened primary text. A green `PRIMARY ✓` marker and tooltip identify CONFIRMED claims in the UI.

The four formerly hidden claims (`o-du.s5`, `fh-mplane.s4`, `fh-cplane.s3`, and `fh-uplane.s3`) were confirmed against opened official ETSI/O-RAN publications and are now rendered. An incorrect LLS-C1 timing citation was corrected from `T-FRHAUL-01` to `T-SPLANE-01`.

## B6 raw-data search

The exact B6 CSV filenames were searched recursively in the complete local project tree, `C:\Users\Admin\Downloads`, and all Git refs/history. No raw B6 CSV was found, so no unsupported curve was added.

| Run | Side | Expected filename | Recorded SHA-256 |
|---|---|---|---|
| 1 | A | `laptopA_20261002-175858_f0886ca920.csv` | `5443796d015ce5023789ceb7610fe9159cdc769677df424edd521f748fe26154` |
| 1 | B | `laptopB_20261002-175545_b212d7a623.csv` | `71a34ccc5fe29fbfb25cc7fcd592487e4dbf2b60692bc0dafe9c8bbda43aaa38` |
| 2 | A | `laptopA_20261002-211329_92214ce7bb.csv` | `37efb32541b9b64b1d89777cae37f52337ebeb4d6e03ae0dacfb384c117429be` |
| 2 | B | `laptopB_20261002-211401_5897fbe2bc.csv` | `68155ad5830dc43096bb026fae349069bb7560fbb38a6dca8e0c95736fbf332f` |

## `stepsRemoved` resolution

The reproducible archive audit decoded 555,335 Announce packets. Legitimate GMs transmit `stepsRemoved=0`; the primary BC relays Announce with `stepsRemoved=1` (62,620 packets), while an RU increments the received value for its local `currentDS`, yielding `2`. Therefore the apparent `1` versus `2` conflict describes wire/sender state versus receiver dataset state. Full evidence and reproduction instructions are in [`STEPS_REMOVED_FINDING.md`](STEPS_REMOVED_FINDING.md).

## Verification

| Check | Final result |
|---|---:|
| TypeScript typecheck | pass |
| ESLint | pass |
| Production build | pass |
| Unit tests | 69 / 69 pass |
| Playwright | 25 / 25 pass |
| Fidelity | 787 checked, 0 mismatches |
| Database ingest | 140 runs, 52,080 samples, 12,055 events, 168 campaign rows, 22 faults |

The automated browser suite exercised the running application, including the new primary marker and the restored M-plane sentence.

## Docker and fresh-checkout limitation

The requested `docker compose down -v` was issued before `docker compose up --build`. Compose could not start because Docker Desktop failed before project containers were created. Docker's host log reports a locked internal socket at:

`C:\Users\Admin\AppData\Local\Docker\run\sailor-ingest.sock`

The failing operation was an internal rename to `sailor-ingest.sock.stale` with Windows reporting that the file could not be accessed by the system. Docker Desktop and WSL were stopped and one exact-target cleanup was attempted, but Windows continued to hold the socket. This is a host-runtime blocker, not an application or Compose failure. No fresh-compose pass is claimed. In lieu of that unavailable check, the same ingest, build, unit, browser and fidelity checks were completed against an isolated local PostgreSQL 18 cluster.

## Deployment status

No production deployment was attempted because the environment contains no `DATABASE_URL`, `DIRECT_URL`, or Vercel authentication. Exact Neon/Supabase and Vercel configuration, import, environment-variable, migration, deployment and verification steps are in [`DEPLOY_VERCEL.md`](DEPLOY_VERCEL.md). Privileged live testbed execution remains disabled on Vercel.

## Reproducible audit utilities

- `ingest/add_primary_citations.py` reapplies and validates the primary-source metadata.
- `ingest/audit_steps_removed.py` decodes the archived packet captures and prints every sender/grandmaster/value/count tuple.

No frozen experiment artifact was modified.
