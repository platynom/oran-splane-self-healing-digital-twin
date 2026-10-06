"use client";
import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";
import clsx from "clsx";
import { architecture, isClickable, type Element } from "@/lib/architecture";
import type { Lls } from "@/lib/sim/state";
import { center, edge, LINKS, LLS_PATH, NODES, RU_SUB, VIEWBOX } from "./layout";

type VB = [number, number, number, number];

/** Animate the SVG viewBox between zoom targets (instant under prefers-reduced-motion). */
function useViewBox(target: VB, reduce: boolean) {
  const [vb, setVb] = useState<VB>(target);
  const cur = useRef<VB>(target);
  useEffect(() => {
    const from = cur.current;
    if (reduce || from.every((v, i) => v === target[i])) {
      cur.current = target;
      setVb(target);
      return;
    }
    let raf = 0;
    const t0 = performance.now();
    const D = 550;
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / D);
      const e = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2;
      const v = from.map((f, i) => f + (target[i] - f) * e) as VB;
      cur.current = v;
      setVb(v);
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target.join(","), reduce]);
  return vb;
}

const STROKE: Record<string, string> = {
  sync: "var(--sync)", freq: "var(--sync)", standby: "var(--muted)", mgmt: "var(--announce)", data: "var(--delay)",
  attack: "var(--danger)", dim: "var(--line)", radio: "var(--muted)",
};

export function Diagram({ level, lls, focus, zoom, onSelect }: {
  level: 1 | 2;
  lls: Lls;
  focus: string | null;
  zoom: "l1" | "l2" | "splane";
  onSelect: (id: string) => void;
}) {
  const reduce = !!useReducedMotion();
  const vb = useViewBox(VIEWBOX[zoom], reduce);
  const [tip, setTip] = useState<{ el: Element; x: number; y: number } | null>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const els = architecture.elements.filter((e) => NODES[e.id] && e.levels.includes(1));

  const showTip = (el: Element, ev: React.MouseEvent | React.FocusEvent) => {
    const r = wrap.current?.getBoundingClientRect();
    if (!r) return;
    const src = "clientX" in ev ? { x: ev.clientX, y: ev.clientY } : (() => {
      const b = (ev.currentTarget as SVGGElement).getBoundingClientRect();
      return { x: b.left + b.width / 2, y: b.bottom };
    })();
    setTip({ el, x: Math.min(src.x - r.left, r.width - 260), y: src.y - r.top + 14 });
  };

  return (
    <div ref={wrap} className="relative" data-testid="sim-diagram" data-level={level} data-zoom={zoom}>
      <svg
        viewBox={vb.map((v) => v.toFixed(2)).join(" ")}
        className="h-auto w-full rounded-xl border border-line bg-surface"
        role="group"
        aria-label={level === 1 ? "O-RAN architecture; the elements this project covers are highlighted" : `Open fronthaul, low-layer split ${lls.toUpperCase()}`}
        data-viewbox={VIEWBOX[zoom].join(" ")}
      >
        <defs>
          <marker id="arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L8,4 L0,8 z" fill="var(--muted)" />
          </marker>
        </defs>
        {LINKS.map(([a, b, kind]) => {
          const p = edge(NODES[a], NODES[b]), q = edge(NODES[b], NODES[a]);
          const muted = level === 2 && kind !== "attack";
          return (
            <line
              key={`${a}-${b}`}
              x1={p.x} y1={p.y} x2={q.x} y2={q.y}
              stroke={STROKE[kind]}
              strokeWidth={kind === "sync" ? 3 : 1.6}
              strokeDasharray={kind === "standby" || kind === "freq" || kind === "attack" || kind === "dim" ? "6 4" : undefined}
              opacity={muted ? 0.35 : kind === "dim" ? 0.6 : 1}
              markerEnd="url(#arr)"
            />
          );
        })}
        {level === 2 && <LlsOverlay lls={lls} />}
        {els.map((el) => {
          const b = NODES[el.id];
          const dim = el.tier === "dimmed";
          const click = isClickable(el);
          const sel = focus === el.id;
          const c = center(b);
          const tierCls = dim ? "sim-node-dim" : el.tier === 1 ? "sim-node-t1" : el.tier === 2 ? "sim-node-t2" : "sim-node-t3";
          return (
            <g
              key={el.id}
              data-testid={`node-${el.id}`}
              data-tier={String(el.tier)}
              data-clickable={click ? "true" : "false"}
              className={clsx("sim-node", tierCls, sel && "sim-node-sel", click && "cursor-pointer")}
              role={click ? "button" : "img"}
              tabIndex={0}
              aria-label={dim ? `${el.name}: ${el.role} Outside this project.` : `${el.name}. ${el.role}`}
              aria-pressed={click ? sel : undefined}
              onClick={click ? () => onSelect(el.id) : undefined}
              onKeyDown={click ? (e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  e.stopPropagation();
                  onSelect(el.id);
                }
              } : undefined}
              onMouseEnter={dim ? (e) => showTip(el, e) : undefined}
              onMouseMove={dim ? (e) => showTip(el, e) : undefined}
              onMouseLeave={dim ? () => setTip(null) : undefined}
              onFocus={dim ? (e) => showTip(el, e) : undefined}
              onBlur={dim ? () => setTip(null) : undefined}
            >
              <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={10} />
              <text x={c.x} y={el.id === "o-ru" ? b.y + 22 : c.y - (el.id === "smo-nonrt" ? 10 : 0)} textAnchor="middle" dominantBaseline="middle" className="sim-label">
                {shortName(el)}
              </text>
              {el.id === "smo-nonrt" && (
                <text x={c.x} y={c.y + 14} textAnchor="middle" dominantBaseline="middle" className="sim-sublabel">
                  {el.role}
                </text>
              )}
              {el.id === "o-ru" &&
                RU_SUB.map((r, i) => (
                  <g key={r}>
                    <rect x={b.x + 14 + i * 60} y={b.y + 48} width={52} height={36} rx={6} className="sim-sub" />
                    <text x={b.x + 40 + i * 60} y={b.y + 67} textAnchor="middle" dominantBaseline="middle" className="sim-sublabel">{r}</text>
                  </g>
                ))}
              {el.id === "o-ru" && (
                <text x={c.x} y={b.y + 112} textAnchor="middle" className="sim-sublabel">T-TSC (ptp4l clients)</text>
              )}
              {el.tier === 3 && (
                <text x={b.x + b.w - 6} y={b.y + 11} textAnchor="end" className="sim-tag">consequence</text>
              )}
            </g>
          );
        })}
      </svg>
      {tip && (
        <div
          role="tooltip"
          data-testid="sim-tooltip"
          className="pointer-events-none absolute z-20 w-64 rounded-md border border-line bg-surface-2 p-2 text-xs shadow-lg"
          style={{ left: Math.max(0, tip.x), top: tip.y }}
        >
          <p className="font-semibold">{tip.el.name}</p>
          <p className="mt-0.5">{tip.el.role}</p>
          <p className="mt-1 font-semibold text-muted">Outside this project.</p>
        </div>
      )}
    </div>
  );
}

