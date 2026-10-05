"use client";
import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { ModelLabel } from "../ui";

/**
 * Simplified IEEE 1588 default data-set comparison: fields compared in order, smaller wins, first
 * difference decides. G.8275.1 (which the testbed ran) uses the alternate BMCA with localPriority and
 * per-port notSlave; this widget is an illustration of the comparison idea, not of that profile's algorithm.
 */
export interface ClockDS {
  key: string;
  name: string;
  priority1: number;
  clockClass: number;
  clockAccuracy: number;
  variance: number;
  priority2: number;
  identity: string;
}

export const FIELDS: { k: keyof ClockDS; label: string }[] = [
  { k: "priority1", label: "priority1" },
  { k: "clockClass", label: "clockClass" },
  { k: "clockAccuracy", label: "clockAccuracy" },
  { k: "variance", label: "offsetScaledLogVariance" },
  { k: "priority2", label: "priority2" },
  { k: "identity", label: "clockIdentity" },
];

/** Returns the winner and the field that decided it. */
export function bmcaCompare(a: ClockDS, b: ClockDS): { winner: ClockDS; field: string } {
  for (const f of FIELDS) {
    const va = a[f.k], vb = b[f.k];
    if (va !== vb) return { winner: va < vb ? a : b, field: f.label };
  }
  return { winner: a, field: "identical" };
}

export function bmcaBest(cands: ClockDS[]): { winner: ClockDS; field: string } | null {
  if (!cands.length) return null;
  let best = cands[0], field = "only candidate";
  for (const c of cands.slice(1)) {
    const r = bmcaCompare(best, c);
    best = r.winner;
    field = r.field;
  }
  return { winner: best, field };
}

/** clockClass values listed for G.8275.1 in STANDARDS_EVIDENCE.md s3 (plus 52, out-of-spec holdover in the benign catalogue). */
export const LEGAL_CLASSES = [6, 7, 52, 135, 140, 150, 160, 165, 248];

const INITIAL: ClockDS[] = [
  { key: "gma", name: "GM-A (allow-listed)", priority1: 128, clockClass: 248, clockAccuracy: 254, variance: 65535, priority2: 128, identity: "020000fffe00000a" },
  { key: "gmb", name: "GM-B (allow-listed)", priority1: 128, clockClass: 248, clockAccuracy: 254, variance: 65535, priority2: 129, identity: "020000fffe00000b" },
  { key: "rogue", name: "Rogue (not on allow-list)", priority1: 128, clockClass: 248, clockAccuracy: 254, variance: 65535, priority2: 128, identity: "020000fffe000042" },
];

