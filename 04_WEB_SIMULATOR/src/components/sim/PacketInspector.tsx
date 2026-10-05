"use client";
import { useMemo } from "react";
import clsx from "clsx";
import { DEVICE_LABEL, packetsAt, type Device, type ReplayRun } from "@/lib/replay";
import { keyEvents } from "@/lib/sim/events";
import type { SimState } from "@/lib/sim/state";
import { KindBadge } from "../ui";
import { Sentences } from "./Sentences";

const TABS = [
  ["exchange", "Sync / Delay exchange (t1–t4)", "ptp-exchange"],
  ["bmca", "Announce and BMCA", "bmca-contest"],
  ["attack", "Attack packets", "attack-packets"],
  ["counts", "Per-sender packet counts", "port-counts"],
] as const;
const TYPES = ["Sync", "Follow_Up", "Delay_Req", "Delay_Resp", "Announce"];
const ATTACKERS = new Set(["rogue", "rbc", "injector"]);
const label = (s: string) => DEVICE_LABEL[s as Device] ?? s;

/** Level-3 overlay: what the PTP frames on the testbed mean, with the recorded counts at the current replay time. */
export function PacketInspector({ run, t, tab, onTab }: { run?: ReplayRun; t: number; tab: SimState["pkt"]; onTab: (t: SimState["pkt"]) => void }) {
  const bin = Math.floor(t / 0.5) * 0.5;
  const dn = useMemo(() => (run ? packetsAt(run, bin, "dn") : {}), [run, bin]);
  const up = useMemo(() => (run ? packetsAt(run, bin, "up") : {}), [run, bin]);
  const loc = useMemo(() => (run ? keyEvents(run).find((e) => e.kind === "localise") : undefined), [run]);
  const elId = TABS.find((x) => x[0] === tab)![2];
  const binLabel = `bin T0 ${bin >= 0 ? "+" : "−"} ${Math.abs(bin).toFixed(1)} s … ${Math.abs(bin + 0.5).toFixed(1)} s`;
  return (
    <section className="rounded-xl border border-line bg-surface p-3 sm:p-4" aria-label="Inspect packets" data-testid="pkt-inspector" data-tab={tab}>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="mr-2 text-base font-semibold">Inspect packets</h2>
        <div role="tablist" aria-label="Packet views" className="flex flex-wrap gap-1">
          {TABS.map(([id, name]) => (
            <button
              key={id}
              role="tab"
              type="button"
              aria-selected={tab === id}
              onClick={() => onTab(id)}
              className={clsx("rounded-md border px-2.5 py-1 text-sm", tab === id ? "border-accent bg-accent-soft font-semibold" : "border-line hover:bg-surface-2")}
              data-testid={`pkt-tab-${id}`}
            >
              {name}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-3 grid gap-4 lg:grid-cols-[1fr_1fr]">
        <div>
          {tab === "exchange" && <Ladder />}
          {tab === "bmca" && <BmcaFields announce={Object.fromEntries(Object.entries(dn).map(([s, m]) => [s, m.Announce ?? 0]).filter(([, n]) => (n as number) > 0))} binLabel={binLabel} />}
          {tab === "attack" && (
            <div className="text-sm" data-testid="pkt-attack">
              <p>
                <KindBadge kind="MEASURED" /> Port the loop localised the violation to in this run:{" "}
                <strong data-testid="pkt-attack-port">{loc ? loc.label.replace("Violation attributed to port ", "") : "none recorded"}</strong>
                {loc && <span className="num text-muted"> (first at T0 + {loc.t.toFixed(3)} s)</span>}
              </p>
              <p className="mt-2">
                <KindBadge kind="MEASURED" /> Frames from attacker senders on brDN, {binLabel}:{" "}
                <strong data-testid="pkt-attack-frames">
                  {Object.entries(dn).filter(([s]) => ATTACKERS.has(s)).reduce((a, [, m]) => a + Object.values(m).reduce((x, y) => x + y, 0), 0)}
                </strong>
              </p>
            </div>
          )}
          {tab === "counts" && (
            <div className="overflow-x-auto" data-testid="pkt-counts">
              <CountTable title={`brDN (RU segment), ${binLabel}`} data={dn} />
              <CountTable title={`brUP (grandmaster segment), ${binLabel}`} data={up} />
            </div>
          )}
        </div>
        <Sentences id={elId} compact />
      </div>
    </section>
  );
}

function CountTable({ title, data }: { title: string; data: Record<string, Record<string, number>> }) {
  const senders = Object.keys(data).sort();
  return (
    <table className="mb-3 w-full min-w-[420px] text-xs">
      <caption className="mb-1 text-left text-xs font-semibold">
        <KindBadge kind="MEASURED" /> {title}
      </caption>
      <thead>
        <tr className="text-left text-muted">
          <th className="py-0.5">Sender</th>
          {TYPES.map((x) => (
            <th key={x} className="num">{x}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {senders.length === 0 && (
          <tr>
            <td colSpan={6} className="py-1 text-muted">No frames recorded in this bin.</td>
          </tr>
        )}
        {senders.map((s) => (
          <tr key={s} className={clsx("border-t border-line", ATTACKERS.has(s) && "text-danger")} data-sender={s}>
            <td className="py-0.5 font-semibold">{label(s)}</td>
            {TYPES.map((x) => (
              <td key={x} className="num">{data[s][x] ?? 0}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Message ladder for the delay request-response exchange. Arrow geometry is ILLUSTRATIVE; the formulas are in the cited sentences. */
function Ladder() {
  const rows = [
    { y: 40, from: "m", name: "Sync", a: "t1", b: "t2" },
    { y: 80, from: "m", name: "Follow_Up (carries t1)", a: "", b: "" },
    { y: 130, from: "s", name: "Delay_Req", a: "t3", b: "t4" },
    { y: 170, from: "m", name: "Delay_Resp (carries t4)", a: "", b: "" },
  ];
  return (
    <figure data-testid="pkt-ladder">
      <svg viewBox="0 0 360 210" className="w-full max-w-md" role="img" aria-label="Sync, Follow_Up, Delay_Req and Delay_Resp between master and slave, with timestamps t1 to t4">
        <text x={60} y={16} textAnchor="middle" className="sim-label">Master (BC)</text>
        <text x={300} y={16} textAnchor="middle" className="sim-label">Slave (RU)</text>
        <line x1={60} y1={24} x2={60} y2={200} stroke="var(--muted)" />
        <line x1={300} y1={24} x2={300} y2={200} stroke="var(--muted)" />
        {rows.map((r) => {
          const x1 = r.from === "m" ? 60 : 300, x2 = r.from === "m" ? 300 : 60;
          return (
            <g key={r.name}>
              <line x1={x1} y1={r.y} x2={x2} y2={r.y + 18} stroke={r.name.startsWith("Delay") ? "var(--delay)" : "var(--sync)"} strokeWidth={2} markerEnd="url(#lad)" />
              <text x={180} y={r.y + 4} textAnchor="middle" className="sim-sublabel">{r.name}</text>
              {r.a && <text x={x1 + (r.from === "m" ? -8 : 8)} y={r.y + 4} textAnchor={r.from === "m" ? "end" : "start"} className="sim-label">{r.a}</text>}
              {r.b && <text x={x2 + (r.from === "m" ? 8 : -8)} y={r.y + 22} textAnchor={r.from === "m" ? "start" : "end"} className="sim-label">{r.b}</text>}
            </g>
          );
        })}
        <defs>
          <marker id="lad" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L8,4 L0,8 z" fill="var(--muted)" />
          </marker>
        </defs>
      </svg>
      <figcaption className="text-xs text-muted">
        <KindBadge kind="ILLUSTRATIVE" /> Ladder geometry only; the recorded runs log frame counts per 0.5 s, not individual timestamps.
      </figcaption>
    </figure>
  );
}

function BmcaFields({ announce, binLabel }: { announce: Record<string, number>; binLabel: string }) {
  const senders = Object.keys(announce).sort();
  return (
    <div className="text-sm" data-testid="pkt-bmca">
      <p className="font-semibold">Fields compared, in order</p>
      <ol className="mt-1 flex flex-wrap items-center gap-1 text-xs">
        {["priority1", "clockClass", "priority2", "clockIdentity"].map((f, i) => (
          <li key={f} className={clsx("rounded border px-2 py-0.5", f === "clockClass" ? "border-danger bg-danger-soft font-semibold" : "border-line")} data-field={f}>
            {i > 0 && "→ "}
            {f}
          </li>
        ))}
      </ol>
      <p className="mt-1 text-xs text-muted">Highlighted: the field that decided the A1 campaign replicate-1 contest (see the measured sentence beside).</p>
      <p className="mt-3 font-semibold">
        <KindBadge kind="MEASURED" /> Announce frames on brDN in this run, {binLabel}
      </p>
      <ul className="mt-1 text-xs" data-testid="pkt-bmca-announce">
        {senders.length === 0 && <li className="text-muted">No Announce frames in this bin.</li>}
        {senders.map((s) => (
          <li key={s} className={ATTACKERS.has(s) ? "font-semibold text-danger" : ""} data-sender={s}>
            {label(s)}: <span className="num">{announce[s]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
