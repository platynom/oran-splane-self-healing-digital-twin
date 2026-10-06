"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import clsx from "clsx";
import { Topology } from "./Topology";
import { Badge, KindBadge, MeasuredLabel } from "./ui";
import { keyEvents, nextEventTime, prevEventTime } from "@/lib/sim/events";
import {
  actionLabel, DEVICE_LABEL, hintLabel, markers, packetsAt, stateAt, type Device, type ReplayEvent, type ReplayRun, type ReplayState,
} from "@/lib/replay";

export interface ScenarioOpt {
  id: string;
  code: string;
  title: string;
  cls: string;
}

const T_MIN = -20;
const T_MAX = 41;
const T_DEFAULT = -3;
const SPEEDS = [0.25, 0.5, 1, 2, 4];
const REPS = [13, 14, 15, 16, 17];

const cache = new Map<string, Promise<ReplayRun>>();
function fetchRun(id: string): Promise<ReplayRun> {
  let p = cache.get(id);
  if (!p) {
    p = fetch(`/api/runs/${encodeURIComponent(id)}`).then(async (r) => {
      if (!r.ok) throw new Error(`run ${id}: HTTP ${r.status}`);
      return (await r.json()) as ReplayRun;
    });
    p.catch(() => cache.delete(id));
    cache.set(id, p);
  }
  return p;
}

const fmtT = (t: number) => `T0 ${t >= 0 ? "+" : "−"} ${Math.abs(t).toFixed(1)} s`;

export type ReplayView = "side" | "control" | "loop";
export interface ReplayContext {
  run?: ReplayRun;
  runs: { control?: ReplayRun; loop?: ReplayRun };
  arm: "control" | "loop";
  t: number;
  playing: boolean;
}

