"use client";
import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { useReducedMotion } from "framer-motion";
import clsx from "clsx";
import { contentStats, getElement } from "@/lib/architecture";

const stats = contentStats();
import { LEVEL_NAME, parseState, select, serializeState, up, ZOOM_TARGET, type Level, type Lls, type SimState } from "@/lib/sim/state";
import { ReplayViewer, type ReplayView, type ScenarioOpt } from "../ReplayViewer";
import { Diagram } from "./Diagram";
import { LoopStages } from "./LoopStages";
import { PacketInspector } from "./PacketInspector";
import { Sentences } from "./Sentences";
import { KindBadge } from "../ui";

export interface HwFault {
  id: string;
  name: string;
}

/** Side-panel content each element offers (lessons, sandbox, catalogue, datasets). */
const ATTACH: Record<string, { panel: string; label: string }[]> = {
  "fh-splane": [{ panel: "lesson:oran-splane", label: "Lesson: O-RAN and the S-plane" }],
  "o-ru": [{ panel: "lesson:oran-splane", label: "Lesson: O-RAN and the S-plane" }],
  "fh-mplane": [{ panel: "lesson:oran-splane", label: "Lesson: O-RAN and the S-plane" }],
  "ptp-exchange": [{ panel: "lesson:ptp", label: "Lesson: PTP" }],
  "gm-a": [{ panel: "lesson:bmca", label: "Lesson: BMCA" }],
  "gm-b": [{ panel: "lesson:bmca", label: "Lesson: BMCA" }, { panel: "lesson:benign", label: "Lesson: benign faults" }],
  "bmca-contest": [{ panel: "lesson:bmca", label: "Lesson: BMCA" }],
  bc: [{ panel: "lesson:benign", label: "Lesson: benign faults" }],
  "bc-standby": [{ panel: "lesson:benign", label: "Lesson: benign faults" }],
  injector: [{ panel: "lesson:attacks", label: "Lesson: attacks" }, { panel: "catalogue", label: "Fault catalogue" }],
  "attack-packets": [{ panel: "lesson:attacks", label: "Lesson: attacks" }, { panel: "catalogue", label: "Fault catalogue" }],
  "port-counts": [{ panel: "lesson:attack-vs-benign", label: "Lesson: attack or benign?" }],
  "hw-faults": [{ panel: "catalogue", label: "Fault catalogue" }],
  "recovery-loop": [{ panel: "sandbox", label: "What-if sandbox (model)" }, { panel: "lesson:loop-limits", label: "Lesson: the loop and its limits" }],
  "smo-nonrt": [{ panel: "lesson:loop-limits", label: "Lesson: the loop and its limits" }],
  "osc-drift": [{ panel: "datasets", label: "Datasets" }],
  "ds-recovery": [{ panel: "datasets", label: "Datasets" }],
  "ds-campaign": [{ panel: "datasets", label: "Datasets" }],
  "ds-pilot": [{ panel: "datasets", label: "Datasets" }],
  "ds-raw-missing": [{ panel: "datasets", label: "Datasets" }],
};
for (const s of ["detect", "localise", "decide", "act", "verify", "rollback"]) ATTACH[`loop-${s}`] = ATTACH["recovery-loop"];

const DS = ["ds-recovery", "ds-campaign", "ds-pilot", "ds-raw-missing", "osc-drift"];

function readPref(k: string) {
  try {
    return localStorage.getItem(k);
  } catch {
    return null;
  }
}
function writePref(k: string, v: string) {
  try {
    localStorage.setItem(k, v);
  } catch {
    /* storage unavailable: preference lasts for this page only */
  }
}

