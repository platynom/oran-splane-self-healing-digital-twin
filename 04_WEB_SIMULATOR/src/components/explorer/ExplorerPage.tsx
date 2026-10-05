"use client";
import dynamic from "next/dynamic";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { Badge } from "../ui";
import { SidePanel } from "./SidePanel";
import { getElement } from "@/lib/architecture";
import { breadcrumb, LEVEL_NAMES, LLS_IDS, MAX_IMPLEMENTED_LEVEL, parseView, select, serializeView, up, type LlsId, type ViewState } from "@/lib/explorerState";
import { useExplorerSettings } from "@/lib/useExplorerSettings";
import type { HoverInfo } from "./Scene";

const Scene = dynamic(() => import("./Scene"), { ssr: false, loading: () => <div className="flex h-full items-center justify-center text-muted" role="status">Loading 3D scene…</div> });

interface Dataset { id: string; name: string; rows: number; frames?: number; kind: string; status: string; note: string; rawCsvPresent?: boolean }

function DatasetStrip() {
  const [ds, setDs] = useState<Dataset[] | null>(null);
  useEffect(() => {
    fetch("/api/scene/datasets").then((r) => r.json()).then((d) => setDs(d.datasets)).catch(() => setDs([]));
  }, []);
  if (!ds) return <p className="text-xs text-muted">Loading dataset status…</p>;
  return (
    <ul className="grid gap-2 text-xs sm:grid-cols-2 xl:grid-cols-4" aria-label="Datasets" data-testid="dataset-strip">
      {ds.map((d) => (
        <li key={d.id} className="rounded-md border border-line bg-surface p-2">
          <span className="font-semibold">{d.name}</span> <Badge tone="ok">{d.kind}</Badge>
          <div className="num">{d.rows} {d.id === "b6" ? "measurements" : "runs"}{d.frames ? ` · ${d.frames.toLocaleString("en-US")} frames` : ""}</div>
          <div className="text-muted">{d.status}</div>
          {d.id === "b6" && !d.rawCsvPresent && <div className="text-warn">raw samples: not in repo</div>}
        </li>
      ))}
    </ul>
  );
}