function shortName(el: Element) {
  const map: Record<string, string> = {
    "gm-a": "GM-A (T-GM)", "gm-b": "GM-B (backup T-GM)", bc: "T-BC", "bc-standby": "Standby T-BC", "o-ru": "O-RU proxies",
    "fh-splane": "S-plane (PTP)", "fh-mplane": "M-plane", "fh-cplane": "C-plane", "fh-uplane": "U-plane", injector: "Injector (attacks)",
    "o-du": "O-DU", "smo-nonrt": "SMO / Non-RT RIC", "gnss-time": "GNSS / time source", synce: "SyncE (frequency)", "osc-drift": "Oscillator drift (B6)",
    "air-interface": "Air interface", ue: "UE", "near-rt-ric": "Near-RT RIC + xApps", "o-cu": "O-CU", "core-5g": "5G Core", "o-cloud": "O-Cloud",
  };
  return map[el.id] ?? el.name;
}

function LlsOverlay({ lls }: { lls: Lls }) {
  const testbed = !!architecture.elements.find((e) => e.id === `lls-${lls}`)?.lls?.testbed;
  const p = LLS_PATH[lls];
  return (
    <g data-testid="lls-overlay" data-lls={lls} data-testbed={testbed ? "true" : "false"} aria-hidden="true">
      <path d={p.d} fill="none" stroke={testbed ? "var(--accent)" : "var(--warn)"} strokeWidth={testbed ? 6 : 4} strokeDasharray={testbed ? undefined : "8 6"} strokeLinecap="round" opacity={0.85} />
      {p.glyph && (
        <g>
          <circle cx={p.glyph.x} cy={p.glyph.y} r={9} fill="var(--surface)" stroke="var(--warn)" strokeWidth={2} />
          <text x={p.glyph.x + 13} y={p.glyph.y - 10} className="sim-sublabel">{p.glyph.label}</text>
        </g>
      )}
      <text x={280} y={410} className="sim-sublabel">
        {`Timing path in LLS-${lls.toUpperCase()}${testbed ? " (closest match to the testbed: no O-DU in the timing chain; the lab has no PRTC)" : " (not the testbed's structure)"}`}
      </text>
    </g>
  );
}
