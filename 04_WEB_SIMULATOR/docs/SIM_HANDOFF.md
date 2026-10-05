# 2D architecture simulator: handoff (branch `webapp-sim`, 2026-10-05)

Branch `webapp-sim` was created from `webapp`, and the backend and content work from `webapp-3d` was carried over.
No other branch was modified.

## Verification summary

All results below come from tests and a running app, not from compilation.

| Check | Result |
|---|---|
| Unit tests (`npm test`) | **63 / 63 pass** in 4 files. 17 are new in `tests/unit/sim.test.ts`: URL state, Esc semantics, event sequencing from recorded `loop.jsonl`, citation hiding, dimmed / LLS flags. |
| Playwright (`npx playwright test`) | **23 / 23 pass**. That is 12 existing tests in `e2e/app.spec.ts` (2 adjusted, see below) and 11 new tests in `e2e/sim.spec.ts`. |
| Data fidelity (`npm run fidelity`) | **787 values checked, 0 mismatches.** Output is in `docs/SIM_FIDELITY.json`. |
| Typecheck / lint | `tsc --noEmit` clean; `eslint . --max-warnings 0` clean. |
| `docker compose up --build` from a clean clone of `webapp-sim` | Serves `http://localhost:3000` with the new home. Ingest row-count checks passed in the container. Fidelity (0 / 787) and Playwright (23 / 23) were then re-run against the container. |

The new Playwright tests cover:

- the home render;
- dimmed elements: not clickable, but they show a tooltip;
- a tier-1 click zooms in, and Esc returns;
- T-BC to the level-3 testbed, then the Back button;
- a deep link restores the exact state, including after a reload;
- replay stepping event by event, with loop stages lit at the recorded times (loop and control arms) and the 0.25× speed button present;
- the Results overlay via R / Esc, including 84/96 and the Wilson intervals;
- the projector and large-text toggles, persisted across a reload;
- the datasets panel;
- zero console errors across 13 simulator states;
- axe (WCAG 2.1 AA, serious or critical) in the dark and projector themes.

### Commands and outputs (last run)

```
$ npx vitest run
 Test Files  4 passed (4)
      Tests  63 passed (63)

$ npx playwright test            # against the clean-clone container on :3000
  23 passed (1.9m)

$ npx tsx scripts/fidelity.ts
fidelity: 787 values checked, 0 mismatches

$ docker compose -p simclean -f docker-compose.yml -f <sandbox override> up --build -d   # fresh clone, branch webapp-sim
loading 140 recovery runs
...
extra datasets loaded: campaign evidence 168 (1451909 frames), pilot 40, pilot summaries 2, B6 2; row counts match the source files
done: runs=140 samples=52080 events=12055 campaign=168 faults=22
 ✓ Ready in 821ms
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/   ->  200 (contains data-testid="sim-diagram")
```

#### Sandbox-only Docker setup (not committed)

This container sits behind an HTTPS-intercepting proxy, so the build used a scratch Dockerfile and a compose override:

- the Dockerfile copied in the proxy CA bundle;
- the override set `build.network: host`, `HTTP(S)_PROXY`, and `NO_PROXY=…,registry.npmjs.org`;
- the images came from mirrors: `NODE_IMAGE` / `POSTGRES_IMAGE` pointed at `mirror.gcr.io` because Docker Hub rate-limited the pulls.

On a normal machine, plain `docker compose up --build` is the command. The CA file was never committed.

### Existing tests that were adjusted

Both adjustments are explained in comments in `e2e/app.spec.ts`.

1. **"home loads …".** The home page is now the diagram, so the hypothesis verdicts and the headline medians moved to the Results overlay. The test now asserts the diagram on `/`, and the same verdicts and medians on `/?results=1`.
2. **"a lesson can be completed …".** The brief requires no gamification, so the `/api/progress` XP / progress assertions and the learning-path counter were removed. The test still completes lesson 1 (all steps plus 3/3 on the check), now inside the simulator panel reached through the `/learn/oran-splane` redirect. It also asserts that no "XP" text is shown.

Every other existing test runs unchanged against the redirected routes, including the replay, dashboard, sandbox, catalogue, live, 390 px, reduced-motion, keyboard and axe tests.

## What was built

### Windows fix

- `.gitattributes` has `*.sh text eol=lf` and `Dockerfile text eol=lf`.
- `Dockerfile` runs `sed -i 's/\r$//' scripts/*.sh` before `CMD`.

