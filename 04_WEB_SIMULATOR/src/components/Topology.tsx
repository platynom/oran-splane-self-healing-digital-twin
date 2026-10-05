"use client";
/**
 * Network topology of the frozen G.8275.1 testbed (topology.sh + run_one.py), drawn as SVG.
 * Every dynamic element is driven by a ReplayState computed from recorded data:
 *   - RU colour, port state and parent arrow  <- observer samples (pmc -d 24, every 0.5 s)
 *   - isolated port / standby BC              <- loop.jsonl act / would_act events
 *   - moving packets                          <- per-0.5 s frame counts from the run's captures
 */
import { motion, useReducedMotion } from "framer-motion";
import { memo } from "react";
import type { Device, ReplayState } from "@/lib/replay";
import { DEVICE_LABEL } from "@/lib/replay";

type XY = { x: number; y: number };
const UP_Y = 122;
const DN_Y = 322;
const NW = 132; // node width
const NH = 56; // node height
const VB_W = 820;
const VB_H = 490;
const POS: Record<Device, XY> = {
  gma: { x: 170, y: 48 },
  gmb: { x: 350, y: 48 },
  bc: { x: 260, y: 222 },
  bcs: { x: 450, y: 222 },
  bc2: { x: 92, y: 222 },
  rbc: { x: 640, y: 222 },
  rogue: { x: 728, y: 222 },
  injector: { x: 735, y: 412 },
  ru1: { x: 150, y: 412 },
  ru2: { x: 370, y: 412 },
  ru3: { x: 590, y: 412 },
};
const PORT_LABEL: Partial<Record<Device, string>> = {
  bc: "p-v-bc-dn",
  bcs: "p-bcs-dn",
  bc2: "p-bc2-dn",
  rbc: "p-rbc-dn",
  rogue: "p-rogue",
  ru1: "p-v-ru1",
  ru2: "p-v-ru2",
  ru3: "p-v-ru3",
};
const PORT_TO_DEV: Record<string, Device> = Object.fromEntries(Object.entries(PORT_LABEL).map(([d, p]) => [p, d as Device]));

const TYPE_COLOR: Record<string, string> = {
  Sync: "var(--sync)",
  Follow_Up: "var(--sync)",
  Announce: "var(--announce)",
  Delay_Req: "var(--delay)",
  Delay_Resp: "var(--delay)",
};

export interface TopologyProps {
  scenarioId: string;
  state: ReplayState | null;
  packetsDn?: Record<string, Record<string, number>>;
  packetsUp?: Record<string, Record<string, number>>;
  binKey?: string; // changes every 0.5 s replay bin, restarts packet animation
  binSeconds?: number; // real seconds one bin lasts at the current speed
  playing?: boolean;
  title: string;
  highlight?: Device | null;
  onSelect?: (d: Device) => void;
  staticMode?: boolean; // lesson tour: no run data
}

/** Endpoints of the link a sender's frames travel on: device -> bus junction. */
function linkFor(dev: string, seg: "dn" | "up"): [XY, XY] | null {
  const d = POS[dev as Device];
  if (!d) return null;
  if (seg === "up") {
    if (dev === "gma" || dev === "gmb") return [{ x: d.x, y: d.y + NH / 2 }, { x: d.x, y: UP_Y }];
    if (dev === "bc" || dev === "bcs" || dev === "bc2" || dev === "rbc") return [{ x: d.x, y: d.y - NH / 2 }, { x: d.x, y: UP_Y }];
    return null;
  }
  if (dev === "bc" || dev === "bcs" || dev === "bc2" || dev === "rbc" || dev === "rogue") return [{ x: d.x, y: d.y + NH / 2 }, { x: d.x, y: DN_Y }];
  // the injector transmits through RU3's own port
  if (dev === "injector") return [{ x: POS.ru3.x + 30, y: POS.ru3.y - NH / 2 }, { x: POS.ru3.x + 30, y: DN_Y }];
  return [{ x: d.x, y: d.y - NH / 2 }, { x: d.x, y: DN_Y }];
}