export function ReplayViewer({
  scenarios, initialScenario, initialRep = 13, lockRep = false, syncUrl = false, compact = false, onEnded, idPrefix = "rp",
  initialT = T_DEFAULT, initialView = "side", hotkeys = false, onChange, extra,
}: {
  scenarios: ScenarioOpt[];
  initialScenario: string;
  initialRep?: number;
  lockRep?: boolean;
  syncUrl?: boolean;
  compact?: boolean;
  onEnded?: () => void;
  idPrefix?: string;
  initialT?: number;
  initialView?: ReplayView;
  /** Space play/pause, Left/Right previous/next recorded event (ignored while a form control has focus). */
  hotkeys?: boolean;
  /** Reported when paused (not every animation frame), for deep links. */
  onChange?: (s: { scenario: string; rep: number; view: ReplayView; t: number }) => void;
  /** Rendered between the transport and the arm panels (packet inspector, loop stages). */
  extra?: (ctx: ReplayContext) => React.ReactNode;
}) {
  const router = useRouter();
  const [scenario, setScenario] = useState(initialScenario);
  const [rep, setRep] = useState(initialRep);
  const [view, setView] = useState<ReplayView>(initialView);
  const [runs, setRuns] = useState<{ control?: ReplayRun; loop?: ReplayRun }>({});
  const [error, setError] = useState<string | null>(null);
  const [t, setT] = useState(initialT);
  const firstLoad = useRef(true);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(2);
  const [ended, setEnded] = useState(false);
  const tRef = useRef(t);
  tRef.current = t;

  useEffect(() => {
    let alive = true;
    setRuns({});
    setError(null);
    setPlaying(false);
    setEnded(false);
    if (!firstLoad.current) setT(T_DEFAULT);
    firstLoad.current = false;
    Promise.all([fetchRun(`${scenario}__r${rep}__control`), fetchRun(`${scenario}__r${rep}__loop`)])
      .then(([c, l]) => alive && setRuns({ control: c, loop: l }))
      .catch((e) => alive && setError(String(e)));
    if (syncUrl) router.replace(`/replay?scenario=${scenario}&rep=${rep}`, { scroll: false });
    return () => {
      alive = false;
    };
  }, [scenario, rep, syncUrl, router]);

  // playback clock
  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      const nt = Math.min(T_MAX, tRef.current + dt * speed);
      setT(nt);
      if (nt >= T_MAX) {
        setPlaying(false);
        setEnded(true);
        onEnded?.();
        return;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, onEnded]);

  const ready = !!(runs.control && runs.loop);
  const togglePlay = useCallback(() => {
    if (!ready) return;
    if (tRef.current >= T_MAX) {
      setT(T_DEFAULT);
      setEnded(false);
    }
    setPlaying((p) => !p);
  }, [ready]);

  const focusArm: "control" | "loop" = view === "control" ? "control" : "loop";
  const evs = useMemo(() => (runs[focusArm] ? keyEvents(runs[focusArm]!) : []), [runs, focusArm]);
  const step = useCallback((dir: 1 | -1) => {
    const nt = dir > 0 ? nextEventTime(evs, tRef.current) : prevEventTime(evs, tRef.current);
    if (nt === null) return;
    setPlaying(false);
    setEnded(false);
    setT(nt);
  }, [evs]);

  useEffect(() => {
    if (!playing) onChange?.({ scenario, rep, view, t });
  }, [playing, scenario, rep, view, t, onChange]);

  useEffect(() => {
    if (!hotkeys) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;
      if (el && el.closest("input, select, textarea, [contenteditable=true]")) return;
      if (e.key === " " && !(el && el.closest("button, a"))) {
        e.preventDefault();
        togglePlay();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        step(1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        step(-1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [hotkeys, togglePlay, step]);

  const bin = Math.floor(t / 0.5);
  const arms = view === "side" ? (["control", "loop"] as const) : ([view] as const);
  const loopMarkers = useMemo(() => (runs.loop ? markers(runs.loop) : []), [runs.loop]);
  const ctrlMarkers = useMemo(() => (runs.control ? markers(runs.control) : []), [runs.control]);
  const sc = scenarios.find((s) => s.id === scenario);

  return (
    <section aria-label="Replay of recorded runs" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col text-sm">
          <span className="mb-1 font-medium">Scenario</span>
          <select
            className="rounded-md border border-line bg-surface px-3 py-2"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            data-testid={`${idPrefix}-scenario`}
          >
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} · {s.title}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-sm">
          <span className="mb-1 font-medium">Replicate</span>
          <select className="rounded-md border border-line bg-surface px-3 py-2" value={rep} disabled={lockRep} onChange={(e) => setRep(Number(e.target.value))} data-testid={`${idPrefix}-rep`}>
            {REPS.map((r) => (
              <option key={r} value={r}>
                r{r}
              </option>
            ))}
          </select>
        </label>
        <fieldset className="flex flex-col text-sm">
          <legend className="mb-1 font-medium">View</legend>
          <div className="flex overflow-hidden rounded-md border border-line" role="group">
            {(["side", "control", "loop"] as const).map((v) => (
              <button
                key={v}
                type="button"
                aria-pressed={view === v}
                onClick={() => setView(v)}
                className={clsx("px-3 py-2", view === v ? "bg-accent text-accent-ink" : "bg-surface hover:bg-surface-2")}
              >
                {v === "side" ? "Side by side" : v === "control" ? "No action (control)" : "Recovery loop"}
              </button>
            ))}
          </div>
        </fieldset>
        <div className="ml-auto">
          <MeasuredLabel />
        </div>
      </div>

      {error && <p role="alert" className="rounded-md border border-danger bg-danger-soft p-3 text-danger">Could not load the recorded runs: {error}</p>}

      <div className="rounded-xl border border-line bg-surface p-3 sm:p-4">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={togglePlay}
            disabled={!ready}
            className="min-w-24 rounded-md bg-accent px-4 py-2 font-semibold text-accent-ink disabled:opacity-50"
            data-testid={`${idPrefix}-play`}
          >
            {playing ? "Pause" : ended ? "Replay" : "Play"}
          </button>
          <div className="flex items-center gap-1 text-sm" role="group" aria-label="Playback speed">
            {SPEEDS.map((s) => (
              <button
                key={s}
                type="button"
                aria-pressed={speed === s}
                onClick={() => setSpeed(s)}
                className={clsx("rounded-md border px-2 py-1 num", speed === s ? "border-accent bg-accent-soft font-semibold" : "border-line")}
                data-testid={`${idPrefix}-speed-${s}`}
              >
                {s}×
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1 text-sm" role="group" aria-label="Step between recorded events">
            <button type="button" onClick={() => step(-1)} disabled={!ready} className="rounded-md border border-line px-2 py-1 disabled:opacity-50" data-testid={`${idPrefix}-prev-event`} title="Previous recorded event (Left arrow)">
              ◀ Event
            </button>
            <button type="button" onClick={() => step(1)} disabled={!ready} className="rounded-md border border-line px-2 py-1 disabled:opacity-50" data-testid={`${idPrefix}-next-event`} title="Next recorded event (Right arrow)">
              Event ▶
            </button>
          </div>
          <output className="num ml-auto font-mono text-sm font-semibold" data-testid={`${idPrefix}-time`} aria-live="off">
            {fmtT(t)}
          </output>
          {ended && (
            <Badge tone="ok">
              <span data-testid={`${idPrefix}-ended`}>Replay finished</span>
            </Badge>
          )}
        </div>
        <Scrubber t={t} setT={(v) => { setT(v); setEnded(false); }} loopMarkers={loopMarkers} ctrlMarkers={ctrlMarkers} idPrefix={idPrefix} />
      </div>

      {extra?.({ run: runs[focusArm], runs, arm: focusArm, t, playing })}

      <div className={clsx("grid gap-4", arms.length === 2 && "xl:grid-cols-2")}>
        {arms.map((arm) => (
          <ArmPanel
            key={arm}
            arm={arm}
            run={runs[arm]}
            t={t}
            bin={bin}
            playing={playing}
            speed={speed}
            scenarioTitle={sc ? `${sc.code} ${sc.title}` : scenario}
            compact={compact}
            idPrefix={idPrefix}
          />
        ))}
      </div>
    </section>
  );
}

function Scrubber({ t, setT, loopMarkers, ctrlMarkers, idPrefix }: {
  t: number;
  setT: (v: number) => void;
  loopMarkers: ReturnType<typeof markers>;
  ctrlMarkers: ReturnType<typeof markers>;
  idPrefix: string;
}) {
  const pct = (x: number) => `${((x - T_MIN) / (T_MAX - T_MIN)) * 100}%`;
  const toneColor = { neutral: "var(--muted)", warn: "var(--warn)", danger: "var(--danger)", ok: "var(--ok)", accent: "var(--accent)" } as const;
  const keyMarkers = loopMarkers.slice(0, 12);
  return (
    <div className="mt-3">
      <div className="relative h-5" aria-hidden="true">
        {keyMarkers.map((m, i) => (
          <span key={`l${i}`} title={`Loop: ${m.label} at ${fmtT(m.t)}`} className="absolute top-0 h-5 w-1 -translate-x-1/2 rounded" style={{ left: pct(m.t), background: toneColor[m.tone] }} />
        ))}
      </div>
      <label className="sr-only" htmlFor={`${idPrefix}-scrub`}>
        Replay time relative to fault onset
      </label>
      <input
        id={`${idPrefix}-scrub`}
        type="range"
        min={T_MIN}
        max={T_MAX}
        step={0.1}
        value={t}
        onChange={(e) => setT(Number(e.target.value))}
        className="w-full accent-[var(--accent)]"
        aria-valuetext={fmtT(t)}
        data-testid={`${idPrefix}-scrubber`}
      />
      <div className="relative h-4" aria-hidden="true">
        {ctrlMarkers.filter((m) => m.kind === "would_act" || m.kind === "onset").map((m, i) => (
          <span key={`c${i}`} title={`Control: ${m.label}`} className="absolute top-0 h-3 w-1 -translate-x-1/2 rounded opacity-70" style={{ left: pct(m.t), background: toneColor[m.tone] }} />
        ))}
      </div>
      <div className="num flex justify-between text-xs text-muted">
        <span>T0 − 20 s (run start)</span>
        <span>T0 (fault onset)</span>
        <span>T0 + 40 s</span>
      </div>
      <p className="mt-1 text-xs text-muted">Markers above the slider: loop arm events. Below: control arm onset and logged would-act decisions (not executed).</p>
    </div>
  );
}

const NODE_NAME: Record<string, string> = { ...DEVICE_LABEL, gma: "GM-A", gmb: "GM-B" };

function describeEvent(e: ReplayEvent): { text: string; tone: "neutral" | "accent" | "ok" | "warn" | "danger" } | null {
  const d = (e.detail ?? {}) as Record<string, unknown>;
  if (e.source === "loop") {
    switch (e.kind) {
      case "act":
        return { text: `ACT: ${actionLabel(e.action)} ${e.target} — ${String(d.reason ?? "")}`, tone: "accent" };
      case "would_act":
        return { text: `WOULD ACT (observe-only, not executed): ${actionLabel(e.action)} ${e.target}`, tone: "neutral" };
      case "verify":
        return { text: `VERIFY ${e.ok ? "passed" : "FAILED"}: ${Object.entries((d.nodes ?? {}) as Record<string, boolean>).map(([k, v]) => `${k.toUpperCase()} ${v ? "ok" : "not ok"}`).join(", ")}`, tone: e.ok ? "ok" : "danger" };
      case "rollback":
        return { text: `ROLLBACK ${e.target}`, tone: "danger" };
      case "escalate":
        return { text: `ESCALATE: ${String(d.reason ?? "")}`, tone: "warn" };
      case "loop_start":
        return { text: "Loop started (warm-up 12 s, window 6 s, persistence 2 of 3)", tone: "neutral" };
      default:
        return null;
    }
  }
  if (e.kind === "port_state" && e.node && ["ru1", "ru2", "ru3", "bc", "bcs", "rogue", "rbc", "bc2"].includes(e.node)) {
    return { text: `ptp4l ${NODE_NAME[e.node] ?? e.node} ${String(d.iface ?? "")}: ${String(d.from_)} → ${String(d.to)} (${String(d.cause)})`, tone: d.to === "FAULTY" ? "danger" : "neutral" };
  }
  if (e.kind === "tx_timeout" && e.node) return { text: `ptp4l ${NODE_NAME[e.node] ?? e.node}: timed out while polling for tx timestamp`, tone: "warn" };
  if (e.kind === "best_master" && e.node && e.node.startsWith("ru")) return { text: `ptp4l ${e.node.toUpperCase()}: selected best master ${String(d.clock)}`, tone: "neutral" };
  return null;
}

function ArmPanel({ arm, run, t, bin, playing, speed, scenarioTitle, compact, idPrefix }: {
  arm: "control" | "loop";
  run?: ReplayRun;
  t: number;
  bin: number;
  playing: boolean;
  speed: number;
  scenarioTitle: string;
  compact: boolean;
  idPrefix: string;
}) {
  const state: ReplayState | null = useMemo(() => (run ? stateAt(run, t) : null), [run, t]);
  const pDn = useMemo(() => (run ? packetsAt(run, bin * 0.5, "dn") : {}), [run, bin]);
  const pUp = useMemo(() => (run ? packetsAt(run, bin * 0.5, "up") : {}), [run, bin]);
  const log = useMemo(() => {
    if (!run) return [];
    const out: { t: number; text: string; tone: "neutral" | "accent" | "ok" | "warn" | "danger"; kind: string }[] = [];
    let lastVerdict: string | null = null;
    for (const e of run.events) {
      if (e.t > t) break;
      if (e.t < -1 && e.source === "ptp4l") continue;
      if (e.source === "loop" && e.kind === "eval") {
        const v = `${e.verdict}${e.hint ? ` (${hintLabel(e.hint)})` : ""}`;
        if (v !== lastVerdict && e.t >= -1) out.push({ t: e.t, text: `Rule verdict: ${v}`, tone: e.verdict === "ATTACK" ? "danger" : e.verdict === "UNKNOWN" ? "warn" : "neutral", kind: "eval" });
        lastVerdict = v;
        continue;
      }
      const d = describeEvent(e);
      if (d) out.push({ t: e.t, ...d, kind: e.kind });
    }
    return out.reverse();
  }, [run, t]);

  const title = `${arm === "control" ? "No action (control)" : "Recovery loop"}: ${scenarioTitle}, replicate ${run?.rep ?? ""}`;
  return (
    <article className="rounded-xl border border-line bg-surface p-3 sm:p-4" aria-label={title} data-testid={`${idPrefix}-arm-${arm}`}>
      <header className="mb-2 flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold">{arm === "control" ? "No action (control)" : "Recovery loop"}</h2>
        {run && <span className="font-mono text-xs text-muted">{run.id}</span>}
        <KindBadge kind="MEASURED" title="RU port states and parents (pmc observer), loop verdicts and actions (loop.jsonl), ptp4l events and per-0.5 s frame counts per sender" />
        <KindBadge kind="ILLUSTRATIVE" title="Packet dot paths, spacing and speed are drawn for legibility; only the per-bin counts are recorded" />
        {state?.verdict && (
          <Badge tone={state.verdict === "ATTACK" ? "danger" : state.verdict === "UNKNOWN" ? "warn" : "neutral"}>
            Rule: {state.verdict}
            {state.hint ? ` (${hintLabel(state.hint)})` : ""}
          </Badge>
        )}
      </header>
      {!run ? (
        <div className="flex h-64 items-center justify-center text-muted" role="status">
          Loading recorded run…
        </div>
      ) : (
        <>
          <Topology
            scenarioId={run.scenarioId}
            state={state}
            packetsDn={pDn}
            packetsUp={pUp}
            binKey={String(bin)}
            binSeconds={0.5 / speed}
            playing={playing}
            title={title}
          />
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <div>
              <table className="w-full text-sm">
                <caption className="sr-only">Radio-unit state from the passive observer</caption>
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-muted">
                    <th className="py-1">RU</th>
                    <th>Port state</th>
                    <th>Parent</th>
                    <th>Healthy</th>
                  </tr>
                </thead>
                <tbody>
                  {(["ru1", "ru2", "ru3"] as const).map((n) => {
                    const v = state?.nodes[n];
                    const parent = v?.parentDevice === "self" ? "itself" : v?.parentDevice ? DEVICE_LABEL[v.parentDevice as Device] : "–";
                    return (
                      <tr key={n} className="border-t border-line">
                        <td className="py-1 font-semibold">{n.toUpperCase()}</td>
                        <td className="font-mono text-xs">{v?.portState ?? "–"}</td>
                        <td title={v?.parentPort ?? ""}>{parent}</td>
                        <td>{v?.portState ? (v.healthy ? <span className="font-semibold text-ok">yes</span> : <span className="font-semibold text-danger">no</span>) : "–"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <dl className="mt-2 grid grid-cols-2 gap-2 text-sm">
                <div className="rounded-md bg-surface-2 p-2">
                  <dt className="text-xs text-muted">RU1/RU2 unhealthy so far</dt>
                  <dd className="num font-semibold" data-testid={`${idPrefix}-${arm}-unhealthy`}>{(state?.unhealthySoFar ?? 0).toFixed(1)} s</dd>
                </div>
                <div className="rounded-md bg-surface-2 p-2">
                  <dt className="text-xs text-muted">Recorded total (T0…T0+40 s)</dt>
                  <dd className="num font-semibold">
                    {run.unhealthyS.toFixed(2)} s · {run.restoredAtEnd ? "restored" : "not restored"}
                  </dd>
                </div>
              </dl>
              {arm === "loop" && /rl-isolate/.test(run.nftFinal) && t >= T_MAX - 0.01 && (
                <p className="mt-2 text-xs text-muted">
                  Final nft ruleset:{" "}
                  <code className="break-all">
                    {run.nftFinal.split("\n").filter((l) => l.includes("rl-isolate")).map((l) => l.trim()).join(" | ")}
                  </code>
                </p>
              )}
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">Event log (loop.jsonl and ptp4l, up to now)</h3>
              <ol className={clsx("mt-1 space-y-1 overflow-y-auto pr-1 text-xs", compact ? "max-h-40" : "max-h-56")} data-testid={`${idPrefix}-log-${arm}`} aria-live="polite" tabIndex={0} aria-label="Event log">
                {log.length === 0 && <li className="text-muted">No events yet.</li>}
                {log.slice(0, 60).map((e, i) => (
                  <li
                    key={`${e.t}-${i}`}
                    className={clsx("rounded px-2 py-1", e.tone === "accent" && "bg-accent-soft", e.tone === "danger" && "bg-danger-soft", e.tone === "warn" && "bg-warn-soft", e.tone === "ok" && "bg-ok-soft")}
                    data-kind={e.kind}
                    data-t={e.t.toFixed(3)}
                  >
                    <span className="num mr-2 font-mono font-semibold">{fmtT(e.t)}</span>
                    {e.text}
                  </li>
                ))}
              </ol>
            </div>
          </div>
          <Legend scenarioId={run.scenarioId} />
        </>
      )}
    </article>
  );
}

function Legend({ scenarioId }: { scenarioId: string }) {
  const items = [
    ["var(--sync)", "Sync / Follow_Up"],
    ["var(--announce)", "Announce"],
    ["var(--delay)", "Delay_Req / Delay_Resp"],
    ["var(--other)", "Other / malformed"],
  ];
  return (
    <p className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
      {items.map(([c, l]) => (
        <span key={l} className="inline-flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: c }} aria-hidden="true" /> {l}
        </span>
      ))}
      <span>Packet dots are drawn from the frame counts per sender in each 0.5 s of the run&apos;s brDN/brUP captures (scaled, capped); frames dropped by the nft rule never reach the bridge capture.</span>
      {scenarioId === "A3_replay" && <span>A3: replayed frames carry the original sender&apos;s MAC, so they appear in the BC&apos;s frame rate (roughly doubled), not as a separate sender.</span>}
      {["A2_sync_spoof", "A5_dos_flood", "C2_malformed", "C3_wholesecond"].includes(scenarioId) && <span>Injector frames are attributed by MAC: frames from unprovisioned MACs, GM MACs seen on brDN, and master-role frames from RU3&apos;s MAC (the injector runs in RU3&apos;s namespace).</span>}
    </p>
  );
}