export function BmcaArena({ onDone }: { onDone: () => void }) {
  const [clocks, setClocks] = useState(INITIAL);
  const [arena, setArena] = useState<string[]>(["gma"]);
  const [drag, setDrag] = useState<string | null>(null);
  const inArena = clocks.filter((c) => arena.includes(c.key));
  const res = useMemo(() => bmcaBest(inArena), [inArena]);
  const rogue = clocks.find((c) => c.key === "rogue")!;
  const legalRogue = rogue.priority1 === 128 && LEGAL_CLASSES.includes(rogue.clockClass);
  const solved = !!res && res.winner.key === "rogue" && arena.length >= 2 && legalRogue;
  useEffect(() => {
    if (solved) onDone();
  }, [solved, onDone]);

  const set = (key: string, k: keyof ClockDS, v: number) => setClocks((cs) => cs.map((c) => (c.key === key ? { ...c, [k]: v } : c)));
  const add = (key: string) => setArena((a) => (a.includes(key) ? a : [...a, key]));
  const remove = (key: string) => setArena((a) => a.filter((k) => k !== key));

  const card = (c: ClockDS, where: "bench" | "arena") => (
    <div
      key={c.key}
      draggable
      onDragStart={() => setDrag(c.key)}
      onDragEnd={() => setDrag(null)}
      className={clsx("rounded-lg border bg-surface p-3", res?.winner.key === c.key && where === "arena" ? "border-ok ring-2 ring-ok" : "border-line", c.key === "rogue" && "border-dashed")}
      aria-label={`${c.name} clock`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold">{c.name}</span>
        {where === "bench" ? (
          <button type="button" onClick={() => add(c.key)} className="rounded border border-line px-2 py-0.5 text-xs" data-testid={`bmca-add-${c.key}`}>
            Add to arena
          </button>
        ) : (
          <button type="button" onClick={() => remove(c.key)} className="rounded border border-line px-2 py-0.5 text-xs">
            Remove
          </button>
        )}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
        <label className="flex flex-col">
          priority1
          <input type="number" min={0} max={255} value={c.priority1} onChange={(e) => set(c.key, "priority1", Number(e.target.value))} className="rounded border border-line bg-surface px-1 py-0.5 num" data-testid={`bmca-${c.key}-priority1`} />
        </label>
        <label className="flex flex-col">
          clockClass
          <select value={c.clockClass} onChange={(e) => set(c.key, "clockClass", Number(e.target.value))} className="rounded border border-line bg-surface px-1 py-0.5" data-testid={`bmca-${c.key}-clockClass`}>
            {[...new Set([...LEGAL_CLASSES, c.clockClass])].sort((a, b) => a - b).map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
            <option value={1}>1 (not in the G.8275.1 table)</option>
          </select>
        </label>
        <label className="flex flex-col">
          priority2
          <input type="number" min={0} max={255} value={c.priority2} onChange={(e) => set(c.key, "priority2", Number(e.target.value))} className="rounded border border-line bg-surface px-1 py-0.5 num" data-testid={`bmca-${c.key}-priority2`} />
        </label>
        <div className="flex flex-col">
          clockIdentity
          <span className="font-mono">{c.identity}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      <ModelLabel>Simplified BMCA illustration</ModelLabel>
      <div className="mt-3 grid gap-4 lg:grid-cols-2">
        <section aria-label="Bench" onDragOver={(e) => e.preventDefault()} onDrop={() => drag && remove(drag)} className="rounded-xl border border-line bg-surface-2 p-3">
          <h3 className="mb-2 text-sm font-semibold">Bench (drag a clock into the arena)</h3>
          <div className="flex flex-col gap-2">{clocks.filter((c) => !arena.includes(c.key)).map((c) => card(c, "bench"))}</div>
        </section>
        <section aria-label="Election arena" onDragOver={(e) => e.preventDefault()} onDrop={() => drag && add(drag)} className="rounded-xl border-2 border-dashed border-accent p-3" data-testid="bmca-arena">
          <h3 className="mb-2 text-sm font-semibold">Arena: candidates in the election</h3>
          <div className="flex flex-col gap-2">{inArena.map((c) => card(c, "arena"))}</div>
          <p className="mt-3 rounded bg-surface-2 p-2 text-sm" aria-live="polite" data-testid="bmca-result">
            {res ? (
              <>
                Winner: <strong>{res.winner.name}</strong> (decided by <strong>{res.field}</strong>)
              </>
            ) : (
              "No candidates."
            )}
          </p>
        </section>
      </div>
      <ul className="mt-3 space-y-1 text-sm">
        <li className={rogue.priority1 === 128 ? "text-ok" : "text-danger"}>{rogue.priority1 === 128 ? "✓" : "✗"} Rogue priority1 is 128 (G.8275.1 fixes it; any other value is illegal)</li>
        <li className={LEGAL_CLASSES.includes(rogue.clockClass) ? "text-ok" : "text-danger"}>{LEGAL_CLASSES.includes(rogue.clockClass) ? "✓" : "✗"} Rogue clockClass is in the G.8275.1 table</li>
        <li className={solved ? "font-semibold text-ok" : "text-muted"}>{solved ? "✓ The rogue wins with legal values: exactly what happened in A1 replicate 1 (rogue clockClass 6 vs the legitimate grandmaster's 248). Only the operator's allow-list exposes it." : "Goal: the rogue wins against at least one allow-listed clock, with legal values."}</li>
      </ul>
      <p className="mt-2 text-xs text-muted">GM-A&apos;s clockClass 248 is the value it advertised in A1 r1 (story guide ch. 9). Other starting values are illustrative.</p>
    </div>
  );
}
