"use client";
import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import type { Widget as W } from "@/lib/lessons";
import type { LessonData } from "../LessonPlayer";
import { ReplayViewer } from "../ReplayViewer";
import { Topology } from "../Topology";
import { LIMITS } from "../LimitsPanel";
import { ModelLabel, MeasuredLabel } from "../ui";
import { BmcaArena } from "./BmcaArena";
import type { Device } from "@/lib/replay";

export function Widget({ widget, data, onDone, stepId }: { widget: W; data: LessonData; onDone: () => void; stepId: string }) {
  switch (widget.type) {
    case "planes":
      return <Reveal items={PLANES} onDone={onDone} min={4} />;
    case "budget":
      return <Budget onDone={onDone} />;
    case "topology-tour":
      return <TopologyTour onDone={onDone} />;
    case "sequence":
      return <Sequence onDone={onDone} />;
    case "offset":
      return <Offset onDone={onDone} />;
    case "profile-check":
      return <ProfileCheck onDone={onDone} />;
    case "bmca":
      return <BmcaArena onDone={onDone} />;
    case "steps-removed":
      return <StepsRemoved onDone={onDone} a8={data.a8} />;
    case "lookalikes":
      return (
        <Reveal
          min={3}
          onDone={onDone}
          items={(data.lookAlikes ?? []).map((l, i) => ({
            key: `la${i + 1}`,
            label: l.symptom,
            content: (
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                <div><dt className="font-semibold text-ok">Benign explanation</dt><dd>{l.benign}</dd></div>
                <div><dt className="font-semibold text-danger">Attack explanation</dt><dd>{l.attack}</dd></div>
                <div className="sm:col-span-2"><dt className="font-semibold">The decisive test</dt><dd>{l.discriminator}</dd></div>
                <div><dt className="text-muted">Decidable within 2 s?</dt><dd>{l.within2s}</dd></div>
                <div><dt className="text-muted">Sources</dt><dd>{l.citations}</dd></div>
              </dl>
            ),
          }))}
        />
      );
    case "verdict-game":
      return <VerdictGame runs={data.game ?? []} onDone={onDone} />;
    case "verdict-actions":
      return <Reveal items={VERDICTS} onDone={onDone} min={3} />;
    case "replay":
      return (
        <div>
          {widget.note && <p className="mb-2 text-sm font-semibold">{widget.note}</p>}
          <ReplayViewer
            scenarios={(data.scenarios ?? []).filter((s) => widget.scenarios.includes(s.id))}
            initialScenario={widget.scenarios[0]}
            initialRep={widget.rep ?? 13}
            lockRep={!!widget.rep}
            compact
            onEnded={onDone}
            idPrefix={`lr-${stepId}`}
          />
        </div>
      );
    case "loop-stepper":
      return <Stepper onDone={onDone} />;
    case "policy":
      return <Reveal items={POLICY} onDone={onDone} min={POLICY.length} />;
    case "limits":
      return <FlipCards onDone={onDone} />;
  }
}

/* ------------------------------------------------------------------ generic reveal list */
interface RevealItem {
  key: string;
  label: string;
  content: React.ReactNode;
}
function Reveal({ items, onDone, min }: { items: RevealItem[]; onDone: () => void; min: number }) {
  const [seen, setSeen] = useState<Set<string>>(new Set());
  const [open, setOpen] = useState<string | null>(null);
  useEffect(() => {
    if (seen.size >= Math.min(min, items.length) && items.length > 0) onDone();
  }, [seen, min, items.length, onDone]);
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs text-muted">
        Opened {seen.size}/{items.length}
      </p>
      {items.map((it) => (
        <div key={it.key} className="rounded-lg border border-line">
          <button
            type="button"
            aria-expanded={open === it.key}
            onClick={() => {
              setOpen(open === it.key ? null : it.key);
              setSeen((s) => new Set(s).add(it.key));
            }}
            className={clsx("flex w-full items-center justify-between gap-2 px-4 py-3 text-left font-semibold", seen.has(it.key) && "text-ink")}
            data-testid={`reveal-${it.key}`}
          >
            <span>{it.label}</span>
            <span aria-hidden="true" className="text-muted">
              {seen.has(it.key) ? "✓" : "+"}
            </span>
          </button>
          {open === it.key && <div className="border-t border-line px-4 py-3 text-sm">{it.content}</div>}
        </div>
      ))}
    </div>
  );
}

