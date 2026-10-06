import Link from "next/link";
import { Badge, Card, MeasuredLabel, Stat } from "@/components/ui";
import { ControlLoopBars } from "@/components/ControlLoopBars";
import { LimitsPanel } from "@/components/LimitsPanel";
import { getAggregates, getCampaignSummary, getHypotheses, getLatencySummary, getScenarios } from "@/lib/data";
import { median, wilson } from "@/lib/metrics";


const CLS_TONE = { attack: "danger", benign: "ok", healthy: "neutral", ambiguous: "warn" } as const;

/** Results: H1-H4, per-scenario tables, campaign attribution. Server component, rendered into the simulator's Results overlay. */
export async function ResultsContent() {
  const [scenarios, aggs, hyps, lat, camp] = await Promise.all([getScenarios(), getAggregates(), getHypotheses(), getLatencySummary(), getCampaignSummary()]);
  const get = (s: string, a: string) => aggs.find((x) => x.scenarioId === s && x.arm === a);
  const pct = (k: number, n: number) => (n ? (k / n).toFixed(3) : "–");
  return (
    <>
      <div className="mb-6 flex flex-col gap-2">
        <h2 id="results-title" className="text-2xl font-semibold tracking-tight">Results</h2>
        <p className="max-w-3xl text-muted">
          All values are computed at request time from the database rows ingested from the recorded archives (140 recovery-loop runs; 168-run
          detection campaign). Nothing in this overlay is modelled.
        </p>
        <div>
          <MeasuredLabel />
        </div>
      </div>

      <section aria-labelledby="hyp" className="mb-10">
        <h2 id="hyp" className="text-xl font-semibold">Pre-registered hypotheses</h2>
        <div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {hyps.map((h) => (
            <Card key={h.id} data-testid={`hyp-${h.id}`} className={h.pass ? "" : "border-danger"}>
              <div className="flex items-center gap-2">
                <Badge tone={h.pass ? "ok" : "danger"}>
                  <span data-testid={`hyp-${h.id}-verdict`}>{h.pass ? "PASS" : "FAILED"}</span>
                </Badge>
                <h3 className="font-semibold">
                  {h.id === "CI" ? "Control integrity" : `${h.id} · ${h.title}`}
                </h3>
              </div>
              <p className="mt-2 text-sm" data-testid={`hyp-${h.id}-summary`}>{h.summary}</p>
              {h.id === "H3" && !h.pass && (
                <div className="mt-3 rounded-md border border-danger/40 bg-danger-soft p-3 text-sm">
                  <p className="font-semibold">Why it failed (RESULTS §3)</p>
                  <p className="mt-1">
                    In B3 replicate 17 the background-traffic generator hit <code>ENOBUFS</code> and the boundary clock hit
                    &nbsp;<code>timed out while polling for tx timestamp</code>; its downstream port went MASTER → FAULTY for about 16 s.
                    Without action RU1/RU2 lost timing for 16.5 s. The loop&apos;s service-continuity channel activated the standby BC at
                    T0 + 5.1 s and the outage was 3.5 s. The action shortened a genuine outage, but the pre-registered criterion was zero
                    disruptive actions on benign runs, so H3 is reported as failed, not re-run.
                  </p>
                  <Link className="mt-2 inline-block font-semibold underline" href="/?level=3&scenario=B3_pdv_congestion&rep=17">
                    Replay B3 r17
                  </Link>
                </div>
              )}
              {h.detail.length > 0 && (
                <details className="mt-2 text-sm">
                  <summary className="cursor-pointer text-muted">Per-scenario detail</summary>
                  <ul className="mt-1 list-disc space-y-0.5 pl-5 text-xs">
                    {h.detail.map((d) => (
                      <li key={d}>{d}</li>
                    ))}
                  </ul>
                </details>
              )}
              {h.id === "H1" && (
                <p className="mt-2 text-xs text-muted">H1 passes trivially for A2, A3, A5, A8 and C2: the attack did not degrade RU1/RU2 in the control arm. There the loop shows containment (H2), not restoration.</p>
              )}
            </Card>
          ))}
        </div>
      </section>

      <section aria-labelledby="timing" className="mb-10">
        <h2 id="timing" className="text-xl font-semibold">Loop timing (attack scenarios, loop arm)</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-3">
          <Stat label="Detection after onset (median)" value={`${lat.detectionMedian.toFixed(2)} s`} sub={`first ATTACK verdict, ${lat.n} loop runs with one`} />
          <Stat label="Action after onset (median)" value={`${lat.actionMedian.toFixed(2)} s`} sub="first executed action (isolate or failover)" />
          <Stat label="Verification after action (median)" value={`${lat.verifyLagMedian.toFixed(2)} s`} sub={`max ${lat.verifyLagMax.toFixed(2)} s; deadline 20 s`} />
        </div>
      </section>

      <section aria-labelledby="per" className="mb-10">
        <h2 id="per" className="text-xl font-semibold">Per scenario: control vs loop</h2>
        <p className="mt-1 text-sm text-muted">
          Median seconds in [T0, T0 + 40 s] during which RU1 or RU2 was not healthy (parent provisioned, GM allow-listed, port SLAVE or
          UNCALIBRATED; PREREGISTRATION.md §4). 5 replicates per arm.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {scenarios.map((s) => {
            const c = get(s.id, "control");
            const l = get(s.id, "loop");
            if (!c || !l) return null;
            const det = l.firstAttackVerdictEach.length ? median(l.firstAttackVerdictEach) : null;
            const act = l.firstActionEach.length ? median(l.firstActionEach) : null;
            return (
              <Card key={s.id} data-testid={`agg-${s.id}`}>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold">
                    {s.code} · {s.title}
                  </h3>
                  <Badge tone={CLS_TONE[s.cls as keyof typeof CLS_TONE] ?? "neutral"}>{s.cls}</Badge>
                </div>
                <div className="mt-3">
                  <ControlLoopBars control={c.unhealthyMedian} loop={l.unhealthyMedian} label={s.title} />
                </div>
                <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                  <dt className="text-muted">Control median (exact)</dt>
                  <dd className="num font-mono" data-testid={`agg-${s.id}-control-median`}>{c.unhealthyMedian.toFixed(2)} s</dd>
                  <dt className="text-muted">Loop median (exact)</dt>
                  <dd className="num font-mono" data-testid={`agg-${s.id}-loop-median`}>{l.unhealthyMedian.toFixed(2)} s</dd>
                  <dt className="text-muted">Restored at end</dt>
                  <dd className="num" data-testid={`agg-${s.id}-restored`}>control {c.restoredAtEnd}/{c.n} · loop {l.restoredAtEnd}/{l.n}</dd>
                  <dt className="text-muted">Executed actions (loop)</dt>
                  <dd className="num" data-testid={`agg-${s.id}-loop-actions`}>{l.disruptiveExecuted}{l.actionKinds.length ? ` · ${l.actionKinds.join(", ")}` : ""}</dd>
                  <dt className="text-muted">Verified</dt>
                  <dd className="num" data-testid={`agg-${s.id}-verified`}>{l.verifyTotal ? `${l.verifyOk}/${l.verifyTotal}` : "–"}</dd>
                  <dt className="text-muted">Would-act logged (control)</dt>
                  <dd className="num">{c.disruptiveWouldAct}</dd>
                  <dt className="text-muted">Runs with escalation (loop)</dt>
                  <dd className="num">{l.runsWithEscalation}/{l.n}</dd>
                  <dt className="text-muted">Detection / action (median)</dt>
                  <dd className="num">{det !== null ? `${det.toFixed(2)} s` : "–"} / {act !== null ? `${act.toFixed(2)} s` : "–"}</dd>
                  <dt className="text-muted">RU3 unhealthy (loop, median)</dt>
                  <dd className="num">{median(l.ru3UnhealthyEach).toFixed(2)} s</dd>
                </dl>
                <Link className="mt-3 inline-block text-sm font-semibold underline" href={`/?level=3&scenario=${s.id}`}>
                  Replay
                </Link>
              </Card>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-muted">
          Known scorer property (RESULTS §5): for the 15 control runs of A1, C1 and C3 the scorer stops at the last observer sample (about
          T0 + 39.55 s), under-counting control-arm harm by about 0.44 s per run. It favours the control; no verdict changes. The values
          here reproduce the project scorer exactly.
        </p>
      </section>

      <section aria-labelledby="camp" className="mb-10">
        <h2 id="camp" className="text-xl font-semibold">Detection campaign (168 runs, 14 scenarios × 12 replicates)</h2>
        <p className="mt-1 text-sm text-muted">Verdicts read from each run&apos;s decision files in the corrected campaign archive; scoring as in evaluate_v4.py.</p>
        <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Attack sensitivity (v3)" value={<span data-testid="camp-v3-sens">{camp.v3.tp}/{camp.v3.nAttack} = {pct(camp.v3.tp, camp.v3.nAttack)}</span>} sub={`pre-frozen base rule: ${camp.base.tp}/${camp.base.nAttack} = ${pct(camp.base.tp, camp.base.nAttack)}`} />
          <Stat label="Benign specificity (v3)" value={`${camp.v3.tn}/${camp.v3.nBenign} = ${pct(camp.v3.tn, camp.v3.nBenign)}`} sub={`misses: ${Object.entries(camp.v3.perScenario).filter(([, v]) => v.expected === "BENIGN" && v.correct < v.n).map(([k, v]) => `${k} ${v.n - v.correct}`).join(", ")}`} />
          <Stat label="Correct abstention" value={`${camp.v3.abstain}/${camp.v3.nUnknown}`} sub="UNKNOWN on the unplanned failover" />
          <Stat label="Fault attribution (v3)" value={<span data-testid="camp-v3-attr">{camp.v3.attributed}/{camp.v3.nAttack} = {pct(camp.v3.attributed, camp.v3.nAttack)}</span>} sub={`base rule: ${camp.base.attributed}/${camp.base.nAttack}`} />
        </div>
        <p className="mt-2 text-sm" data-testid="camp-wilson">
          Wilson 95% intervals (v3):{" "}
          {([["sensitivity", camp.v3.tp, camp.v3.nAttack], ["specificity", camp.v3.tn, camp.v3.nBenign], ["attribution", camp.v3.attributed, camp.v3.nAttack]] as const).map(([l, k, n], i) => {
            const [, lo, hi] = wilson(k, n);
            return (
              <span key={l} className="num" data-testid={`camp-wilson-${l}`}>
                {i > 0 && "; "}
                {l} {k}/{n} [{lo.toFixed(3)}, {hi.toFixed(3)}]
              </span>
            );
          })}
          .
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <caption className="sr-only">Per-scenario correct verdicts, base rule vs v3</caption>
            <thead>
              <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
                <th className="py-2">Scenario</th>
                <th>Expected</th>
                <th>Base rule</th>
                <th>v2</th>
                <th>v3</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => {
                const b = camp.base.perScenario[s.id], v2 = camp.v2.perScenario[s.id], v3 = camp.v3.perScenario[s.id];
                if (!b) return null;
                return (
                  <tr key={s.id} className="border-b border-line">
                    <td className="py-1.5">{s.code} · {s.title}</td>
                    <td>{b.expected}</td>
                    <td className="num">{b.correct}/{b.n}</td>
                    <td className="num">{v2.correct}/{v2.n}</td>
                    <td className={`num font-semibold ${v3.correct < v3.n ? "text-danger" : ""}`}>{v3.correct}/{v3.n}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-muted">
          v2 was frozen before the 168 runs; v3 is a disclosed, additive-only revision (zero runs where the base rule said ATTACK and v3 did
          not). Both v2 and v3 give the same verdicts on all 168 runs.
        </p>
      </section>

      <section aria-labelledby="limits">
        <h2 id="limits" className="text-xl font-semibold">Limits</h2>
        <LimitsPanel />
      </section>
    </>
  );
}
