"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Badge, ModelLabel } from "./ui";
import {
  isHarmCase, PREREGISTERED, runModel, type CaseInput, type FlowNode, type RecoveryLatency, type SandboxParams,
} from "@/lib/sandboxModel";
import { median } from "@/lib/metrics";
import type { ScenarioOpt } from "./ReplayViewer";

interface Data {
  cases: CaseInput[];
  latency: RecoveryLatency;
  windows: number[];
  ruleWindows: { agreement_w6?: number; ticks_compared_w6?: number; agree_w6?: number; method?: string } | null;
}

const FLOW: { id: FlowNode; label: string; x: number; y: number }[] = [
  { id: "capture", label: "Capture per port", x: 10, y: 65 },
  { id: "detect", label: "Frozen rule (W s)", x: 190, y: 10 },
  { id: "service", label: "Service continuity", x: 190, y: 120 },
  { id: "persist", label: "Persistence K of N", x: 370, y: 10 },
  { id: "tolerate", label: "TOLERATE", x: 370, y: 65 },
  { id: "localise", label: "Localise port", x: 550, y: 10 },
  { id: "guard", label: "Safety guard", x: 550, y: 65 },
  { id: "failover", label: "FAILOVER to standby", x: 550, y: 120 },
  { id: "isolate", label: "ISOLATE port", x: 730, y: 10 },
  { id: "escalate", label: "ESCALATE", x: 730, y: 65 },
];
const EDGES: [FlowNode, FlowNode][] = [
  ["capture", "detect"], ["capture", "service"], ["detect", "persist"], ["persist", "localise"], ["localise", "isolate"],
  ["localise", "guard"], ["guard", "escalate"], ["service", "failover"], ["detect", "tolerate"],
];