export function Simulator({ scenarios, initial, results, panel, hwFaults, b6Measured = null }: {
  scenarios: ScenarioOpt[];
  initial: SimState;
  results: React.ReactNode; // server-rendered when ?results=1
  panel: React.ReactNode; // server-rendered for ?panel=...
  hwFaults: HwFault[];
  /** B6 is measured off the testbed (two laptops); shown apart from the hardware-only faults. */
  b6Measured?: { id: string; name: string; runs: { id: string; verdict: string }[] } | null;
}) {
  const router = useRouter();
  const reduce = !!useReducedMotion();
  const [s, setS] = useState<SimState>(initial);
  const [zoom, setZoom] = useState<"l1" | "l2" | "splane">(initial.level >= 2 ? "l2" : "l1");
  const [pending, startTransition] = useTransition();
  const [projector, setProjector] = useState(false);
  const [large, setLarge] = useState(false);
  const sRef = useRef(s);
  sRef.current = s;

  // presentation preferences
  useEffect(() => {
    setProjector(readPref("sim-projector") === "1");
    setLarge(readPref("sim-large") === "1");
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = projector ? "projector" : "dark";
    document.documentElement.dataset.text = large ? "large" : "normal";
  }, [projector, large]);

  /** Apply a new state: server-rendered parts (results, panel) go through the router, the rest only rewrites the URL. */
  const apply = useCallback((next: SimState) => {
    const prev = sRef.current;
    setS(next);
    const url = serializeState(next);
    if (next.results !== prev.results || next.panel !== prev.panel) {
      startTransition(() => router.push(url, { scroll: false }));
    } else {
      window.history.replaceState(window.history.state, "", url);
    }
  }, [router]);

  /** Level changes animate the diagram's viewBox; zooming into level 3/4 first flies to the S-plane. */
  const goLevel = useCallback((next: SimState) => {
    const from = sRef.current.level;
    if (next.level <= 2) setZoom(next.level === 2 ? "l2" : "l1");
    if (next.level >= 3 && from <= 2 && !reduce) {
      setZoom("splane");
      setS({ ...sRef.current, focus: next.focus });
      window.setTimeout(() => apply(next), 600);
      return;
    }
    apply(next);
  }, [apply, reduce]);

  const onSelect = useCallback((id: string) => {
    const next = select(sRef.current, id);
    if (next.level !== sRef.current.level) goLevel(next);
    else apply(next);
  }, [apply, goLevel]);

  const goUp = useCallback(() => {
    const next = up(sRef.current);
    if (next.level !== sRef.current.level) goLevel(next);
    else apply(next);
  }, [apply, goLevel]);

  // presenter keys (Space / Left / Right are handled by the replay at levels 3 and 4)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;
      if (el && el.closest("input, select, textarea, [contenteditable=true]")) return;
      const k = e.key.toLowerCase();
      if (e.key === "Escape") {
        e.preventDefault();
        goUp();
      } else if (k === "r") {
        apply({ ...sRef.current, results: !sRef.current.results });
      } else if (k === "p") {
        setProjector((p) => (writePref("sim-projector", p ? "0" : "1"), !p));
      } else if (k === "l") {
        setLarge((p) => (writePref("sim-large", p ? "0" : "1"), !p));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [apply, goUp]);

  // browser back/forward: re-read the URL and remount the replay at the restored time
  const [epoch, setEpoch] = useState(0);
  useEffect(() => {
    const onPop = () => {
      const next = parseState(new URLSearchParams(window.location.search));
      setS(next);
      setZoom(next.level >= 2 ? "l2" : "l1");
      setEpoch((e) => e + 1);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [router]);

  const onReplayChange = useCallback((r: { scenario: string; rep: number; view: ReplayView; t: number }) => {
    const c = sRef.current;
    const t = Math.round(r.t * 10) / 10;
    if (c.scenario === r.scenario && c.rep === r.rep && c.arm === r.view && c.t === t) return;
    apply({ ...c, scenario: r.scenario, rep: r.rep, arm: r.view, t });
  }, [apply]);

  const focusEl = s.focus ? getElement(s.focus) : undefined;
  const levels = ([1, 2, 3, 4] as Level[]).filter((l) => l <= s.level);

  return (
    <div className="flex flex-col gap-4" data-testid="simulator" data-level={s.level}>
      <h1 className="sr-only">O-RAN S-plane architecture simulator</h1>
      <div className="flex flex-wrap items-center gap-2">
        <nav aria-label="Zoom level" data-testid="breadcrumb">
          <ol className="flex flex-wrap items-center gap-1 text-sm">
            {levels.map((l, i) => (
              <li key={l} className="flex items-center gap-1">
                {i > 0 && <span className="text-muted" aria-hidden="true">›</span>}
                {l === s.level ? (
                  <span aria-current="location" className="font-semibold" data-testid={`crumb-${l}`}>
                    {LEVEL_NAME[l]}
                  </span>
                ) : (
                  <button type="button" className="underline" onClick={() => goLevel({ ...sRef.current, level: l, focus: null })} data-testid={`crumb-${l}`}>
                    {LEVEL_NAME[l]}
                  </button>
                )}
              </li>
            ))}
          </ol>
        </nav>
        <div className="ml-auto flex flex-wrap items-center gap-2 text-sm">
          {s.level > 1 && (
            <button type="button" onClick={goUp} className="rounded-md border border-line px-3 py-1.5 hover:bg-surface-2" data-testid="sim-back">
              Back <kbd className="ml-1 text-xs text-muted">Esc</kbd>
            </button>
          )}
          <button type="button" onClick={() => apply({ ...s, results: true })} className="rounded-md border border-line px-3 py-1.5 font-semibold hover:bg-surface-2" data-testid="open-results">
            Results <kbd className="ml-1 text-xs text-muted">R</kbd>
          </button>
          <button type="button" aria-pressed={projector} onClick={() => setProjector((p) => (writePref("sim-projector", p ? "0" : "1"), !p))} className="rounded-md border border-line px-3 py-1.5 hover:bg-surface-2" data-testid="toggle-projector">
            Projector <kbd className="ml-1 text-xs text-muted">P</kbd>
          </button>
          <button type="button" aria-pressed={large} onClick={() => setLarge((p) => (writePref("sim-large", p ? "0" : "1"), !p))} className="rounded-md border border-line px-3 py-1.5 hover:bg-surface-2" data-testid="toggle-large">
            Large text <kbd className="ml-1 text-xs text-muted">L</kbd>
          </button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="flex min-w-0 flex-col gap-3">
          {s.level <= 2 ? (
            <>
              {s.level === 2 && (
                <div role="group" aria-label="Low-layer split configuration" className="flex flex-wrap gap-1 text-sm" data-testid="lls-switch">
                  {(["c1", "c2", "c3", "c4"] as Lls[]).map((l) => {
                    const el = getElement(`lls-${l}`)!;
                    return (
                      <button
                        key={l}
                        type="button"
                        aria-pressed={s.lls === l}
                        onClick={() => apply({ ...s, lls: l, focus: `lls-${l}` })}
                        className={clsx("rounded-md border px-3 py-1.5", s.lls === l ? "border-accent bg-accent-soft font-semibold" : "border-line", !el.lls?.testbed && "text-muted")}
                        data-testid={`lls-${l}`}
                      >
                        LLS-{l.toUpperCase()}
                        {el.lls?.testbed ? " · closest match (reference doc says C2/C3)" : ""}
                      </button>
                    );
                  })}
                </div>
              )}
              <Diagram level={s.level as 1 | 2} lls={s.lls} focus={s.focus} zoom={zoom} onSelect={onSelect} />
              <p className="text-xs text-muted">
                Bright: what this project built and measured (tier 1). Normal: context it depends on (tier 2). Dashed: consequences only (tier 3).
                Faded: outside this project (hover for a description; not selectable). Layout is illustrative.
              </p>
              {s.level === 1 && (
                <div className="flex flex-wrap items-center gap-2 text-sm" data-testid="dataset-strip">
                  <span className="font-semibold">Datasets:</span>
                  {DS.map((id) => (
                    <button key={id} type="button" onClick={() => onSelect(id)} aria-pressed={s.focus === id} className={clsx("rounded-full border px-3 py-1", s.focus === id ? "border-accent bg-accent-soft" : "border-line hover:bg-surface-2")} data-testid={`ds-${id}`}>
                      {getElement(id)?.name.replace("Dataset: ", "")}
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <>
              <ReplayViewer
                key={`${s.level}-${epoch}`}
                scenarios={scenarios}
                initialScenario={s.scenario}
                initialRep={s.rep}
                initialT={s.t}
                initialView={s.arm}
                hotkeys
                onChange={onReplayChange}
                extra={(ctx) =>
                  s.level === 3 ? (
                    <PacketInspector run={ctx.run} t={ctx.t} tab={s.pkt} onTab={(pkt) => apply({ ...sRef.current, pkt, focus: { exchange: "ptp-exchange", bmca: "bmca-contest", attack: "attack-packets", counts: "port-counts" }[pkt] })} />
                  ) : (
                    <LoopStages run={ctx.run} t={ctx.t} onFocus={(id) => apply({ ...sRef.current, focus: id })} />
                  )
                }
              />
              {s.level === 3 && (
                <section aria-label="Faults that need hardware" className="rounded-xl border border-dashed border-line p-3 text-sm" data-testid="hw-faults">
                  <button type="button" className="font-semibold underline" onClick={() => onSelect("hw-faults")}>
                    Not in the replay: faults that need hardware
                  </button>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {hwFaults.map((f) => (
                      <li key={f.id} data-disabled="true" className="cursor-not-allowed rounded-full border border-dashed border-line px-3 py-1 text-muted" data-testid={`hw-${f.id}`}>
                        {f.id} · {f.name} — requires hardware, not measured
                      </li>
                    ))}
                  </ul>
                  {b6Measured && (
                    <p className="mt-3" data-testid="hw-B6-measured">
                      <KindBadge kind="MEASURED" /> {b6Measured.id} · {b6Measured.name}: measured on two laptops (software timestamping):{" "}
                      {b6Measured.runs.map((r, i) => (
                        <span key={r.id} data-testid={`hw-B6-${r.id}`}>
                          {i > 0 && "; "}
                          {r.id} {r.verdict.toLowerCase().replace("_", " ")}
                        </span>
                      ))}
                      . Physical premise only (relative crystal offset between the laptops); not an end-to-end detection test on the testbed.{" "}
                      <button type="button" className="underline" onClick={() => onSelect("osc-drift")} data-testid="hw-B6-open">
                        Open the B6 measurement
                      </button>
                    </p>
                  )}
                </section>
              )}
            </>
          )}
        </div>

        <aside aria-label="Details" className="min-w-0 rounded-xl border border-line bg-surface p-4" data-testid="side-panel">
          {focusEl ? (
            <>
              <div className="flex items-start gap-2">
                <h2 className="text-lg font-semibold" data-testid="side-title">{focusEl.name}</h2>
                <button type="button" onClick={() => apply({ ...s, focus: null })} className="ml-auto rounded border border-line px-2 text-sm" aria-label="Close details">
                  ×
                </button>
              </div>
              <p className="mb-3 text-sm text-muted">{focusEl.role}</p>
              <Sentences id={focusEl.id} />
              <div className="mt-4 flex flex-wrap gap-2">
                {ZOOM_TARGET[focusEl.id] && ZOOM_TARGET[focusEl.id] > s.level && (
                  <button type="button" onClick={() => goLevel({ ...s, level: ZOOM_TARGET[focusEl.id] })} className="rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-accent-ink" data-testid="side-zoom">
                    Zoom in: {LEVEL_NAME[ZOOM_TARGET[focusEl.id]]}
                  </button>
                )}
                {(ATTACH[focusEl.id] ?? []).map((a) => (
                  <button key={a.panel} type="button" onClick={() => apply({ ...s, panel: a.panel })} className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-surface-2" data-testid={`attach-${a.panel}`}>
                    {a.label}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <IntroPanel level={s.level} onOpen={(p) => apply({ ...s, panel: p })} />
          )}
        </aside>
      </div>

      {s.panel && (
        <section aria-label="Panel" className="rounded-xl border border-line bg-surface p-4" data-testid="sim-panel" data-panel={s.panel}>
          <div className="mb-3 flex items-center gap-2">
            <button type="button" onClick={() => apply({ ...s, panel: null })} className="ml-auto rounded-md border border-line px-3 py-1 text-sm" data-testid="panel-close">
              Close panel
            </button>
          </div>
          {pending ? <p role="status">Loading…</p> : panel}
        </section>
      )}

      {s.results && (
        <div role="dialog" aria-modal="true" aria-labelledby="results-title" className="fixed inset-0 z-50 overflow-y-auto bg-black/60 p-2 sm:p-6" data-testid="results-overlay">
          <div className="mx-auto max-w-6xl rounded-xl border border-line bg-bg p-4 sm:p-6">
            <div className="mb-2 flex">
              <button type="button" onClick={() => apply({ ...sRef.current, results: false })} className="ml-auto rounded-md border border-line px-3 py-1 text-sm" data-testid="results-close" autoFocus>
                Close <kbd className="ml-1 text-xs text-muted">Esc</kbd>
              </button>
            </div>
            {pending || !results ? <p role="status" id="results-title">Loading results…</p> : results}
          </div>
        </div>
      )}
      <p className="text-xs text-muted">
        Keys: Space play/pause · ←/→ previous/next recorded event · Esc up a level · R results · P projector · L large text. Every view has its own URL.
        Content: {stats.elements} elements, {stats.sentences} cited sentences: <span data-testid="content-counts">{stats.verified} VERIFIED by an independent audit, {stats.unverified} UNVERIFIED, {stats.sourceNeeded} hidden (source needed)</span>.
      </p>
    </div>
  );
}

function IntroPanel({ level, onOpen }: { level: Level; onOpen: (p: string) => void }) {
  return (
    <div data-testid="side-intro">
      <h2 className="text-lg font-semibold">{LEVEL_NAME[level]}</h2>
      <p className="mt-2 text-sm">
        {level === 1 && "Select a highlighted element to read what it is, with sources. The S-plane, O-RU and O-DU zoom into the open fronthaul; the T-BC and grandmasters zoom into the recorded testbed; the SMO zooms into the recovery loop."}
        {level === 2 && "Switch the low-layer split configuration to see where timing enters the fronthaul. Select the T-BC to open the recorded testbed."}
        {level === 3 && "Play a recorded run. Step from event to event with the arrow keys; open the packet views to see what the frames mean."}
        {level === 4 && "Each stage lights at the time recorded in this run's loop.jsonl. Select a stage for its description."}
      </p>
      <div className="mt-3 flex flex-wrap gap-2 text-sm">
        <button type="button" onClick={() => onOpen("lessons")} className="rounded-md border border-line px-3 py-1.5 hover:bg-surface-2" data-testid="open-lessons">
          Lessons
        </button>
        <button type="button" onClick={() => onOpen("catalogue")} className="rounded-md border border-line px-3 py-1.5 hover:bg-surface-2">
          Fault catalogue
        </button>
        <button type="button" onClick={() => onOpen("sandbox")} className="rounded-md border border-line px-3 py-1.5 hover:bg-surface-2">
          Sandbox (model)
        </button>
        <button type="button" onClick={() => onOpen("datasets")} className="rounded-md border border-line px-3 py-1.5 hover:bg-surface-2">
          Datasets
        </button>
      </div>
    </div>
  );
}