**Not re-run on this branch:** the CRLF failure reproduction. It was done on `webapp-3d` commit fe28c27:

- without the `sed`, the original "set: illegal option -" error reproduced;
- with the `sed`, the container had 0 CRs and served the app.

The clean clone here was a Linux checkout with 0 CRs in `scripts/*.sh`.

### Home `/` = full O-RAN diagram (2D SVG; no WebGL)

`src/components/sim/Diagram.tsx` and `layout.ts` draw the diagram with relevance lighting by tier:

| Tier | Styling | Elements |
|---|---|---|
| 1 | Bright, thick accent | GM-A, GM-B, T-BC, standby T-BC, O-RU (RU1–3 as T-TSC), S-plane (PTP / SyncE), injector |
| 2 | Normal | O-DU, M-plane, SMO / Non-RT RIC (labelled with its role: "Where a closed loop like ours maps in O-RAN; not implemented there."), GNSS / time source, SyncE, B6 oscillator drift |
| 3 | Dashed "consequence" cards | C-plane, U-plane (both demoted, see the tier log), air interface, UE |
| Dimmed | Opacity 0.4, `role="img"`, not clickable; hover / focus tooltip with name, role and "Outside this project." | Near-RT RIC + xApps, O-CU, 5G Core, O-Cloud |

### Zoom levels

- Clicking an element animates the SVG `viewBox` over 550 ms. Under reduced motion the change is instant.
- A breadcrumb is shown, and a Back button / Esc goes up one level.
- **L1:** the whole O-RAN diagram.
- **L2:** the open fronthaul, with an LLS-C1 … C4 switch.
  - C3 is the testbed's configuration: it is drawn as a solid accent path and labelled "testbed".
  - The others are drawn as dashed warn paths, labelled "not the testbed's configuration".
  - Their explanations come from the `lls-c*` content sentences.
- **L3:** the S-plane testbed.
  - It reuses `ReplayViewer` / `Topology`, extended with 0.25× speed, previous / next recorded event, presenter hotkeys, an initial t / view, a state callback, and an `extra` render slot.
  - The **Inspect packets** overlay (`PacketInspector.tsx`) has four views:
    - the Sync / Follow_Up / Delay_Req / Delay_Resp ladder, labelled with t1–t4. The offset and delay formulas come from the `ptp-exchange` sentences. The ladder is ILLUSTRATIVE.
    - Announce / BMCA: the compared fields in order, plus measured Announce counts per sender in the current bin.
    - attack packets: the port the loop localised the violation to (from `loop.jsonl`), plus frames from attacker senders in the current bin.
    - recorded per-sender × message-type counts on brDN and brUP.
  - Faults that need hardware (A6, A7, B1, B4, B6, selected by the workbook field `testbedRequired = HARDWARE required`) are listed greyed as "requires hardware, not measured".
- **L4:** recovery-loop stages detect / localise / decide / act / verify / rollback (`LoopStages.tsx`).
  - Each stage lights at the recorded time from `src/lib/sim/events.ts`:
    - **detect** = first ATTACK eval at or after T0;
    - **localise** = first eval naming a port;
    - **decide** = act / would_act / escalate;
    - **act** = act;
    - **verify** = verify;
    - **rollback** = rollback.
  - The same data drives it as the replay (scenario / replicate picker, control / loop / side-by-side view, scrubber, 0.25–4×, pause, step).
  - Rollback shows "not in this run" for every run: the 140 runs contain 0 rollback records, and a unit test checks this.

### MEASURED vs ILLUSTRATIVE badges

These appear on each arm panel, on every packet-inspector view and on the loop stages. Every content sentence carries its own kind badge (MEASURED / CONFIGURED / ILLUSTRATIVE / UNKNOWN / REFERENCE).

### Results overlay

It opens from anywhere with R or the Results button.

- `src/components/ResultsContent.tsx` is the former dashboard body, moved; the old `/dashboard` page now renders it.
- It shows H1–H4 plus control integrity, the per-scenario tables and the loop timing.
- Campaign attribution is **84/96 = 0.875**. New Wilson 95% intervals are added for v3 sensitivity 95/96, specificity 47/60 and attribution 84/96.

### Panels

Panels live in the URL as `?panel=`:

- lessons (embedded `LessonPlayer`, with XP and progress recording removed);
- sandbox (unchanged, still labelled MODEL);
- fault catalogue;
- datasets.