function Packets({ counts, seg, binSeconds, binKey, dropped }: {
  counts: Record<string, Record<string, number>>;
  seg: "dn" | "up";
  binSeconds: number;
  binKey: string;
  dropped: Set<string>;
}) {
  const dots: React.ReactNode[] = [];
  for (const [sender, types] of Object.entries(counts)) {
    const link = linkFor(sender, seg);
    if (!link) continue;
    const [a, b] = link;
    const entries = Object.entries(types).sort((x, y) => y[1] - x[1]);
    let i = 0;
    for (const [type, n] of entries) {
      const k = Math.min(6, Math.max(1, Math.round(n / 8)));
      for (let j = 0; j < k && i < 10; j++, i++) {
        const delay = (i / 10) * binSeconds * 0.8;
        const stopAt = dropped.has(sender) ? 0.75 : 1;
        dots.push(
          <motion.circle
            key={`${binKey}-${seg}-${sender}-${type}-${j}`}
            r={3.2}
            fill={TYPE_COLOR[type] ?? "var(--other)"}
            initial={{ cx: a.x, cy: a.y, opacity: 0 }}
            animate={{ cx: a.x + (b.x - a.x) * stopAt, cy: a.y + (b.y - a.y) * stopAt, opacity: [0, 1, 1, 0] }}
            transition={{ duration: Math.max(0.12, binSeconds * 0.6), delay, ease: "linear" }}
          />,
        );
      }
    }
  }
  return <g aria-hidden="true">{dots}</g>;
}

function rate(counts: Record<string, number> | undefined) {
  if (!counts) return 0;
  return Object.values(counts).reduce((a, b) => a + b, 0) * 2; // frames per second (0.5 s bins)
}

