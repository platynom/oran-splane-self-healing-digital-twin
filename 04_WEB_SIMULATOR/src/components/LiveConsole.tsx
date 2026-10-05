"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import { Badge } from "./ui";
import { Topology } from "./Topology";
import { stateAt, type ReplayRun, type ReplaySample, type ReplayEvent } from "@/lib/replay";
import { ALLOW_GM, LEGIT_PARENT } from "@/lib/metrics";

interface Check { name: string; ok: boolean; detail: string }
interface Status { ready: boolean; checks: Check[]; running: string | null; scenarios: string[]; rep_range: [number, number] }

const ident = (s?: string) => (s ? s.split("-")[0].replace(/\./g, "") : null);

/** Streams loop.jsonl / observer.jsonl from the local live service and renders them with the replay components. */
export function LiveConsole({ serviceUrl }: { serviceUrl: string }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [scenario, setScenario] = useState("A1_rogue_master");
  const [arm, setArm] = useState<"control" | "loop">("loop");
  const [rep, setRep] = useState(201);
  const [run, setRun] = useState<string | null>(null);
  const [samples, setSamples] = useState<ReplaySample[]>([]);
  const [events, setEvents] = useState<ReplayEvent[]>([]);
  const [done, setDone] = useState(false);
  const t0Ref = useRef<number | null>(null);
  const roundRef = useRef({ n: 0, seen: new Set<string>() });

  useEffect(() => {
    fetch(`${serviceUrl}/status`).then((r) => r.json()).then(setStatus).catch((e) => setErr(`Live service unreachable at ${serviceUrl}: ${e}`));
  }, [serviceUrl]);

  const start = async () => {
    setErr(null);
    setSamples([]);
    setEvents([]);
    setDone(false);
    t0Ref.current = null;
    roundRef.current = { n: 0, seen: new Set() };
    const r = await fetch(`${serviceUrl}/runs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenario, rep, arm }) });
    const d = await r.json();
    if (!r.ok) {
      setErr(typeof d.detail === "string" ? d.detail : d.detail?.message ?? "refused");
      return;
    }
    setRun(d.run);
    const ws = new WebSocket(`${serviceUrl.replace(/^http/, "ws")}/ws/runs/${d.run}`);
    ws.onmessage = (m) => {
      const msg = JSON.parse(m.data);
      if (msg.stream === "loop") {
        const e = msg.data;
        // T0 is 20 s after the run start; the loop starts at the run start (run_one.py), so T0 ≈ loop start + 20 s
        if (e.kind === "start" && t0Ref.current === null) t0Ref.current = e.t_mono + 20;
        const t = t0Ref.current !== null ? e.t_mono - t0Ref.current : 0;
        setEvents((ev) => [...ev, { t, source: "loop", kind: e.kind, node: null, verdict: e.verdict ?? null, hint: e.hint ?? null, action: e.action ?? null, target: e.target ?? null, ok: e.ok ?? null, detail: e }]);
      } else if (msg.stream === "observer") {
        const o = msg.data;
        if (t0Ref.current === null) return;
        const rr = roundRef.current;
        if (rr.seen.has(o.node)) { rr.n++; rr.seen = new Set(); }
        rr.seen.add(o.node);
        const parent = ident(o.parentPortIdentity), gm = ident(o.grandmasterIdentity);
        const healthy = ["SLAVE", "UNCALIBRATED"].includes(o.portState) && !!parent && LEGIT_PARENT.includes(parent) && !!gm && ALLOW_GM.has(gm);
        setSamples((s) => [...s, { round: rr.n, t: o.t - t0Ref.current!, node: o.node, portState: o.portState ?? null, parent, parentPort: o.parentPortIdentity ?? null, gm, stepsRemoved: null, healthy }]);
      } else if (msg.stream === "done") {
        setDone(true);
        if (msg.timeline?.t0_mono && t0Ref.current !== null) {
          const shift = t0Ref.current - msg.timeline.t0_mono; // exact T0 now known: correct the estimate
          setSamples((s) => s.map((x) => ({ ...x, t: x.t + shift })));
          setEvents((ev) => ev.map((x) => ({ ...x, t: x.t + shift })));
        }
      } else if (msg.stream === "error") setErr(msg.message);
    };
    ws.onerror = () => setErr("WebSocket error");
  };

  const live: ReplayRun | null = useMemo(() => (run ? {
    id: run, scenarioId: scenario, rep, arm, tStartRel: -20, tEndRel: 41, params: {}, nftFinal: "", unhealthyS: 0, restoredAtEnd: false,
    firstActionS: null, firstAttackVerdictS: null, samples, events, packets: [],
  } : null), [run, scenario, rep, arm, samples, events]);
  const now = samples.length ? samples[samples.length - 1].t : -20;
  const state = useMemo(() => (live ? stateAt(live, now) : null), [live, now]);

  return (
    <div className="flex flex-col gap-4">
      {err && <p role="alert" className="rounded-md border border-danger bg-danger-soft p-3 text-danger">{err}</p>}
      {status && (
        <section className="rounded-xl border border-line bg-surface p-4" aria-label="Preflight">
          <h2 className="font-semibold">Preflight {status.ready ? <Badge tone="ok">ready</Badge> : <Badge tone="danger">refusing to run</Badge>}</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {status.checks.map((c) => <li key={c.name} className={c.ok ? "text-ok" : "text-danger"}>{c.ok ? "✓" : "✗"} {c.name}: <span className="text-ink">{c.detail}</span></li>)}
          </ul>
        </section>
      )}
      {status?.ready && (
        <form className="flex flex-wrap items-end gap-3 rounded-xl border border-line bg-surface p-4" onSubmit={(e) => { e.preventDefault(); void start(); }}>
          <label className="flex flex-col text-sm">Scenario
            <select value={scenario} onChange={(e) => setScenario(e.target.value)} className="rounded-md border border-line bg-surface px-3 py-2">{status.scenarios.map((s) => <option key={s}>{s}</option>)}</select>
          </label>
          <label className="flex flex-col text-sm">Arm
            <select value={arm} onChange={(e) => setArm(e.target.value as "control" | "loop")} className="rounded-md border border-line bg-surface px-3 py-2"><option value="loop">loop</option><option value="control">control</option></select>
          </label>
          <label className="flex flex-col text-sm">Replicate ({status.rep_range[0]}–{status.rep_range[1]})
            <input type="number" min={status.rep_range[0]} max={status.rep_range[1]} value={rep} onChange={(e) => setRep(Number(e.target.value))} className="w-28 rounded-md border border-line bg-surface px-3 py-2" />
          </label>
          <button type="submit" disabled={!!run && !done} className="rounded-md bg-accent px-4 py-2 font-semibold text-accent-ink disabled:opacity-50">Start run (about 70 s)</button>
        </form>
      )}
      {live && (
        <section className="rounded-xl border border-line bg-surface p-4">
          <h2 className="font-semibold">{run} {done ? <Badge tone="ok">finished</Badge> : <Badge tone="accent">running</Badge>}</h2>
          <Topology scenarioId={scenario} state={state} title={`Live run ${run}`} />
          <ol className="mt-2 max-h-64 overflow-y-auto text-xs">
            {[...events].reverse().filter((e) => e.kind !== "eval" || e.verdict === "ATTACK").slice(0, 80).map((e, i) => (
              <li key={i} className={clsx("rounded px-2 py-0.5", e.kind === "act" && "bg-accent-soft", e.kind === "escalate" && "bg-warn-soft")}>
                <span className="num font-mono">T0{e.t >= 0 ? "+" : ""}{e.t.toFixed(2)} s</span> {e.kind} {e.verdict ?? ""} {e.hint ?? ""} {e.action ?? ""} {e.target ?? ""}
              </li>
            ))}
          </ol>
          <p className="mt-2 text-xs text-muted">T0 is estimated as loop start + 20 s while running and corrected from timeline.json when the run ends. Live runs are not part of the evaluation and are not written to the database.</p>
        </section>
      )}
    </div>
  );
}
