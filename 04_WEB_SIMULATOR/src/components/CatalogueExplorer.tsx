"use client";
import { useMemo, useState } from "react";
import clsx from "clsx";
import type { Fault } from "@prisma/client";
import { Badge } from "./ui";

const CLASSES = ["ALL", "ATTACK", "BENIGN", "UNKNOWN"] as const;
const TESTBED = ["ALL", "SOFTWARE", "SOFTWARE (detection only)", "HARDWARE required", "campaign scenario"] as const;

export function CatalogueExplorer({ faults }: { faults: Fault[] }) {
  const [q, setQ] = useState("");
  const [cls, setCls] = useState<(typeof CLASSES)[number]>("ALL");
  const [tb, setTb] = useState<(typeof TESTBED)[number]>("ALL");
  const [open, setOpen] = useState<string | null>(null);

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return faults.filter((f) => {
      if (cls !== "ALL" && f.cls !== cls) return false;
      if (tb === "campaign scenario" && f.kind !== "campaign scenario") return false;
      if (tb !== "ALL" && tb !== "campaign scenario" && f.testbedRequired !== tb) return false;
      if (!needle) return true;
      return [f.id, f.name, f.source, f.destination, f.attackDevices, f.consequence, f.citations, f.threatId, f.mechanism, f.signature]
        .filter(Boolean)
        .some((x) => x!.toLowerCase().includes(needle));
    });
  }, [faults, q, cls, tb]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-line bg-surface p-4">
        <label className="flex min-w-60 flex-1 flex-col text-sm">
          <span className="mb-1 font-medium">Search</span>
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. Announce, GNSS, T-SPLANE-03, boundary clock"
            className="rounded-md border border-line bg-surface px-3 py-2"
            data-testid="cat-search"
          />
        </label>
        <fieldset className="text-sm">
          <legend className="mb-1 font-medium">Class</legend>
          <div className="flex overflow-hidden rounded-md border border-line">
            {CLASSES.map((c) => (
              <button key={c} type="button" aria-pressed={cls === c} onClick={() => setCls(c)} className={clsx("px-3 py-2", cls === c ? "bg-accent text-accent-ink" : "hover:bg-surface-2")}>
                {c === "ALL" ? "All" : c}
              </button>
            ))}
          </div>
        </fieldset>
        <label className="flex flex-col text-sm">
          <span className="mb-1 font-medium">Testbed</span>
          <select value={tb} onChange={(e) => setTb(e.target.value as (typeof TESTBED)[number])} className="rounded-md border border-line bg-surface px-3 py-2">
            {TESTBED.map((t) => (
              <option key={t} value={t}>
                {t === "ALL" ? "Any" : t}
              </option>
            ))}
          </select>
        </label>
        <p className="num ml-auto text-sm text-muted" aria-live="polite" data-testid="cat-count">
          {rows.length} of {faults.length} faults
        </p>
      </div>

      <ul className="flex flex-col gap-3">
        {rows.map((f) => {
          const isOpen = open === f.id;
          return (
            <li key={f.id} className="rounded-xl border border-line bg-surface">
              <button
                type="button"
                aria-expanded={isOpen}
                aria-controls={`fault-${f.id}`}
                onClick={() => setOpen(isOpen ? null : f.id)}
                className="flex w-full flex-wrap items-center gap-3 p-4 text-left"
              >
                <span className="font-mono text-sm font-semibold">{f.id}</span>
                <span className="font-semibold">{f.name}</span>
                <Badge tone={f.cls === "ATTACK" ? "danger" : f.cls === "BENIGN" ? "ok" : "warn"}>{f.cls}</Badge>
                {f.testbedRequired && <Badge>{f.testbedRequired}</Badge>}
                {f.kind === "campaign scenario" && <Badge tone="accent">campaign scenario</Badge>}
                <span className="ml-auto text-sm text-muted">{isOpen ? "Hide" : "Details"}</span>
              </button>
              <div className="grid gap-x-6 gap-y-3 border-t border-line p-4 text-sm md:grid-cols-2" hidden={!isOpen} id={`fault-${f.id}`}>
                <Field label="Source (of attack or fault)" v={f.source} />
                <Field label="Destination (where it hits)" v={f.destination} />
                <Field label="Attack devices (possible originating devices)" v={f.attackDevices} />
                <Field label="Consequence (effect)" v={f.consequence} />
                <Field label="Detectable now on the software testbed?" v={f.detectableNow} />
                <Field label="Evidence / decision rule" v={f.evidence} />
                <Field label="Mechanism / cause" v={f.mechanism} />
                <Field label="Signature / benign tell" v={f.signature} />
                <Field label="Look-alike" v={f.lookAlike} />
                <Field label="Still missing" v={f.missing} />
                <Field label="O-RAN WG11 threat ID (ETSI TR 104 106)" v={f.threatId} />
                <Field label="Standards / sources" v={f.citations} />
                <p className="text-xs text-muted md:col-span-2">From: {f.sourceFile}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function Field({ label, v }: { label: string; v: string | null }) {
  if (!v) return null;
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-0.5 whitespace-pre-line">{v}</p>
    </div>
  );
}