function TopologyInner({
  scenarioId, state, packetsDn = {}, packetsUp = {}, binKey = "0", binSeconds = 0.5, playing = false, title, highlight, onSelect, staticMode,
}: TopologyProps) {
  const reduce = useReducedMotion();
  const sc = scenarioId;
  const has = {
    rogue: sc === "A1_rogue_master",
    rbc: sc === "A8_rogue_bc",
    injector: ["A2_sync_spoof", "A3_replay", "A5_dos_flood", "C2_malformed", "C3_wholesecond"].includes(sc),
    bc2: sc === "B_bc_replacement",
  };
  const t = state?.t ?? -999;
  const faultOn = !!state?.faultActive;
  const isolated = new Set((state?.isolatedPorts ?? []).map((p) => PORT_TO_DEV[p]).filter(Boolean));
  const would = new Set((state?.wouldIsolate ?? []).map((p) => PORT_TO_DEV[p]).filter(Boolean));
  // the injector sits in RU3's namespace: isolating p-v-ru3 isolates it too
  if (isolated.has("ru3")) isolated.add("injector");
  if (would.has("ru3")) would.add("injector");
  const standbyOn = !!state?.standbyActive;
  const attackerOn = staticMode || (faultOn && t >= 0);

  const nodeBox = (d: Device, opts: { dim?: boolean; tone?: "danger" | "ok" | "warn" | "neutral"; sub?: string; dashed?: boolean } = {}) => {
    const p = POS[d];
    const w = NW;
    const h = NH;
    const stroke = opts.tone === "danger" ? "var(--danger)" : opts.tone === "ok" ? "var(--ok)" : opts.tone === "warn" ? "var(--warn)" : "var(--line)";
    const fill = opts.tone === "danger" ? "var(--danger-soft)" : opts.tone === "ok" ? "var(--ok-soft)" : opts.tone === "warn" ? "var(--warn-soft)" : "var(--surface)";
    const label = DEVICE_LABEL[d];
    const interactive = !!onSelect;
    return (
      <g
        key={d}
        transform={`translate(${p.x - w / 2},${p.y - h / 2})`}
        opacity={opts.dim ? 0.45 : 1}
        role={interactive ? "button" : undefined}
        tabIndex={interactive ? 0 : undefined}
        aria-label={interactive ? `${label}${opts.sub ? `: ${opts.sub}` : ""}` : undefined}
        onClick={interactive ? () => onSelect!(d) : undefined}
        onKeyDown={interactive ? (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onSelect!(d)) : undefined}
        style={{ cursor: interactive ? "pointer" : undefined }}
      >
        <rect width={w} height={h} rx={8} fill={fill} stroke={highlight === d ? "var(--accent)" : stroke} strokeWidth={highlight === d ? 3 : 2} strokeDasharray={opts.dashed ? "5 4" : undefined} />
        <text x={w / 2} y={23} textAnchor="middle" fontSize={18} fontWeight={700} fill="var(--ink)">
          {label}
        </text>
        {opts.sub && (
          <text x={w / 2} y={44} textAnchor="middle" fontSize={13} fill="var(--muted)">
            {opts.sub}
          </text>
        )}
      </g>
    );
  };

  const link = (from: XY, to: XY, opts: { cut?: boolean; isolated?: boolean; would?: boolean; dim?: boolean; key: string; label?: string }) => (
    <g key={opts.key} opacity={opts.dim ? 0.4 : 1}>
      <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={opts.cut || opts.isolated ? "var(--danger)" : "var(--line)"} strokeWidth={opts.isolated ? 4 : 3} strokeDasharray={opts.cut ? "6 5" : undefined} />
      {opts.isolated && (
        <g transform={`translate(${to.x},${to.y + (to.y === DN_Y && from.y < DN_Y ? -16 : 16)})`}>
          <rect x={-13} y={-13} width={26} height={26} rx={5} fill="var(--danger)" />
          <path d="M-6 -6 L6 6 M6 -6 L-6 6" stroke="var(--surface)" strokeWidth={3} />
        </g>
      )}
      {opts.would && !opts.isolated && (
        <g transform={`translate(${to.x},${to.y + (to.y === DN_Y && from.y < DN_Y ? -16 : 16)})`}>
          <rect x={-13} y={-13} width={26} height={26} rx={5} fill="none" stroke="var(--muted)" strokeDasharray="3 3" strokeWidth={2} />
        </g>
      )}
      {opts.label && (
        <text x={to.x + 5} y={to.y - (to.y === DN_Y ? 7 : -16)} fontSize={12} fill="var(--muted)" fontFamily="var(--font-mono)">
          {opts.label}
        </text>
      )}
    </g>
  );

  const ruTone = (n: "ru1" | "ru2" | "ru3") => {
    if (staticMode || !state) return "neutral" as const;
    const v = state.nodes[n];
    if (!v || v.portState === null) return "neutral" as const;
    return v.healthy ? ("ok" as const) : ("danger" as const);
  };

  const parentArrow = (n: "ru1" | "ru2" | "ru3") => {
    if (!state || staticMode) return null;
    const v = state.nodes[n];
    const pd = v?.parentDevice;
    if (!pd || pd === "self") return null;
    const target = POS[pd as Device];
    if (!target) return null;
    const bad = !v.healthy;
    const stroke = bad ? "var(--danger)" : "var(--accent)";
    const marker = bad ? "url(#arr-bad)" : "url(#arr-ok)";
    if (pd === "injector") {
      // same row as the RUs: arc below the nodes
      const fx = POS[n].x - 20, tx = target.x - 20, y0 = POS[n].y + NH / 2, depth = 40 + (n === "ru1" ? 24 : n === "ru2" ? 12 : 0);
      return <path key={`par-${n}`} d={`M${fx},${y0} C${fx},${y0 + depth} ${tx},${y0 + depth} ${tx},${y0 + 2}`} fill="none" stroke={stroke} strokeWidth={3} markerEnd={marker} opacity={0.9} />;
    }
    const off = n === "ru1" ? -28 : n === "ru2" ? 0 : 28;
    const from = { x: POS[n].x - 30, y: POS[n].y - NH / 2 };
    const to = { x: target.x + off, y: target.y + NH / 2 + 2 };
    const midY = (from.y + to.y) / 2;
    return (
      <path
        key={`par-${n}`}
        d={`M${from.x},${from.y} C${from.x},${midY} ${to.x},${midY} ${to.x},${to.y}`}
        fill="none"
        stroke={stroke}
        strokeWidth={3}
        markerEnd={marker}
        opacity={0.9}
      />
    );
  };

  const ruSub = (n: "ru1" | "ru2" | "ru3") => {
    if (staticMode || !state) return "radio unit";
    const v = state.nodes[n];
    return v?.portState ?? "–";
  };

  const dropped = new Set<string>([...isolated].map(String));
  const bcCut = !!state?.bcDownstreamDown;
  const ru3Cut = !!state?.ru3LinkDown;
  const gmaDown = !!state?.gmaDown;
  const bcGone = !!state?.bcReplaced;
  const showDots = !staticMode && playing && !reduce;

  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} role="img" aria-labelledby={`topo-title-${title.replace(/\W/g, "")}`} className="h-auto w-full">
        <title id={`topo-title-${title.replace(/\W/g, "")}`}>{title}</title>
        <defs>
          <marker id="arr-ok" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--accent)" />
          </marker>
          <marker id="arr-bad" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--danger)" />
          </marker>
        </defs>
        {/* bridges */}
        <line x1={20} y1={UP_Y} x2={VB_W - 20} y2={UP_Y} stroke="var(--muted)" strokeWidth={6} strokeLinecap="round" />
        <text x={VB_W - 22} y={UP_Y - 10} textAnchor="end" fontSize={14} fontWeight={700} fill="var(--muted)">brUP · grandmasters</text>
        <line x1={20} y1={DN_Y} x2={VB_W - 20} y2={DN_Y} stroke="var(--muted)" strokeWidth={6} strokeLinecap="round" />
        <text x={VB_W - 22} y={DN_Y + 22} textAnchor="end" fontSize={14} fontWeight={700} fill="var(--muted)">brDN · radio units</text>

        {/* links */}
        {link({ x: POS.gma.x, y: POS.gma.y + NH / 2 }, { x: POS.gma.x, y: UP_Y }, { key: "l-gma", dim: gmaDown })}
        {link({ x: POS.gmb.x, y: POS.gmb.y + NH / 2 }, { x: POS.gmb.x, y: UP_Y }, { key: "l-gmb" })}
        {link({ x: POS.bc.x, y: POS.bc.y - NH / 2 }, { x: POS.bc.x, y: UP_Y }, { key: "l-bc-up", dim: bcGone })}
        {link({ x: POS.bc.x, y: POS.bc.y + NH / 2 }, { x: POS.bc.x, y: DN_Y }, { key: "l-bc-dn", cut: bcCut, dim: bcGone, isolated: isolated.has("bc"), label: "p-v-bc-dn" })}
        {link({ x: POS.bcs.x, y: POS.bcs.y - NH / 2 }, { x: POS.bcs.x, y: UP_Y }, { key: "l-bcs-up", dim: !standbyOn })}
        {link({ x: POS.bcs.x, y: POS.bcs.y + NH / 2 }, { x: POS.bcs.x, y: DN_Y }, { key: "l-bcs-dn", dim: !standbyOn, label: "p-bcs-dn" })}
        {has.bc2 && link({ x: POS.bc2.x, y: POS.bc2.y - NH / 2 }, { x: POS.bc2.x, y: UP_Y }, { key: "l-bc2-up", dim: !attackerOn })}
        {has.bc2 && link({ x: POS.bc2.x, y: POS.bc2.y + NH / 2 }, { x: POS.bc2.x, y: DN_Y }, { key: "l-bc2-dn", dim: !attackerOn, label: "p-bc2-dn" })}
        {has.rbc && link({ x: POS.rbc.x, y: POS.rbc.y - NH / 2 }, { x: POS.rbc.x, y: UP_Y }, { key: "l-rbc-up", dim: !attackerOn })}
        {has.rbc && link({ x: POS.rbc.x, y: POS.rbc.y + NH / 2 }, { x: POS.rbc.x, y: DN_Y }, { key: "l-rbc-dn", dim: !attackerOn, isolated: isolated.has("rbc"), would: would.has("rbc"), label: "p-rbc-dn" })}
        {(["ru1", "ru2", "ru3"] as const).map((n) =>
          link({ x: POS[n].x, y: POS[n].y - NH / 2 }, { x: POS[n].x, y: DN_Y }, {
            key: `l-${n}`,
            cut: n === "ru3" && ru3Cut,
            isolated: isolated.has(n),
            would: would.has(n),
            label: PORT_LABEL[n],
          }),
        )}
        {has.rogue && link({ x: POS.rogue.x, y: POS.rogue.y + NH / 2 }, { x: POS.rogue.x, y: DN_Y }, { key: "l-rogue", dim: !attackerOn, isolated: isolated.has("rogue"), would: would.has("rogue"), label: "p-rogue" })}

        {/* packets */}
        {showDots && <Packets counts={packetsUp} seg="up" binSeconds={binSeconds} binKey={binKey} dropped={dropped} />}
        {showDots && <Packets counts={packetsDn} seg="dn" binSeconds={binSeconds} binKey={binKey} dropped={dropped} />}

        {/* parent arrows */}
        {(["ru1", "ru2", "ru3"] as const).map(parentArrow)}

        {/* nodes */}
        {nodeBox("gma", { dim: gmaDown, sub: gmaDown ? "stopped at T0" : `grandmaster${!staticMode ? ` · ${rate(packetsUp.gma)}/s` : ""}` })}
        {nodeBox("gmb", { sub: `backup GM${!staticMode ? ` · ${rate(packetsUp.gmb)}/s` : ""}` })}
        {nodeBox("bc", { dim: bcGone, tone: bcCut ? "warn" : "neutral", sub: bcGone ? "withdrawn at T0" : bcCut ? "downstream blackholed" : `boundary clock${!staticMode ? ` · ${rate(packetsDn.bc)}/s` : ""}` })}
        {nodeBox("bcs", { dim: !standbyOn && !staticMode, tone: standbyOn ? "ok" : "neutral", dashed: !standbyOn, sub: standbyOn ? `active · ${rate(packetsDn.bcs)}/s` : state?.standbyWouldAct ? "would activate (control)" : "cold standby, daemon off" })}
        {has.bc2 && nodeBox("bc2", { dim: !attackerOn, sub: "provisioned (ticket)" })}
        {has.rbc && nodeBox("rbc", { dim: !attackerOn, tone: attackerOn ? "danger" : "neutral", sub: isolated.has("rbc") ? "isolated" : "relays GM-A, +1 step" })}
        {has.rogue && nodeBox("rogue", { dim: !attackerOn, tone: attackerOn ? "danger" : "neutral", sub: isolated.has("rogue") ? "isolated" : `unprovisioned${!staticMode ? ` · ${rate(packetsDn.rogue)}/s` : ""}` })}
        {nodeBox("ru1", { tone: ruTone("ru1"), sub: ruSub("ru1") })}
        {nodeBox("ru2", { tone: ruTone("ru2"), sub: ruSub("ru2") })}
        {nodeBox("ru3", { tone: ruTone("ru3"), sub: ruSub("ru3") })}
        {has.injector && (
          <g opacity={attackerOn ? 1 : 0.4}>
            <path d={`M${POS.ru3.x + NW / 2},${POS.ru3.y} L${POS.injector.x - NW / 2 + 4},${POS.injector.y}`} stroke="var(--danger)" strokeDasharray="4 4" strokeWidth={2} />
            <g transform={`translate(${POS.injector.x - NW / 2 + 4},${POS.injector.y - NH / 2})`}>
            <rect width={NW - 8} height={NH} rx={8} fill={attackerOn ? "var(--danger-soft)" : "var(--surface)"} stroke="var(--danger)" strokeDasharray="5 4" strokeWidth={2} />
            <text x={(NW - 8) / 2} y={23} textAnchor="middle" fontSize={18} fontWeight={700} fill="var(--ink)">Injector</text>
            <text x={(NW - 8) / 2} y={44} textAnchor="middle" fontSize={13} fill="var(--muted)">
              {isolated.has("injector") ? "cut with p-v-ru3" : `in RU3 netns${!staticMode ? ` · ${rate(packetsDn.injector)}/s` : ""}`}
            </text>
            </g>
          </g>
        )}
      </svg>
      <figcaption className="sr-only">
        {title}. {staticMode ? "Static testbed diagram." : describe(state)}
      </figcaption>
    </figure>
  );
}

function describe(s: ReplayState | null) {
  if (!s) return "";
  const ru = (["ru1", "ru2", "ru3"] as const).map((n) => `${n.toUpperCase()} ${s.nodes[n].portState ?? "unknown"}, parent ${s.nodes[n].parentDevice ?? "none"}, ${s.nodes[n].healthy ? "healthy" : "not healthy"}`);
  return `At T0 ${s.t >= 0 ? "+" : ""}${s.t.toFixed(1)} s: ${ru.join("; ")}.${s.isolatedPorts.length ? ` Isolated: ${s.isolatedPorts.join(", ")}.` : ""}${s.standbyActive ? " Standby BC active." : ""}`;
}

export const Topology = memo(TopologyInner);