const PLANES: RevealItem[] = [
  { key: "C", label: "C-plane (control)", content: "Tells the radio unit what to do with the next slots (scheduling and beamforming commands)." },
  { key: "U", label: "U-plane (user)", content: "The radio samples themselves, meaning the users' data." },
  { key: "S", label: "S-plane (synchronization)", content: "Time and frequency: PTP (IEEE 1588 with the ITU-T G.8275.1 profile) and SyncE. This project lives here." },
  { key: "M", label: "M-plane (management)", content: "Configuring and monitoring the radio unit." },
];

const VERDICTS: RevealItem[] = [
  { key: "ATTACK", label: "ATTACK", content: "Evidence is illegal under the standard, or unauthorised under the operator's provisioning. Loop: ISOLATE the offending ingress port once 2 of the last 3 evaluations say ATTACK, unless the port is a provisioned master-role port (safety guard → escalate). Basis: RFC 7384 §5.1.1, §5.10.1; acceptable-master table / master-only ports (Arnold & Frost, WSTS 2016)." },
  { key: "BENIGN", label: "BENIGN", content: "Only provisioned clocks are involved, nothing is illegal, and the declared state agrees with what is observed. Loop: TOLERATE (no action)." },
  { key: "UNKNOWN", label: "UNKNOWN", content: "The packets genuinely cannot reveal intent, for example a grandmaster change between allow-listed clocks with no maintenance window. Loop: ESCALATE to an operator, no automatic action ('raise alarm', Arnold & Frost)." },
];

const POLICY: RevealItem[] = [
  { key: "p1", label: "ATTACK on ≥ 2 of the last 3 evaluations + a violating, non-master port", content: "ISOLATE: nft bridge prerouting `iifname <port> ether type 0x88f7 drop`. Verify every non-isolated RU within 20 s, else roll back and escalate. Basis: RFC 7384 §5.1.1, §5.10.1; G.8275.1 notSlave; master-only ports." },
  { key: "p2", label: "ATTACK, but only provisioned master-role ports (or none) violate", content: "ESCALATE (safety guard). Isolating a provisioned BC would itself remove timing. This is what keeps the B_bc_replacement false A8 harmless." },
  { key: "p3", label: "No Announce from any provisioned master port for > 2 s (10 s in a maintenance window)", content: "ACTIVATE STANDBY BC. Verified like isolation. Basis: RFC 7384 §5.9 (redundant masters / paths); IEEE 1588 security Prong C. Correct whether the loss is interception (C1) or a failed BC (B3 r17)." },
  { key: "p4", label: "UNKNOWN", content: "ESCALATE, no automatic action." },
  { key: "p5", label: "BENIGN", content: "TOLERATE: nothing is done." },
];

