"use client";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { Badge } from "../ui";
import { CitationChip } from "./Citation";
import { architecture, getElement, hiddenSentenceCount, isClickable, renderableSentences, type Element, type Kind } from "@/lib/architecture";
import { LEVEL_NAMES, MAX_IMPLEMENTED_LEVEL, TESTBED_LLS, type ViewState } from "@/lib/explorerState";
import { drawnIds } from "@/lib/sceneLayout";

const KIND_TONE: Record<Kind, "ok" | "accent" | "warn" | "danger" | "neutral"> = {
  MEASURED: "ok", CONFIGURED: "accent", ILLUSTRATIVE: "warn", UNKNOWN: "danger", REFERENCE: "neutral",
};
const TIER_LABEL: Record<string, string> = { "1": "Tier 1 · core", "2": "Tier 2 · related", "3": "Tier 3 · influenced", dimmed: "Outside this project" };

interface B6Row { id: string; verdict: string; relativePpm: number; ci95: number[]; halfwidthPpm: number }

function B6Card() {
  const [rows, setRows] = useState<B6Row[] | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    fetch("/api/scene/b6").then((r) => r.json()).then((d) => setRows(d.measurements)).catch(() => setErr(true));
  }, []);
  if (err) return <p className="text-sm text-danger">Could not load the B6 figures.</p>;
  if (!rows) return <p className="text-sm text-muted">Loading B6 figures…</p>;
  return (
    <div className="rounded-lg border border-line p-3" data-testid="b6-card">
      <Badge tone="ok">MEASURED · derived analysis output</Badge>
      <table className="mt-2 w-full text-sm">
        <thead><tr className="text-left text-xs text-muted"><th>Run</th><th>Relative offset</th><th>95 % interval</th><th>Verdict</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-line">
              <td>{r.id}</td>
              <td className="num">{r.relativePpm >= 0 ? "+" : ""}{r.relativePpm.toFixed(3)} ppm</td>
              <td className="num">[{r.ci95.map((x) => x.toFixed(3)).join(", ")}]</td>
              <td className={r.verdict === "ESTABLISHED" ? "text-ok" : "text-danger"}>{r.verdict.replace("_", " ").toLowerCase()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted">Raw per-sample files are not in the repository, so no time series is drawn.</p>
    </div>
  );
}

function ElementCard({ el, fromLevel, onZoom }: { el: Element; fromLevel: number; onZoom?: () => void }) {
  const sents = renderableSentences(el);
  const hidden = hiddenSentenceCount(el);
  return (
    <article aria-labelledby={`el-${el.id}`} data-testid={`card-${el.id}`} className={clsx("rounded-xl border bg-surface p-4", el.consequence_card ? "border-warn" : "border-line")}>
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={el.tier === 1 ? "accent" : el.tier === 2 ? "neutral" : el.tier === 3 ? "warn" : "neutral"}>{TIER_LABEL[String(el.tier)]}</Badge>
        {el.consequence_card && <Badge tone="warn">Consequence card</Badge>}
      </div>
      <h2 id={`el-${el.id}`} className="mt-2 text-lg font-semibold">{el.name}</h2>
      <p className="text-sm text-muted">{el.role}</p>
      <ul className="mt-3 space-y-3">
        {sents.map((s) => (
          <li key={s.id} className="text-sm" data-testid={`sentence-${s.id}`} data-status={s.citation.status}>
            <Badge tone={KIND_TONE[s.kind]} className="mr-2 align-middle">{s.kind}</Badge>
            <span>{s.text}</span>
            <CitationChip citation={s.citation} sentenceId={s.id} />
            <Badge tone="warn" className="ml-1 align-middle">{s.citation.status}</Badge>
          </li>
        ))}
      </ul>
      {hidden > 0 && (
        <p className="mt-3 text-xs text-muted" data-testid={`hidden-${el.id}`}>
          {hidden} statement{hidden === 1 ? " is" : "s are"} hidden until a source is found.
        </p>
      )}
      {el.id === "osc-drift" && <div className="mt-3"><B6Card /></div>}
      {onZoom && fromLevel === 1 && el.levels.includes(2) && (
        <button type="button" onClick={onZoom} className="mt-3 rounded-md border border-line px-3 py-2 text-sm font-semibold hover:bg-surface-2">
          Show in the open fronthaul (level 2)
        </button>
      )}
    </article>
  );
}

