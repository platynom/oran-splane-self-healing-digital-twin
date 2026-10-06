/**
 * Key recorded events of one run (loop.jsonl plus RU port-state changes from ptp4l) and the recovery-loop
 * stage reached at time t. Every stage is derived from a recorded loop.jsonl record; nothing is interpolated.
 *
 *   detect   first eval with verdict ATTACK at or after T0
 *   localise first eval at or after T0 whose violations name a switch port (the per-port attribution)
 *   decide   act / would_act / escalate record (the loop logs the decision and the action in one record)
 *   act      act record (executed); control arm logs would_act instead, which is never executed
 *   verify   verify record
 *   rollback rollback record (none in the 140 recorded runs)
 */
import type { ReplayEvent, ReplayRun } from "../replay";
import { actionLabel, hintLabel } from "../replay";

export const STAGES = ["detect", "localise", "decide", "act", "verify", "rollback"] as const;
export type Stage = (typeof STAGES)[number];

export interface KeyEvent {
  t: number;
  kind: string;
  label: string;
  stage: Stage | null;
}

const portsOf = (e: ReplayEvent) => Object.keys(((e.detail ?? {}) as { violations?: Record<string, unknown> }).violations ?? {});

export function keyEvents(run: Pick<ReplayRun, "events" | "scenarioId">): KeyEvent[] {
  const out: KeyEvent[] = [];
  if (run.scenarioId !== "baseline") out.push({ t: 0, kind: "onset", label: "Fault onset (T0)", stage: null });
  let detected = false;
  let localised = false;
  let lastVerdict: string | null = null;
  for (const e of run.events) {
    if (e.source === "loop") {
      if (e.kind === "eval") {
        const v = `${e.verdict}|${e.hint}`;
        if (e.t < 0) {
          lastVerdict = v; // pre-onset verdicts only set the baseline for change detection
          continue;
        }
        if (!detected && e.verdict === "ATTACK") {
          detected = true;
          out.push({ t: e.t, kind: "detect", label: `Rule verdict ATTACK (${hintLabel(e.hint) || "no hint"})`, stage: "detect" });
        } else if (v !== lastVerdict) {
          out.push({ t: e.t, kind: "eval", label: `Rule verdict ${e.verdict}${e.hint ? ` (${hintLabel(e.hint)})` : ""}`, stage: null });
        }
        lastVerdict = v;
        const ports = portsOf(e);
        if (!localised && ports.length) {
          localised = true;
          out.push({ t: e.t, kind: "localise", label: `Violation attributed to port ${ports.join(", ")}`, stage: "localise" });
        }
      } else if (e.kind === "act") {
        out.push({ t: e.t, kind: "decide", label: `Decision: ${actionLabel(e.action)} ${e.target ?? ""}`.trim(), stage: "decide" });
        out.push({ t: e.t, kind: "act", label: `Executed: ${actionLabel(e.action)} ${e.target ?? ""}`.trim(), stage: "act" });
      } else if (e.kind === "would_act") {
        out.push({ t: e.t, kind: "would_act", label: `Decision logged, not executed (observe-only): ${actionLabel(e.action)} ${e.target ?? ""}`.trim(), stage: "decide" });
      } else if (e.kind === "escalate") {
        out.push({ t: e.t, kind: "escalate", label: "Escalated to operator (no automatic action)", stage: "decide" });
      } else if (e.kind === "verify") {
        out.push({ t: e.t, kind: "verify", label: `Verification ${e.ok ? "passed" : "FAILED"}`, stage: "verify" });
      } else if (e.kind === "rollback") {
        out.push({ t: e.t, kind: "rollback", label: `Rollback ${e.target ?? ""}`.trim(), stage: "rollback" });
      }
    } else if (e.kind === "port_state" && e.t >= 0 && e.node && /^ru[123]$/.test(e.node)) {
      const d = (e.detail ?? {}) as Record<string, unknown>;
      out.push({ t: e.t, kind: "port_state", label: `${e.node.toUpperCase()} port ${String(d.from_)} → ${String(d.to)}`, stage: null });
    }
  }
  // stable sort: same-time records keep their logged order (decide before act)
  return out.map((k, i) => [k, i] as const).sort((a, b) => a[0].t - b[0].t || a[1] - b[1]).map(([k]) => k);
}

const EPS = 1e-6;
export function nextEventTime(evs: KeyEvent[], t: number): number | null {
  const e = evs.find((k) => k.t > t + EPS);
  return e ? e.t : null;
}
export function prevEventTime(evs: KeyEvent[], t: number): number | null {
  for (let i = evs.length - 1; i >= 0; i--) if (evs[i].t < t - EPS) return evs[i].t;
  return null;
}

/** For each stage: the recorded time it was reached (<= t), or null if not (yet) reached. */
export function stagesAt(evs: KeyEvent[], t: number): Record<Stage, KeyEvent | null> {
  const r = Object.fromEntries(STAGES.map((s) => [s, null])) as Record<Stage, KeyEvent | null>;
  for (const e of evs) if (e.stage && e.t <= t + EPS && !r[e.stage]) r[e.stage] = e;
  return r;
}

/** Stages that occur anywhere in the run (used to grey out stages this run never reaches). */
export function stagesInRun(evs: KeyEvent[]): Set<Stage> {
  return new Set(evs.flatMap((e) => (e.stage ? [e.stage] : [])));
}