/* ------------------------------------------------------------------ budget */
function Budget({ onDone }: { onDone: () => void }) {
  const [ns, setNs] = useState(20);
  const limits = [
    { v: 65, label: "65 ns · time-alignment error for MIMO (3GPP TS 38.104 cl. 9.6.3.2)" },
    { v: 130, label: "130 ns · max relative error between RUs in a cluster (O-RAN category A)" },
    { v: 260, label: "260 ns · TAE for intra-band contiguous carrier aggregation (TS 38.104)" },
    { v: 1500, label: "1.5 µs · absolute time error at point E (ITU-T G.8271.1)" },
    { v: 3000, label: "3 µs · cell phase synchronization (3GPP TS 38.133)" },
  ];
  useEffect(() => {
    if (ns > 65) onDone();
  }, [ns, onDone]);
  return (
    <div>
      <label htmlFor="budget" className="font-semibold">
        Time error: <span className="num">{ns >= 1000 ? `${(ns / 1000).toFixed(2)} µs` : `${ns} ns`}</span>
      </label>
      <input id="budget" type="range" min={0} max={4000} step={5} value={ns} onChange={(e) => setNs(Number(e.target.value))} className="mt-2 w-full accent-[var(--accent)]" />
      <ul className="mt-3 space-y-1 text-sm">
        {limits.map((l) => (
          <li key={l.v} className={clsx("rounded px-2 py-1", ns > l.v ? "bg-danger-soft text-danger" : "bg-ok-soft text-ok")}>
            {ns > l.v ? "Exceeded: " : "Within: "}
            {l.label}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-muted">These limits measure different quantities (relative alignment vs absolute error vs cell phase) and are shown together only for scale. Software timestamping on this testbed has microsecond-scale noise, so the project makes no claim at this scale.</p>
    </div>
  );
}

/* ------------------------------------------------------------------ topology tour */
const TOUR: Partial<Record<Device, string>> = {
  gma: "GM-A, grandmaster (identity 020000fffe00000a), on the allow-list. Serves time on brUP.",
  gmb: "GM-B, backup grandmaster (020000fffe00000b), also allow-listed.",
  bc: "Boundary clock (020000fffe000001): slave on brUP, master on brDN, re-serving time to the radio units. Its downstream bridge port is p-v-bc-dn.",
  bcs: "Cold-standby boundary clock (020000fffe0000c5), cabled to both bridges in every run of both arms. Its daemon starts only if the loop executes a failover.",
  ru1: "RU1, a timing client (020000fffe00000c). RU1 and RU2 are the primary outcome nodes.",
  ru2: "RU2, a timing client (020000fffe00000d).",
  ru3: "RU3 (020000fffe00000e). In A2, A3, A5, C2 and C3 the injector runs inside RU3's namespace, so isolating its port also cuts RU3. Reported separately.",
};
function TopologyTour({ onDone }: { onDone: () => void }) {
  const [sel, setSel] = useState<Device | null>(null);
  const [seen, setSeen] = useState<Set<Device>>(new Set());
  const need = Object.keys(TOUR) as Device[];
  useEffect(() => {
    if (need.every((d) => seen.has(d))) onDone();
  }, [seen, need, onDone]);
  return (
    <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
      <Topology scenarioId="baseline" state={null} title="Testbed topology (static diagram)" staticMode highlight={sel} onSelect={(d) => { if (TOUR[d]) { setSel(d); setSeen((s) => new Set(s).add(d)); } }} />
      <div>
        <p className="text-xs text-muted">Inspected {need.filter((d) => seen.has(d)).length}/{need.length}. Select a device in the diagram (keyboard: Tab, then Enter) or use the list.</p>
        <div className="mt-2 flex flex-wrap gap-1">
          {need.map((d) => (
            <button key={d} type="button" onClick={() => { setSel(d); setSeen((s) => new Set(s).add(d)); }} className={clsx("rounded border px-2 py-1 text-xs", seen.has(d) ? "border-ok text-ok" : "border-line")} data-testid={`tour-${d}`}>
              {d.toUpperCase()}
            </button>
          ))}
        </div>
        <p className="mt-3 min-h-24 text-sm" aria-live="polite">{sel ? TOUR[sel] : "Nothing selected yet."}</p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ PTP message ladder */
const MSGS = [
  { name: "Sync", dir: "m2s", note: "Master sends Sync at t1. Slave records arrival t2." },
  { name: "Follow_Up", dir: "m2s", note: "Two-step: the master sends the precise value of t1." },
  { name: "Delay_Req", dir: "s2m", note: "Slave sends Delay_Req at t3." },
  { name: "Delay_Resp", dir: "m2s", note: "Master returns the arrival time t4. The slave now has t1, t2, t3, t4." },
];
function Sequence({ onDone }: { onDone: () => void }) {
  const [k, setK] = useState(0);
  useEffect(() => {
    if (k >= 4) onDone();
  }, [k, onDone]);
  return (
    <div className="grid gap-4 md:grid-cols-[1fr_1fr]">
      <svg viewBox="0 0 320 260" className="w-full max-w-sm" role="img" aria-label={`PTP exchange, ${k} of 4 messages shown`}>
        <text x={50} y={18} textAnchor="middle" fontSize={13} fontWeight={600} fill="var(--ink)">Master</text>
        <text x={270} y={18} textAnchor="middle" fontSize={13} fontWeight={600} fill="var(--ink)">Slave (RU)</text>
        <line x1={50} y1={28} x2={50} y2={250} stroke="var(--line)" strokeWidth={3} />
        <line x1={270} y1={28} x2={270} y2={250} stroke="var(--line)" strokeWidth={3} />
        {MSGS.slice(0, k).map((m, i) => {
          const y0 = 45 + i * 50, y1 = y0 + 30;
          const [x0, x1] = m.dir === "m2s" ? [50, 270] : [270, 50];
          return (
            <g key={m.name}>
              <line x1={x0} y1={y0} x2={x1} y2={y1} stroke={m.name === "Delay_Req" || m.name === "Delay_Resp" ? "var(--delay)" : "var(--sync)"} strokeWidth={2.5} markerEnd="url(#seq-arr)" />
              <text x={160} y={(y0 + y1) / 2 - 6} textAnchor="middle" fontSize={12} fill="var(--ink)">{m.name}</text>
              {i === 0 && <text x={40} y={y0 + 4} textAnchor="end" fontSize={11} fill="var(--muted)">t1</text>}
              {i === 0 && <text x={280} y={y1 + 4} fontSize={11} fill="var(--muted)">t2</text>}
              {i === 2 && <text x={280} y={y0 + 4} fontSize={11} fill="var(--muted)">t3</text>}
              {i === 2 && <text x={40} y={y1 + 4} textAnchor="end" fontSize={11} fill="var(--muted)">t4</text>}
            </g>
          );
        })}
        <defs>
          <marker id="seq-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--muted)" />
          </marker>
        </defs>
      </svg>
      <div>
        <p className="min-h-16" aria-live="polite">{k === 0 ? "Press Next message to start." : MSGS[k - 1].note}</p>
        <div className="mt-3 flex gap-2">
          <button type="button" className="rounded-md bg-accent px-4 py-2 font-semibold text-accent-ink disabled:opacity-50" disabled={k >= 4} onClick={() => setK(k + 1)} data-testid="seq-next">
            Next message
          </button>
          <button type="button" className="rounded-md border border-line px-4 py-2" onClick={() => setK(0)}>
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ offset calculator */
function Offset({ onDone }: { onDone: () => void }) {
  const [t, setT] = useState({ t1: 0, t2: 5300, t3: 8000, t4: 12700 });
  const [asym, setAsym] = useState(0);
  const [guess, setGuess] = useState("");
  const [checked, setChecked] = useState<null | boolean>(null);
  const t2 = t.t2 + asym; // extra one-way delay master -> slave only
  const ms = t2 - t.t1, sm = t.t4 - t.t3;
  const offset = (ms - sm) / 2, delay = (ms + sm) / 2;
  const base = (t.t2 - t.t1 - (t.t4 - t.t3)) / 2;
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div>
        <div className="flex items-center gap-2"><ModelLabel>Illustrative numbers</ModelLabel></div>
        <div className="mt-3 grid grid-cols-2 gap-3">
          {(["t1", "t2", "t3", "t4"] as const).map((k) => (
            <label key={k} className="flex flex-col text-sm">
              <span className="font-mono font-semibold">{k} (ns)</span>
              <input type="number" value={t[k]} onChange={(e) => { setT({ ...t, [k]: Number(e.target.value) }); setChecked(null); }} className="rounded-md border border-line bg-surface px-2 py-1 num" />
            </label>
          ))}
        </div>
        <label className="mt-4 block text-sm">
          <span className="font-semibold">Extra one-way delay master → slave (asymmetry): {asym} ns</span>
          <input type="range" min={0} max={2000} step={50} value={asym} onChange={(e) => setAsym(Number(e.target.value))} className="w-full accent-[var(--accent)]" />
        </label>
      </div>
      <div className="text-sm">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const ok = Math.abs(Number(guess) - base) < 0.5;
            setChecked(ok);
            if (ok) onDone();
          }}
          className="flex flex-col gap-2"
        >
          <label htmlFor="offset-guess" className="font-semibold">
            With no asymmetry, what is the slave&apos;s offset from master (ns)?
          </label>
          <div className="flex gap-2">
            <input id="offset-guess" inputMode="numeric" value={guess} onChange={(e) => setGuess(e.target.value)} className="w-32 rounded-md border border-line bg-surface px-2 py-1 num" data-testid="offset-input" />
            <button type="submit" className="rounded-md bg-accent px-3 py-1 font-semibold text-accent-ink" data-testid="offset-check">Check</button>
          </div>
          {checked !== null && (
            <p role="status" className={checked ? "text-ok" : "text-danger"}>
              {checked ? `Correct: [(t2 − t1) − (t4 − t3)] / 2 = ${base} ns.` : "Not yet. Use offset = [(t2 − t1) − (t4 − t3)] / 2."}
            </p>
          )}
        </form>
        <dl className="mt-4 grid grid-cols-2 gap-2">
          <div className="rounded bg-surface-2 p-2"><dt className="text-xs text-muted">Computed offset</dt><dd className="num font-semibold">{checked ? `${offset} ns` : "?"}</dd></div>
          <div className="rounded bg-surface-2 p-2"><dt className="text-xs text-muted">Computed mean path delay</dt><dd className="num font-semibold">{checked ? `${delay} ns` : "?"}</dd></div>
        </dl>
        {checked && asym > 0 && (
          <p className="mt-2 rounded bg-warn-soft p-2 text-warn">
            The true offset did not change, but the computed offset moved by {offset - base} ns: half of the {asym} ns asymmetry. The slave cannot see this error.
          </p>
        )}
        <p className="mt-3 text-xs text-muted">
          Real log line, baseline run 1, RU1: <code>ptp4l[517.414]: master offset 1191 s0 freq -1547 path delay 5313</code>: offset 1 191 ns, servo state s0 (not steering, because of free_running 1), path delay 5 313 ns (story guide ch. 3).
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ profile legality */
const ANNOUNCES = [
  { id: "a", fields: "domain 24 · priority1 128 · clockClass 6 · from GM-A (allow-listed)", legal: true, why: "All fields match G.8275.1 and the sender is provisioned." },
  { id: "b", fields: "domain 24 · priority1 100 · clockClass 6", legal: false, why: "G.8275.1 fixes priority1 at 128: illegal under the profile (rule check 5)." },
  { id: "c", fields: "domain 0 · priority1 128 · clockClass 6", legal: false, why: "Out-of-profile domain: the testbed runs domain 24 (rule check 8)." },
  { id: "d", fields: "domain 24 · priority1 128 · priority2 1 · clockClass 6 · from 020000fffe000042 (not on the allow-list)", legal: true, why: "Every field is legal. This is A1 replicate 1's rogue: only the operator's allow-list exposes it." },
];
function ProfileCheck({ onDone }: { onDone: () => void }) {
  const [ans, setAns] = useState<Record<string, boolean>>({});
  useEffect(() => {
    if (Object.keys(ans).length === ANNOUNCES.length) onDone();
  }, [ans, onDone]);
  return (
    <ul className="flex flex-col gap-3">
      {ANNOUNCES.map((a) => {
        const picked = ans[a.id];
        return (
          <li key={a.id} className="rounded-lg border border-line p-3">
            <p className="font-mono text-sm">Announce {a.id.toUpperCase()}: {a.fields}</p>
            <div className="mt-2 flex gap-2">
              {[true, false].map((v) => (
                <button key={String(v)} type="button" disabled={picked !== undefined} onClick={() => setAns({ ...ans, [a.id]: v })}
                  className={clsx("rounded-md border px-3 py-1 text-sm", picked === v ? (v === a.legal ? "border-ok bg-ok-soft" : "border-danger bg-danger-soft") : "border-line")}
                  data-testid={`profile-${a.id}-${v ? "legal" : "illegal"}`}>
                  {v ? "Legal under the profile" : "Breaks the profile"}
                </button>
              ))}
            </div>
            {picked !== undefined && <p role="status" className={clsx("mt-2 text-sm", picked === a.legal ? "text-ok" : "text-danger")}>{picked === a.legal ? "Correct. " : "Not quite. "}{a.why}</p>}
          </li>
        );
      })}
    </ul>
  );
}

/* ------------------------------------------------------------------ stepsRemoved */
function StepsRemoved({ onDone, a8 }: { onDone: () => void; a8?: { id: string; onBc: number; total: number }[] }) {
  const [seen, setSeen] = useState<Set<string>>(new Set());
  useEffect(() => {
    if (seen.size >= 2) onDone();
  }, [seen, onDone]);
  const P = [
    { k: "real", title: "Real path: GM-A → BC → RU", text: "The provisioned boundary clock slaves to GM-A on brUP and serves the RU segment on brDN." },
    { k: "rogue", title: "Rogue path: GM-A → rogue BC → RU", text: "The rogue BC (A8) also slaves to the real grandmaster and re-advertises downstream. The frozen rule flags it as 'unauthorised clock inserted in the timing path, relaying another grandmaster with stepsRemoved incremented'." },
  ];
  return (
    <div>
      <div className="grid gap-3 md:grid-cols-2">
        {P.map((p) => (
          <button key={p.k} type="button" onClick={() => setSeen((s) => new Set(s).add(p.k))} className={clsx("rounded-lg border p-3 text-left", seen.has(p.k) ? "border-accent bg-accent-soft" : "border-line")} data-testid={`path-${p.k}`}>
            <span className="font-semibold">{p.title}</span>
            {seen.has(p.k) && <span className="mt-1 block text-sm">{p.text}</span>}
          </button>
        ))}
      </div>
      {seen.size >= 2 && (
        <div className="mt-3 rounded-lg border border-line p-3 text-sm">
          <MeasuredLabel />
          <p className="mt-2">
            In the A8 control runs (no action), RU1 and RU2 reported the real BC as parent in{" "}
            <strong className="num">{a8 ? a8.map((r) => `${r.onBc}/${r.total}`).join(", ") : "–"}</strong> observer samples between T0 and T0 + 40 s
            (one figure per run, {a8?.length ?? 0} runs; database count). RESULTS §4 reports the same 160/160. The
            project&apos;s explanation (RESULTS §4): with the same grandmaster on both paths, the BMCA prefers the path with fewer
            stepsRemoved, so the rogue BC was a candidate, not a takeover. The v8 deck&apos;s &quot;36/36 RU logs took the rogue BC as a new
            master&quot; meant a new foreign-master candidate.
          </p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ verdict game */
const CTX: Record<string, string> = {
  A1_rogue_master: "Maintenance window: closed. A clock not on the allow-list starts announcing itself as grandmaster with clockClass 6.",
  B2_gm_failover: "Maintenance window: OPEN. GM-A is withdrawn; allow-listed GM-B takes over.",
  B_unplanned_failover: "Maintenance window: closed. GM-A stops; allow-listed GM-B is elected.",
  B_bc_replacement: "Maintenance window: OPEN. The BC is swapped for a provisioned replacement (ticket open).",
  C3_wholesecond: "Maintenance window: closed. Announce frames appear with leap61 set, currentUtcOffset 0 (true value 37) and traceability flags cleared.",
  B3_pdv_congestion: "Maintenance window: closed. A 1 Mbit bottleneck with competing traffic; only provisioned clocks present.",
};
function VerdictGame({ runs, onDone }: { runs: { id: string; scenarioId: string; expected: string; description: string | null; v3Verdict: string; v3Hint: string | null; v3Reason: string | null; nPackets: number | null }[]; onDone: () => void }) {
  const [ans, setAns] = useState<Record<string, string>>({});
  useEffect(() => {
    if (runs.length && Object.keys(ans).length === runs.length) onDone();
  }, [ans, runs.length, onDone]);
  const score = useMemo(() => runs.filter((r) => ans[r.id] === r.expected).length, [ans, runs]);
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <MeasuredLabel>Real campaign runs</MeasuredLabel>
        <span className="num text-sm text-muted">Your score: {score}/{Object.keys(ans).length}</span>
      </div>
      <ul className="mt-3 grid gap-3 md:grid-cols-2">
        {runs.map((r) => {
          const a = ans[r.id];
          return (
            <li key={r.id} className="rounded-lg border border-line p-3">
              <p className="font-mono text-xs text-muted">{r.id} · {r.nPackets?.toLocaleString("en-US")} packets</p>
              <p className="mt-1 text-sm">{CTX[r.scenarioId]}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {["ATTACK", "BENIGN", "UNKNOWN"].map((v) => (
                  <button key={v} type="button" disabled={!!a} onClick={() => setAns({ ...ans, [r.id]: v })}
                    className={clsx("rounded-md border px-3 py-1 text-sm font-semibold", a === v ? (v === r.expected ? "border-ok bg-ok-soft" : "border-danger bg-danger-soft") : "border-line")}
                    data-testid={`game-${r.scenarioId}-${v}`}>
                    {v}
                  </button>
                ))}
              </div>
              {a && (
                <div role="status" className="mt-2 text-sm">
                  <p className={a === r.expected ? "font-semibold text-ok" : "font-semibold text-danger"}>
                    Expected: {r.expected}. {a === r.expected ? "You match the ground truth." : "Ground truth differs."}
                  </p>
                  <p className="mt-1">
                    Frozen v3 rule returned <strong>{r.v3Verdict}{r.v3Hint ? ` (${r.v3Hint})` : ""}</strong>
                    {r.v3Verdict !== r.expected ? <span className="font-semibold text-danger">: a rule error on this run</span> : ""}.
                  </p>
                  {r.v3Reason && <p className="mt-1 text-xs text-muted">Recorded reason: {r.v3Reason}</p>}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ------------------------------------------------------------------ loop stepper */
const STAGES = [
  { k: "CAPTURE", text: "AF_PACKET socket per brDN bridge port, ingress only; every PTP frame is tagged with the port it entered on and parsed by the frozen extractor (the same 56 columns as the campaign)." },
  { k: "DETECT", text: "Every 1 s, the frozen rule v3 (hash-checked at start-up) judges a 6 s sliding window. In parallel, the service-continuity channel tracks the last Announce from any provisioned master-role port. No decisions in the first 12 s (warm-up)." },
  { k: "LOCALISE", text: "Per-port role conformance against provisioning.json: unprovisioned port originating PTP; client-role port sending master-role messages; source identities not provisioned for that port; malformed frames." },
  { k: "DECIDE", text: "Policy table + persistence (ATTACK on ≥ 2 of the last 3 evaluations) + safety guard (never isolate a provisioned master-role port). At most 4 actions per run." },
  { k: "ACT", text: "ISOLATE: nftables bridge rule dropping ethertype 0x88F7 at the port. FAILOVER: start the cold-standby BC daemon. In the control arm the identical loop only logs would_act." },
  { k: "VERIFY", text: "pmc -d 24 on every non-isolated RU: parent ∈ provisioned master identities, GM ∈ allow-list, portState ∈ {SLAVE, UNCALIBRATED}, within 20 s. Recorded: all 41 verifications passed, median 0.3 s and at most 1.2 s after the action (RESULTS: \"within about 1 s\")." },
  { k: "ROLLBACK", text: "If verification fails: undo the action and escalate. No rollback was needed in any of the 140 runs." },
];
function Stepper({ onDone }: { onDone: () => void }) {
  const [i, setI] = useState(0);
  const [seen, setSeen] = useState<Set<number>>(new Set([0]));
  useEffect(() => {
    if (seen.size === STAGES.length) onDone();
  }, [seen, onDone]);
  const go = (k: number) => {
    setI(k);
    setSeen((s) => new Set(s).add(k));
  };
  return (
    <div>
      <ol className="flex flex-wrap gap-2" aria-label="Loop stages">
        {STAGES.map((s, k) => (
          <li key={s.k}>
            <button type="button" aria-current={i === k ? "step" : undefined} onClick={() => go(k)} className={clsx("rounded-md border px-3 py-2 text-sm font-semibold", i === k ? "border-accent bg-accent text-accent-ink" : seen.has(k) ? "border-accent bg-accent-soft" : "border-line")} data-testid={`stage-${k}`}>
              {k + 1}. {s.k}
            </button>
          </li>
        ))}
      </ol>
      <p className="mt-3 min-h-20" aria-live="polite">{STAGES[i].text}</p>
      <div className="mt-2 flex gap-2">
        <button type="button" disabled={i === 0} onClick={() => go(i - 1)} className="rounded-md border border-line px-3 py-1 disabled:opacity-50">Previous</button>
        <button type="button" disabled={i === STAGES.length - 1} onClick={() => go(i + 1)} className="rounded-md border border-line px-3 py-1 disabled:opacity-50">Next stage</button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ limits flip cards */
function FlipCards({ onDone }: { onDone: () => void }) {
  const [flipped, setFlipped] = useState<Set<number>>(new Set());
  useEffect(() => {
    if (flipped.size === LIMITS.length) onDone();
  }, [flipped, onDone]);
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {LIMITS.map((l, i) => (
        <li key={l.title}>
          <button type="button" aria-pressed={flipped.has(i)} onClick={() => setFlipped((s) => new Set(s).add(i))} className={clsx("h-full w-full rounded-lg border p-3 text-left", flipped.has(i) ? "border-warn bg-warn-soft" : "border-line hover:border-accent")} data-testid={`limit-${i}`}>
            <span className="font-semibold">{l.title}</span>
            {flipped.has(i) ? <span className="mt-1 block text-sm text-ink">{l.text} <span className="text-xs text-muted">({l.source})</span></span> : <span className="mt-1 block text-sm text-muted">Turn card</span>}
          </button>
        </li>
      ))}
    </ul>
  );
}