export function ExplorerPage() {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const view = useMemo(() => parseView(new URLSearchParams(sp.toString())), [sp]);
  const settings = useExplorerSettings(sp.get("q"));
  const { theme, setTheme, text, setText, quality, setQuality, auto } = settings;
  const [hover, setHover] = useState<HoverInfo | null>(null);
  const [listHover, setListHover] = useState<string | null>(null);
  const [gl, setGl] = useState<boolean | null>(null);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    import("./Scene").then((m) => setGl(m.hasWebGL()));
  }, []);

  const go = useCallback((next: ViewState) => router.push(pathname + serializeView(next), { scroll: false }), [router, pathname]);
  const onSelect = useCallback((id: string) => go(select(view, id)), [go, view]);
  const onBack = useCallback(() => go(up(view)), [go, view]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && /^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName)) return;
      if (e.key === "Escape") {
        if (view.focus || view.level > 1) {
          e.preventDefault();
          onBack();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [view, onBack]);

  const hoveredId = hover?.id ?? listHover;
  const hoveredEl = hoveredId ? getElement(hoveredId) : undefined;
  const crumbs = breadcrumb(view);
  const effectiveLevel = Math.min(view.level, MAX_IMPLEMENTED_LEVEL);
  const sceneView: ViewState = { ...view, level: effectiveLevel, focus: view.level > MAX_IMPLEMENTED_LEVEL ? null : view.focus };
  const canUp = !!view.focus || view.level > 1;

  return (
    <div className="flex flex-col gap-4" data-testid="explorer-root">
      <div className="flex flex-wrap items-center gap-3" role="toolbar" aria-label="Explorer controls">
        <nav aria-label="Breadcrumb" data-testid="breadcrumb">
          <ol className="flex flex-wrap items-center gap-1 text-sm">
            {crumbs.map((c, i) => (
              <li key={i} className="flex items-center gap-1">
                {i > 0 && <span aria-hidden="true" className="text-muted">›</span>}
                {i === crumbs.length - 1 ? (
                  <span aria-current="page" className="font-semibold">{c.label}</span>
                ) : (
                  <button type="button" className="underline" onClick={() => go(c.view)}>{c.label}</button>
                )}
              </li>
            ))}
          </ol>
        </nav>
        <button type="button" onClick={onBack} disabled={!canUp} data-testid="back-btn" className="rounded-md border border-line px-3 py-1.5 text-sm font-semibold hover:bg-surface-2 disabled:opacity-40">
          Back (Esc)
        </button>
        <span className="sr-only" data-testid="level-readout" aria-live="polite">
          Level {effectiveLevel}: {LEVEL_NAMES[effectiveLevel]}{view.focus ? `, focus ${view.focus}` : ""}
        </span>
        <div className="ml-auto flex flex-wrap items-center gap-2 text-sm">
          <div className="flex overflow-hidden rounded-md border border-line" role="group" aria-label="Theme">
            {(["dark", "projector"] as const).map((t) => (
              <button key={t} type="button" aria-pressed={theme === t} onClick={() => setTheme(t)} data-testid={`theme-${t}`} className={clsx("px-3 py-1.5", theme === t ? "bg-accent text-accent-ink" : "hover:bg-surface-2")}>
                {t === "dark" ? "Dark" : "Projector"}
              </button>
            ))}
          </div>
          <button type="button" aria-pressed={text === "large"} onClick={() => setText(text === "large" ? "normal" : "large")} data-testid="text-toggle" className={clsx("rounded-md border border-line px-3 py-1.5", text === "large" && "bg-accent text-accent-ink")}>
            Large text
          </button>
          <label className="flex items-center gap-1">
            <span className="text-muted">3D quality</span>
            <select value={quality} onChange={(e) => setQuality(e.target.value as "high" | "medium" | "low")} className="rounded-md border border-line bg-surface px-2 py-1.5" data-testid="quality-select">
              <option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
            </select>
          </label>
          <span className="text-xs text-muted" data-testid="quality-badge">{auto ? "auto-reduces if slow" : "fixed"}</span>
        </div>
      </div>

      {view.level === 2 || view.level > MAX_IMPLEMENTED_LEVEL ? (
        <div role="tablist" aria-label="LLS configuration" className="flex flex-wrap items-center gap-2" data-testid="lls-tabs">
          {LLS_IDS.map((l: LlsId) => (
            <button key={l} role="tab" aria-selected={view.lls === l} onClick={() => go({ ...view, level: 2, lls: l, focus: null })} data-testid={`lls-${l}`} className={clsx("rounded-md border px-3 py-1.5 text-sm font-semibold", view.lls === l ? "border-accent bg-accent text-accent-ink" : "border-line hover:bg-surface-2")}>
              LLS-{l.toUpperCase()}{l === "c3" ? " (testbed)" : ""}
            </button>
          ))}
          <span className="text-sm text-muted">{view.lls === "c3" ? "Configured in the testbed." : "Not configured in the testbed (dimmed)."}</span>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_26rem]">
        <section aria-label="3D explorer" className="relative min-h-[26rem] overflow-hidden rounded-xl border border-line" style={{ height: "min(72vh, 46rem)" }} data-testid="canvas-wrap">
          {gl === false ? (
            <div role="alert" className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center" data-testid="no-webgl">
              <p className="font-semibold">WebGL is not available in this browser.</p>
              <p className="max-w-md text-sm text-muted">The 3D view needs WebGL. All explanations remain available in the panel and the parts list; enable hardware acceleration or try another browser to see the scene.</p>
            </div>
          ) : gl === null ? (
            <div className="flex h-full items-center justify-center text-muted" role="status">Checking graphics support…</div>
          ) : (
            <Scene view={sceneView} theme={theme} quality={quality} autoQuality={auto} onQuality={setQuality} reducedMotion={reduced} hoveredId={hoveredId} onHover={setHover} onSelect={onSelect} />
          )}
          <div className="pointer-events-none absolute bottom-2 left-2 flex flex-wrap gap-1 text-[11px]" aria-hidden="true">
            <span className="rounded px-1.5 py-0.5 font-semibold" style={{ background: "var(--surface)", border: "1px solid var(--accent)" }}>Tier 1 core</span>
            <span className="rounded px-1.5 py-0.5 font-semibold" style={{ background: "var(--surface)", border: "1px solid #6aa8ff" }}>Tier 2 related</span>
            <span className="rounded px-1.5 py-0.5 font-semibold" style={{ background: "var(--surface)", border: "1px solid #ffc15a" }}>Tier 3 influenced</span>
            <span className="rounded px-1.5 py-0.5 font-semibold text-muted" style={{ background: "var(--surface)", border: "1px dashed var(--line)" }}>Dimmed: outside project</span>
          </div>
          <div className="pointer-events-none absolute right-2 top-2 rounded border border-warn px-1.5 py-0.5 text-[11px] font-bold uppercase text-warn" style={{ background: "var(--surface)" }}>
            Illustrative scene · packet motion is not recorded data
          </div>
          {hoveredEl && (
            <div
              role="tooltip"
              data-testid="part-tooltip"
              data-part={hoveredEl.id}
              className="pointer-events-none fixed z-50 max-w-xs rounded-md border border-line bg-surface p-2 text-xs shadow-lg"
              style={hover ? { left: Math.min(hover.x + 14, (typeof window !== "undefined" ? window.innerWidth : 1200) - 280), top: hover.y + 14 } : { left: 24, bottom: 24 }}
            >
              <div className="font-semibold">{hoveredEl.name}</div>
              <div className="text-muted">{hoveredEl.role}</div>
              <div className="mt-1 font-semibold">{hoveredEl.tier === "dimmed" ? "Outside this project (not selectable)" : `Tier ${hoveredEl.tier}: click to select`}</div>
            </div>
          )}
        </section>
        <SidePanel view={view} onSelect={onSelect} onZoom={() => go({ ...view, level: 2 })} onHoverId={setListHover} />
      </div>
      <DatasetStrip />
    </div>
  );
}