export function Sandbox({ scenarios }: { scenarios: ScenarioOpt[] }) {
  const [data, setData] = useState<Data | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [scenario, setScenario] = useState("C1_removal");
  const [rep, setRep] = useState(13);
  const [p, setP] = useState<SandboxParams>(PREREGISTERED);
  useEffect(() => {
    fetch("/api/sandbox").then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then(setData).catch((e) => setErr(String(e)));
  }, []);
  const c = data?.cases.find((x) => x.scenarioId === scenario && x.rep === rep);
  const res = useMemo(() => (c && data ? runModel(c, p, data.latency) : null), [c, p, data]);
  const pre = useMemo(() => (c && data ? runModel(c, PREREGISTERED, data.latency) : null), [c, data]);
  const sweep = useMemo(() => {
    if (!data) return null;
    const all = data.cases.map((x) => ({ x, r: runModel(x, p, data.latency) }));
    const harm = all.filter(({ x }) => x.cls === "benign" || x.cls === "healthy");
    const amb = all.filter(({ x }) => x.cls === "ambiguous");
    const att = all.filter(({ x }) => x.cls === "attack");
    const byAtt = new Map<string, { ctrl: number[]; model: number[] }>();
    for (const { x, r } of att) {
      const m = byAtt.get(x.scenarioId) ?? { ctrl: [], model: [] };
      m.ctrl.push(x.controlUnhealthyS);
      m.model.push(r.predictedUnhealthyS);
      byAtt.set(x.scenarioId, m);
    }
    return {
      benignRunsWithAction: harm.filter(({ r }) => r.disruptive > 0).length,
      benignN: harm.length,
      ambiguousActions: amb.reduce((a, { r }) => a + r.disruptive, 0),
      ambiguousN: amb.length,
      attacksWithAction: att.filter(({ r }) => r.disruptive > 0).length,
      attackN: att.length,
      perAttack: [...byAtt.entries()].map(([sc, v]) => ({ sc, ctrl: median(v.ctrl), model: median(v.model) })),
    };
  }, [data, p]);
  // calibration: at the pre-registered parameters, does the model make the same decisions the loop logged in the control arm?
  const calib = useMemo(() => {
    if (!data) return null;
    let match = 0, total = 0;
    const misses: string[] = [];
    for (const x of data.cases) {
      const r = runModel(x, PREREGISTERED, data.latency);
      const rec = x.controlWouldAct.filter((a) => a.t >= -10);
      total++;
      const same = r.actions.length === rec.length && r.actions.every((a, i) => a.action === rec[i].action && Math.abs(a.t - rec[i].t) < 0.05);
      if (same) match++;
      else misses.push(`${x.scenarioId} r${x.rep}: model ${r.actions.map((a) => `${a.action}@${a.t.toFixed(2)}`).join(", ") || "none"} vs logged ${rec.map((a) => `${a.action}@${a.t.toFixed(2)}`).join(", ") || "none"}`);
    }
    return { match, total, misses };
  }, [data]);

  if (err) return <p role="alert" className="rounded-md border border-danger bg-danger-soft p-3 text-danger">Could not load model inputs: {err}</p>;
  if (!data || !c || !res || !pre || !sweep || !calib)
    return (
      <div className="min-h-[1700px]" aria-busy="true">
        <p role="status" className="text-muted">Loading model inputs from the recorded runs…</p>
      </div>
    );

  const isPre = JSON.stringify(p) === JSON.stringify(PREREGISTERED);
  const harmful = isHarmCase(c.cls) && res.disruptive > 0;
  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-xl border-2 border-dashed border-warn bg-warn-soft p-4" data-testid="sandbox-model-banner">
        <ModelLabel />
        <p className="mt-2 text-sm text-ink">
          This is a deterministic model of the loop&apos;s decision logic, driven by inputs recorded in the <strong>control</strong> run you
          select (rule verdicts per window, Announce gaps, RU health). Its outputs are predictions, not measurements. The closest recorded
          run is always shown next to it.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <form className="flex flex-col gap-4 rounded-xl border border-line bg-surface p-4" onSubmit={(e) => e.preventDefault()} aria-label="Model parameters">
          <label className="flex flex-col text-sm">
            <span className="mb-1 font-medium">Fault (scenario)</span>
            <select value={scenario} onChange={(e) => setScenario(e.target.value)} className="rounded-md border border-line bg-surface px-3 py-2" data-testid="sb-scenario">
              {scenarios.map((s) => (
                <option key={s.id} value={s.id}>{s.code} · {s.title}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-sm">
            <span className="mb-1 font-medium">Recorded replicate used as input</span>
            <select value={rep} onChange={(e) => setRep(Number(e.target.value))} className="rounded-md border border-line bg-surface px-3 py-2">
              {[13, 14, 15, 16, 17].map((r) => <option key={r} value={r}>r{r}</option>)}
            </select>
          </label>
          <label className="flex flex-col text-sm">
            <span className="mb-1 font-medium">Evidence window W: {p.window} s</span>
            <select value={p.window} onChange={(e) => setP({ ...p, window: Number(e.target.value) })} className="rounded-md border border-line bg-surface px-3 py-2" data-testid="sb-window">
              {data.windows.map((w) => <option key={w} value={w}>{w} s{w === 6 ? " (pre-registered)" : ""}</option>)}
            </select>
          </label>
          <fieldset className="text-sm">
            <legend className="mb-1 font-medium">Persistence: act when ≥ K of the last N evaluations are ATTACK</legend>
            <div className="flex gap-3">
              <label className="flex items-center gap-1">K
                <input type="number" min={1} max={p.persistN} value={p.persistK} onChange={(e) => setP({ ...p, persistK: Math.max(1, Math.min(p.persistN, Number(e.target.value))) })} className="w-16 rounded border border-line bg-surface px-2 py-1 num" data-testid="sb-k" />
              </label>
              <label className="flex items-center gap-1">N
                <input type="number" min={p.persistK} max={6} value={p.persistN} onChange={(e) => setP({ ...p, persistN: Math.max(p.persistK, Math.min(6, Number(e.target.value))) })} className="w-16 rounded border border-line bg-surface px-2 py-1 num" />
              </label>
            </div>
          </fieldset>
          <label className="flex flex-col text-sm">
            <span className="mb-1 font-medium">Service-loss threshold: {p.serviceLossS.toFixed(1)} s</span>
            <input type="range" min={0.5} max={20} step={0.5} value={p.serviceLossS} onChange={(e) => setP({ ...p, serviceLossS: Number(e.target.value) })} className="accent-[var(--accent)]" data-testid="sb-loss" />
          </label>
          <label className="flex flex-col text-sm">
            <span className="mb-1 font-medium">…while a maintenance window is open: {p.serviceLossMaintS.toFixed(1)} s</span>
            <input type="range" min={0.5} max={20} step={0.5} value={p.serviceLossMaintS} onChange={(e) => setP({ ...p, serviceLossMaintS: Number(e.target.value) })} className="accent-[var(--accent)]" />
          </label>
          <button type="button" onClick={() => setP(PREREGISTERED)} disabled={isPre} className="rounded-md border border-line px-3 py-2 font-semibold disabled:opacity-50">
            Reset to pre-registered values
          </button>
          <p className="text-xs text-muted">Fixed as in recovery_loop.py: 1 s evaluation period, 12 s warm-up, at most 4 actions, verification deadline 20 s.</p>
        </form>

        <div className="flex flex-col gap-4">
          <section className="rounded-xl border border-line bg-surface p-4" aria-label="Decision flow">
            <h2 className="font-semibold">Decision flow (model path for this case)</h2>
            <svg viewBox="0 0 900 165" className="mt-2 h-auto w-full" role="img" aria-label={`Model path: ${res.path.join(" → ")}`}>
              {EDGES.map(([a, b]) => {
                const A = FLOW.find((f) => f.id === a)!, B = FLOW.find((f) => f.id === b)!;
                const on = res.path.includes(a) && res.path.includes(b);
                return <line key={`${a}-${b}`} x1={A.x + 160} y1={A.y + 17} x2={B.x} y2={B.y + 17} stroke={on ? "var(--accent)" : "var(--line)"} strokeWidth={on ? 3 : 1.5} />;
              })}
              {FLOW.map((f) => {
                const on = res.path.includes(f.id);
                const danger = on && (f.id === "isolate" || f.id === "failover");
                return (
                  <g key={f.id} transform={`translate(${f.x},${f.y})`}>
                    <rect width={160} height={34} rx={6} fill={on ? (danger ? "var(--danger-soft)" : "var(--accent-soft)") : "var(--surface)"} stroke={on ? (danger ? "var(--danger)" : "var(--accent)") : "var(--line)"} strokeWidth={on ? 2.5 : 1.5} />
                    <text x={80} y={22} textAnchor="middle" fontSize={13} fontWeight={on ? 700 : 400} fill="var(--ink)">{f.label}</text>
                  </g>
                );
              })}
            </svg>
          </section>

          <section className="rounded-xl border border-line bg-surface p-4" aria-label="Verdict timeline">
            <h2 className="font-semibold">Rule verdicts at each evaluation tick (W = {p.window} s)</h2>
            <VerdictStrip c={c} W={String(p.window)} actions={res.actions} recorded={c.loop.actions} />
            <p className="mt-2 text-xs text-muted">
              {p.window === 6 ? "Verdicts logged live by the loop in the control run." : `Verdicts from re-running the frozen rule on the control run's recorded brDN capture with a ${p.window} s window (ingest/rule_windows.py).`}{" "}
              Localisation (which port is isolatable) comes from the live 6 s log at each tick for every W.
            </p>
          </section>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border-2 border-dashed border-warn bg-surface p-4" data-testid="sb-model-card">
              <div className="flex items-center gap-2"><ModelLabel>Model</ModelLabel></div>
              <p className="num mt-2 text-2xl font-semibold" data-testid="sb-model-unhealthy">{res.predictedUnhealthyS.toFixed(1)} s</p>
              <p className="text-xs text-muted">predicted RU1/RU2 unhealthy, of 40 s</p>
              <ul className="mt-2 space-y-1 text-sm" data-testid="sb-model-actions">
                {res.actions.length === 0 && <li>No disruptive action</li>}
                {res.actions.map((a, i) => <li key={i}><span className="num font-mono">T0+{a.t.toFixed(2)} s</span> {a.action === "ISOLATE_PTP_AT_PORT" ? `isolate ${a.target}` : "activate standby BC"}</li>)}
                {res.escalations.map((e, i) => <li key={`e${i}`} className="text-warn"><span className="num font-mono">T0+{e.t.toFixed(2)} s</span> escalate: {e.reason}</li>)}
              </ul>
              {harmful && <Badge tone="danger" className="mt-2">Disruptive action on a {c.cls} case</Badge>}
              {res.notes.map((n) => <p key={n} className="mt-2 text-xs text-muted">{n}</p>)}
            </div>
            <div className="rounded-xl border border-line bg-surface p-4">
              <Badge tone="ok">Measured</Badge>
              <p className="num mt-2 text-2xl font-semibold">{c.controlUnhealthyS.toFixed(1)} s</p>
              <p className="text-xs text-muted">recorded control run (no action), same replicate</p>
              <p className="mt-2 text-sm">Logged would-act: {c.controlWouldAct.length ? c.controlWouldAct.map((a) => `${a.action === "ISOLATE_PTP_AT_PORT" ? "isolate" : "failover"} @ T0+${a.t.toFixed(2)} s`).join(", ") : "none"}</p>
            </div>
            <div className="rounded-xl border border-line bg-surface p-4">
              <Badge tone="ok">Measured: closest real run</Badge>
              <p className="num mt-2 text-2xl font-semibold">{c.loop.unhealthyS.toFixed(1)} s</p>
              <p className="text-xs text-muted">recorded loop run {scenario}__r{rep}__loop (pre-registered parameters)</p>
              <p className="mt-2 text-sm">Actions: {c.loop.actions.length ? c.loop.actions.map((a) => `${a.action === "ISOLATE_PTP_AT_PORT" ? `isolate ${a.target}` : "failover"} @ T0+${a.t.toFixed(2)} s`).join(", ") : "none"}</p>
              <Link className="mt-2 inline-block text-sm font-semibold underline" href={`/replay?scenario=${scenario}&rep=${rep}`}>Replay it</Link>
            </div>
          </div>
          {isPre && (
            <p className="text-sm text-muted">
              At the pre-registered parameters this case&apos;s model run predicts {pre.predictedUnhealthyS.toFixed(1)} s against {c.loop.unhealthyS.toFixed(1)} s measured in the loop run.
            </p>
          )}
        </div>
      </div>

      <section className="rounded-xl border border-line bg-surface p-4" aria-labelledby="sweep">
        <div className="flex flex-wrap items-center gap-2">
          <h2 id="sweep" className="font-semibold">Your parameters across all 70 recorded cases</h2>
          <ModelLabel>Model</ModelLabel>
        </div>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg bg-surface-2 p-3" data-testid="sb-sweep-benign">
            <p className="text-xs text-muted">Benign/healthy runs with a disruptive action (H3 criterion: 0)</p>
            <p className="num text-xl font-semibold">{sweep.benignRunsWithAction}/{sweep.benignN}</p>
          </div>
          <div className="rounded-lg bg-surface-2 p-3">
            <p className="text-xs text-muted">Disruptive actions on the ambiguous case (H4 criterion: 0)</p>
            <p className="num text-xl font-semibold">{sweep.ambiguousActions} in {sweep.ambiguousN} runs</p>
          </div>
          <div className="rounded-lg bg-surface-2 p-3">
            <p className="text-xs text-muted">Attack runs where the model acts</p>
            <p className="num text-xl font-semibold">{sweep.attacksWithAction}/{sweep.attackN}</p>
          </div>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[420px] text-sm">
            <thead><tr className="border-b border-line text-left text-xs uppercase tracking-wide text-muted"><th className="py-1">Attack</th><th>Control median (measured)</th><th>Model median</th></tr></thead>
            <tbody>
              {sweep.perAttack.map((r) => (
                <tr key={r.sc} className="border-b border-line"><td className="py-1">{scenarios.find((s) => s.id === r.sc)?.code}</td><td className="num">{r.ctrl.toFixed(1)} s</td><td className="num">{r.model.toFixed(1)} s</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-muted">Try lowering the service-loss threshold below the Announce gaps seen under congestion, or setting K = 1: watch the benign count and the ambiguous case.</p>
      </section>

      <section className="rounded-xl border border-line bg-surface p-4 text-sm" aria-labelledby="calib">
        <h2 id="calib" className="font-semibold">How far to trust the model</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li data-testid="sb-calibration">
            At the pre-registered parameters the model reproduces the loop&apos;s own logged decisions (action, and time within 50 ms) in{" "}
            <strong className="num">{calib.match}/{calib.total}</strong> control runs.
          </li>
          {data.ruleWindows?.agreement_w6 !== undefined && (
            <li>
              Re-running the frozen rule offline on the bridge capture with W = 6 s agrees with the verdicts logged live at{" "}
              <strong className="num">{data.ruleWindows.agree_w6}/{data.ruleWindows.ticks_compared_w6}</strong> ticks ({(100 * data.ruleWindows.agreement_w6).toFixed(1)} %). The
              other windows use the same offline method.
            </li>
          )}
          <li>Recovery after the first action uses the median latency measured in loop runs: isolation {data.latency.ISOLATE_PTP_AT_PORT.toFixed(2)} s, failover {data.latency.ACTIVATE_STANDBY_BC.toFixed(2)} s.</li>
          <li>Not modelled: what an action does to radio units that were not harmed; a second action after the first; any change in the attacker&apos;s behaviour.</li>
        </ul>
        {calib.misses.length > 0 && (
          <details className="mt-2"><summary className="cursor-pointer text-muted">Cases where the model differs from the logged decisions</summary>
            <ul className="mt-1 list-disc pl-5 text-xs">{calib.misses.map((m) => <li key={m}>{m}</li>)}</ul>
          </details>
        )}
      </section>
    </div>
  );
}

function VerdictStrip({ c, W, actions, recorded }: { c: CaseInput; W: string; actions: { t: number; action: string }[]; recorded: { t: number; action: string }[] }) {
  const t0 = -10, t1 = 41;
  const x = (t: number) => ((t - t0) / (t1 - t0)) * 100;
  const color = (v: string) => (v === "ATTACK" ? "var(--danger)" : v === "UNKNOWN" ? "var(--warn)" : v === "BENIGN" ? "var(--ok)" : "var(--line)");
  return (
    <div className="mt-2">
      <div className="relative h-8 rounded bg-surface-2" role="img" aria-label="Verdict per evaluation tick">
        {c.ticks.filter((k) => k.t >= t0).map((k) => (
          <span key={k.t} className="absolute top-1 h-6 w-[1.6%] rounded-sm" style={{ left: `${x(k.t) - 0.8}%`, background: color(k.verdicts[W] ?? "NO_EVIDENCE") }} title={`T0${k.t >= 0 ? "+" : ""}${k.t.toFixed(2)} s: ${k.verdicts[W] ?? "no data"}`} />
        ))}
        <span className="absolute top-0 h-8 w-0.5 bg-ink" style={{ left: `${x(0)}%` }} title="T0" />
      </div>
      <div className="relative mt-1 h-5 text-[10px]">
        {actions.map((a, i) => <span key={`m${i}`} className="absolute -translate-x-1/2 rounded bg-warn px-1 font-semibold text-surface" style={{ left: `${x(a.t)}%` }}>model</span>)}
      </div>
      <div className="relative h-5 text-[10px]">
        {recorded.map((a, i) => <span key={`r${i}`} className="absolute -translate-x-1/2 rounded bg-ok px-1 font-semibold text-surface" style={{ left: `${x(a.t)}%` }}>loop run</span>)}
      </div>
      <div className="flex justify-between text-xs text-muted"><span>T0 − 10 s</span><span>T0</span><span>T0 + 40 s</span></div>
      <p className="mt-1 flex flex-wrap gap-3 text-xs text-muted">
        <span><span className="mr-1 inline-block h-2 w-3 rounded-sm" style={{ background: "var(--danger)" }} />ATTACK</span>
        <span><span className="mr-1 inline-block h-2 w-3 rounded-sm" style={{ background: "var(--ok)" }} />BENIGN</span>
        <span><span className="mr-1 inline-block h-2 w-3 rounded-sm" style={{ background: "var(--warn)" }} />UNKNOWN</span>
      </p>
    </div>
  );
}