Each is offered from the side panel of the diagram elements it belongs to, for example: BMCA → lesson 3, injector → attacks lesson + catalogue, recovery loop → sandbox + loop-limits lesson, ds-* → datasets.

### Redirects (`next.config.ts`, all 307)

Query strings pass through.

| Old route | New target |
|---|---|
| `/learn` | `/?panel=lessons` |
| `/learn/:id` | `/?panel=lesson:<id>` |
| `/replay` | `/?level=3` |
| `/sandbox` | `/?level=4&focus=recovery-loop&panel=sandbox` |
| `/dashboard` | `/?results=1` |
| `/catalogue` | `/?focus=hw-faults&panel=catalogue` |

`/live` and `/about` are kept.

### Navigation

- The header shows Simulator · Live · About.
- The sign-in / user menu and XP are gone from the UI.
- The auth code paths (`/api/auth`, `/signin`, `UserMenu`, `useProgress`, `LearningPath`) remain in the code, unlinked. Nothing was deleted.
- `/api/progress` remains because the Playwright web-server health check uses it.

### Live mode

The page is unchanged. The nav link is hidden when `VERCEL` is set.

### Presenter keys

| Key | Action |
|---|---|
| Space | Play / pause |
| ← / → | Previous / next recorded event |
| Esc | Close overlay → close panel → up a level |
| R | Results |
| P | Projector (high-contrast light theme) |
| L | Large text (125 %) |

- The keys are ignored while a form control has focus.
- The default theme is dark (`html[data-theme="dark"]`).
- Projector and large-text are stored in `localStorage` as per-viewer conveniences.

### Deep links

`src/lib/sim/state.ts` parses and serializes the URL. Every view is a URL built from these fields:

- `level`, `lls`, `focus`, `scenario`, `rep`, `arm` (`side` | `control` | `loop`), `t`, `pkt`, `panel`, `results`.

Behaviour:

- Default fields are omitted, so the home URL stays `/`.
- Malformed values fall back to the defaults.
- Back / forward re-read the URL.

### Backend (from `webapp-3d`, unchanged here)

- **Prisma models:** `CampaignEvidence`, `PilotRun`, `PilotSummary`, `B6Measurement`.
- **Idempotent ingest:** `scripts/ingest-extra.ts`, with row-count checks of 168 evidence rows / 1,451,909 frames, 40 pilot runs, 2 summaries and 2 B6.
- **Read-only GET APIs:** `/api/scene/{architecture,datasets,campaign,pilot,b6}`.

## Data inventory (as loaded and rendered)

| Dataset | Rows | Status shown |
|---|---|---|
| Recovery-loop runs | 140 (52,080 samples, 12,055 events) | pre-registered; replayable at L3 / L4 |
| Detector campaign | 168 runs, 168 with evidence, 1,451,909 PTP frames | corrected archive 2026-09-20 |
| 13 Sep pilot | S11: 10 trials; S15: 30 trials | "independent validation S15 not established" |
| B6 two-laptop drift | run1 20.161 ppm (not established), run2 21.013 ppm (established) | raw per-sample CSVs: **data not in repo** |
| Absent files | listed from `docs/3D_DATA_INVENTORY.md` (ABSENT rows) | shown as "data not in repo"; never approximated |

## Content (`content/architecture.json`)

- **Totals:** 41 elements, 98 sentences, 28 sources (23 openable in this session).
- **Status:** **94 UNVERIFIED, 4 SOURCE_NEEDED, 0 VERIFIED.**
- **SOURCE_NEEDED sentences:** the UI hides all 4 and shows only a count ("1 sentence hidden: source needed"):
  - `o-du.s5`: PTP clock type of the O-DU in LLS-C1 / C2;
  - `fh-mplane.s4`: the `o-ran-sync` YANG name;
  - `fh-cplane.s3`: C-plane behaviour under timing loss;
  - `fh-uplane.s3`: U-plane behaviour under timing loss.
- **Sentence kinds:** REFERENCE 36, CONFIGURED 24, MEASURED 21, UNKNOWN 16, ILLUSTRATIVE 1.

The five recorded checks:

1. **LLS mapping.** The v8 deck and the story guide say LLS-C3. The Testbed Configuration Reference §4 says "models O-RAN LLS-C2/C3". This is **unresolved**; the app treats C3 as the testbed's configuration.
2. **O-DU timing role in LLS-C1 / C2.** Partly verified: the O-DU's membership in the sync chain is verified. Its clock type is SOURCE_NEEDED.
3. **M-plane sync YANG name.** SOURCE_NEEDED. "o-ran-sync" appears only in a project comment, and the O-RAN YANG repository was not reachable.
4. **G.8271 ±1.5 µs.** Supported as an absolute limit at reference point E (G.8271.1). The "TDD" framing is not verified.
5. **WG11 S-plane threats.** The mapping is relayed by project documents (v8 slides 10–12, the Fault Matrix). ETSI TR 104 106 itself was not opened.

Tier log:

- C-plane and U-plane were requested as tier 2 and **demoted to tier 3**. No openable source covers their behaviour under timing loss, and the testbed has no O-DU or radio stack.
- B6 oscillator drift was added as a tier-2 data element.

## Known defects and limits (preserved, not fixed)

1. **B6 ppm storage precision.**
   - What: Postgres holds `relativePpm` as `20.16130672777283`; the source `drift_pair.json` has `20.161306727772832`. The 17th significant digit was lost at ingest (|Δ| ≈ 2e-15 ppm).
   - Why it does not show: the panel renders 3 decimals (the precision `DRIFT_REPORT.md` quotes), and the fidelity check compares at that precision.
   - How it was found: the first fidelity run compared full precision and reported this as 2 mismatches.
2. **Not all explanatory text is in `architecture.json`.**
   - The architecture explanations are in that file.
   - Other text is outside it: UI instructions (intro panel per level, legend line, keyboard help) and short provenance captions in the packet inspector (e.g. "Ladder geometry only; the recorded runs log frame counts per 0.5 s, not individual timestamps").
   - The absorbed lessons, sandbox, catalogue and results keep their own existing text and citations (lesson step `source` lines, workbook tags).
3. **BMCA "field-by-field contest" is partial.** The recovery runs record no per-run Announce field values (clockClass, priority1 …), only frame counts per sender. The view therefore shows:
   - the comparison order named in the cited sentence (priority1 → clockClass → priority2 → clockIdentity; clockAccuracy and variance are not listed because no content sentence names them);
   - the deciding field from the A1 campaign replicate-1 sentence;
   - live, measured Announce counts per sender.
4. **t1–t4 have no recorded per-packet timestamps.** The ladder is ILLUSTRATIVE. The measured `ptp4l` offset / delay example is in the `ptp-exchange` sentences.
5. **Attack-packet counts are attributed by MAC.**
   - A3 replayed frames carry the BC's MAC, so the attacker-sender count is 0 for A3; the replay legend says so.
   - The "recorded injection point" is the port the loop localised the violation to in `loop.jsonl`.
6. **L2 → L3 is not one continuous drawing.** It is a viewBox flight to the S-plane region, followed by a switch to the replay topology.
7. **Deep-link time precision.**
   - The URL `t` has 0.1 s resolution and is written only while paused.
   - Stepping to an event at 1.068 s writes `t=1.1`, so a reload restores 1.1 s, not 1.068 s. The stages lit are the same.
8. **Round trips and gaps in test coverage.**
   - The Results overlay and the panels are server-rendered, so opening one costs a server round trip ("Loading…" is shown meanwhile).
   - Browser back / forward is implemented (via `popstate`) but has no e2e test.
9. **Dimmed elements are faint by design.** Opacity 0.4; axe reports no serious or critical violations on these pages in either theme.
10. **Lighthouse was not run on this branch.**
11. **Unchanged from earlier phases:** software timestamping, `free_running 1`, single-host namespaces, nftables as a switch-ACL stand-in, no digital twin. See `/about` and the footer.

## Files

- **New:**
  - `src/lib/sim/{state,events}.ts`
  - `src/components/sim/{Simulator,Diagram,layout,PacketInspector,LoopStages,Sentences,DatasetsPanel}.tsx|ts`
  - `src/components/ResultsContent.tsx`
  - `src/lib/lessonData.ts`
  - `scripts/fidelity.ts`
  - `tests/unit/sim.test.ts`
  - `e2e/sim.spec.ts`
  - `docs/SIM_FIDELITY.json`
  - this file
- **Modified:**
  - `src/app/{page,layout,globals.css}`
  - `src/app/dashboard/page.tsx`
  - `src/app/learn/[lessonId]/page.tsx`
  - `src/components/{ReplayViewer,LessonPlayer,SiteHeader,ui}.tsx`
  - `next.config.ts`
  - `package.json` (adds `npm run fidelity`)
  - `e2e/app.spec.ts` (2 tests)