export function SidePanel({ view, onSelect, onZoom, onHoverId }: {
  view: ViewState;
  onSelect: (id: string) => void;
  onZoom: () => void;
  onHoverId: (id: string | null) => void;
}) {
  const focusEl = view.focus ? getElement(view.focus) : undefined;
  const llsEl = view.level === 2 ? getElement(`lls-${view.lls}`) : undefined;
  const ids = drawnIds(Math.min(view.level, MAX_IMPLEMENTED_LEVEL), view.lls);
  const parts = ids.map((id) => getElement(id)!).filter(Boolean);
  return (
    <aside aria-label="Details" data-testid="side-panel" className="flex flex-col gap-4">
      {view.level > MAX_IMPLEMENTED_LEVEL && (
        <div role="status" className="rounded-xl border border-warn bg-warn-soft p-4 text-sm" data-testid="level-pending">
          Level {view.level} ({LEVEL_NAMES[view.level]}) is planned for a later phase. Showing the open fronthaul instead.
        </div>
      )}
      {focusEl ? (
        <ElementCard el={focusEl} fromLevel={view.level} onZoom={onZoom} />
      ) : llsEl ? (
        <ElementCard el={llsEl} fromLevel={view.level} />
      ) : (
        <div className="rounded-xl border border-line bg-surface p-4 text-sm">
          <h2 className="text-lg font-semibold">Whole O-RAN</h2>
          <p className="mt-1">Select a lit part in the scene or in the list below. Bright parts are part of this project; dimmed parts are outside it. The camera flies to each part and stays within a limited orbit.</p>
        </div>
      )}
      {view.level === 2 && view.lls !== TESTBED_LLS && (
        <div className="rounded-xl border border-danger bg-danger-soft p-3 text-sm" role="note">
          This configuration is shown for comparison only. The testbed uses LLS-{TESTBED_LLS.toUpperCase()}.
        </div>
      )}
      <section aria-labelledby="parts-h" className="rounded-xl border border-line bg-surface p-4">
        <h2 id="parts-h" className="text-sm font-semibold uppercase tracking-wide text-muted">Parts in this view</h2>
        <ul className="mt-2 grid gap-1" data-testid="parts-list">
          {parts.map((e) => {
            const click = isClickable(e);
            return (
              <li key={e.id}>
                {click ? (
                  <button
                    type="button"
                    onClick={() => onSelect(e.id)}
                    onMouseEnter={() => onHoverId(e.id)}
                    onMouseLeave={() => onHoverId(null)}
                    onFocus={() => onHoverId(e.id)}
                    onBlur={() => onHoverId(null)}
                    aria-pressed={view.focus === e.id}
                    data-testid={`part-item-${e.id}`}
                    className={clsx("flex w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-left text-sm", view.focus === e.id ? "border-accent bg-accent-soft" : "border-line hover:border-accent")}
                  >
                    <span>{e.name}</span>
                    <span className="text-xs text-muted">{TIER_LABEL[String(e.tier)]}</span>
                  </button>
                ) : (
                  <div
                    tabIndex={0}
                    role="group"
                    aria-label={`${e.name}: outside this project, not selectable`}
                    onMouseEnter={() => onHoverId(e.id)}
                    onMouseLeave={() => onHoverId(null)}
                    onFocus={() => onHoverId(e.id)}
                    onBlur={() => onHoverId(null)}
                    data-testid={`part-item-${e.id}`}
                    data-dimmed="true"
                    className="flex items-center justify-between gap-2 rounded-md border border-dashed border-line px-3 py-2 text-sm text-muted"
                  >
                    <span>{e.name}</span>
                    <span className="text-xs">outside this project</span>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </section>
      <details className="rounded-xl border border-line bg-surface p-4 text-sm" data-testid="checks">
        <summary className="cursor-pointer font-semibold">Verification notes ({architecture.checks.length} explicit checks)</summary>
        <ul className="mt-2 space-y-2">
          {architecture.checks.map((c) => (
            <li key={c.id}>
              <span className="font-semibold">{c.question}</span> <span className="text-muted">{c.result}</span>
              <p className="text-xs">{c.finding}</p>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-muted">{architecture.status_note}</p>
      </details>
    </aside>
  );
}
