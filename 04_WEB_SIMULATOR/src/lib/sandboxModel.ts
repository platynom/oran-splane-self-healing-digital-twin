/**
 * What-if MODEL of the recovery loop's decision flow (not measured data).
 *
 * It replays the decision logic of 03_RECOVERY_LOOP_S-PLANE/code/recovery_loop.py (Loop.decide) over inputs
 * recorded in the CONTROL run of the chosen scenario and replicate, where nothing was done:
 *   - channel 1: the frozen rule's verdict at each live evaluation tick, for the chosen window W. These were
 *     computed by running the frozen rule on the recorded capture (ingest/rule_windows.py); W = 6 s is checked
 *     against the verdicts logged live.
 *   - localisation: whether the live 6 s window at that tick had a violating port that is not a provisioned
 *     master-role port (taken from the live log for every W: an assumption the UI states).
 *   - channel 2: gaps between Announce frames from the provisioned master ports on brDN, from the capture.
 *   - outcome: the control run's RU1/RU2 health per observer round. After the first action the model assumes
 *     health returns after the median recovery latency measured in the loop runs for that action.
 */

export interface SandboxParams {
  window: number; // s, one of the recomputed windows
  persistK: number;
  persistN: number;
  serviceLossS: number;
  serviceLossMaintS: number;
}

export const PREREGISTERED: SandboxParams = { window: 6, persistK: 2, persistN: 3, serviceLossS: 2, serviceLossMaintS: 10 };

export interface Tick {
  t: number;
  verdicts: Record<string, string>; // window -> verdict
  hints: Record<string, string | null>;
  isolatable: boolean;
  violatingPorts: string[];
}

export interface CaseInput {
  scenarioId: string;
  rep: number;
  cls: string;
  maintenance: boolean;
  ticks: Tick[];
  announceGaps: [number, number | null][];
  controlRounds: [number, boolean][]; // [t, RU1&RU2 healthy]
  controlUnhealthyS: number;
  controlWouldAct: { t: number; action: string; target: string }[];
  loop: { unhealthyS: number; actions: { t: number; action: string; target: string }[]; restoredAtEnd: boolean };
}

export interface RecoveryLatency {
  ISOLATE_PTP_AT_PORT: number;
  ACTIVATE_STANDBY_BC: number;
  perScenario: Record<string, Partial<Record<"ISOLATE_PTP_AT_PORT" | "ACTIVATE_STANDBY_BC", number>>>;
}

export type FlowNode = "capture" | "detect" | "service" | "persist" | "localise" | "guard" | "isolate" | "failover" | "escalate" | "tolerate";

export interface ModelAction {
  t: number;
  action: "ISOLATE_PTP_AT_PORT" | "ACTIVATE_STANDBY_BC";
  target: string;
  reason: string;
}

export interface ModelResult {
  actions: ModelAction[];
  escalations: { t: number; reason: string }[];
  firstAttackT: number | null;
  predictedUnhealthyS: number;
  latencyUsed: number | null;
  path: FlowNode[];
  disruptive: number;
  notes: string[];
}

/** Last provisioned-master Announce at or before t, from the recorded gaps (Announce otherwise every <= 0.4 s). */
function lastAnnounceBefore(gaps: [number, number | null][], t: number): number {
  for (const [a, b] of gaps) {
    if (a <= t && (b === null || t < b)) return a;
  }
  return t; // inside normal cadence: an Announce arrived less than 0.4 s ago
}

export function runModel(c: CaseInput, p: SandboxParams, lat: RecoveryLatency): ModelResult {
  const W = String(p.window);
  const hist: string[] = [];
  const actions: ModelAction[] = [];
  const esc: { t: number; reason: string }[] = [];
  const escalated = new Set<string>();
  const path = new Set<FlowNode>(["capture", "detect", "service"]);
  let standby = false;
  let isolated = false;
  let firstAttackT: number | null = null;
  const notes: string[] = [];
  const escalate = (t: number, why: string) => {
    if (escalated.has(why)) return;
    escalated.add(why);
    esc.push({ t, reason: why });
    path.add("escalate");
  };
  for (const tick of c.ticks) {
    if (actions.length >= 4) break;
    const t = tick.t;
    // channel 2 first, exactly as Loop.decide
    if (!standby) {
      const last = lastAnnounceBefore(c.announceGaps, t);
      const limit = c.maintenance ? p.serviceLossMaintS : p.serviceLossS;
      if (t - last > limit) {
        actions.push({ t, action: "ACTIVATE_STANDBY_BC", target: "bcs", reason: `no Announce from a provisioned master port for ${(t - last).toFixed(1)} s (> ${limit} s)` });
        standby = true;
        path.add("failover");
        continue;
      }
    }
    const v = tick.verdicts[W] ?? "NO_EVIDENCE";
    hist.push(v);
    if (hist.length > p.persistN) hist.shift();
    if (v === "ATTACK" && t >= 0 && firstAttackT === null) firstAttackT = t;
    if (v === "UNKNOWN") escalate(t, "UNKNOWN verdict");
    const votes = hist.filter((h) => h === "ATTACK").length;
    if (v === "ATTACK") path.add("persist");
    if (votes < p.persistK || v !== "ATTACK") continue;
    if (isolated) continue;
    path.add("localise");
    if (tick.isolatable) {
      const target = tick.violatingPorts[0] ?? "violating port";
      actions.push({ t, action: "ISOLATE_PTP_AT_PORT", target, reason: `ATTACK (${tick.hints[W] ?? "?"}) on ${votes} of the last ${hist.length} evaluations` });
      isolated = true;
      path.add("isolate");
    } else {
      path.add("guard");
      escalate(t, `ATTACK (${tick.hints[W] ?? "?"}) with no isolatable violating port`);
    }
  }
  if (!actions.length && !esc.length) path.add("tolerate");

  // outcome
  let predicted = c.controlUnhealthyS;
  let latencyUsed: number | null = null;
  const first = actions[0];
  const controlHarm = c.controlUnhealthyS > 0.5;
  if (first && controlHarm) {
    const L = lat.perScenario[c.scenarioId]?.[first.action] ?? lat[first.action];
    latencyUsed = L;
    const until = Math.min(40, first.t + L);
    predicted = integrateUnhealthy(c.controlRounds, until);
    if (lat.perScenario[c.scenarioId]?.[first.action] === undefined) {
      notes.push(`No loop run of this scenario executed ${first.action}; the model uses the median recovery latency of that action across all scenarios (${L.toFixed(2)} s).`);
    }
  } else if (first && !controlHarm) {
    notes.push("The control run shows no RU1/RU2 harm, so the action cannot shorten anything. Its own effect on the radio units is not modelled; it is counted as a disruptive action.");
  }
  return {
    actions,
    escalations: esc,
    firstAttackT,
    predictedUnhealthyS: Math.round(predicted * 100) / 100,
    latencyUsed,
    path: [...path],
    disruptive: actions.length,
    notes,
  };
}

/** Seconds RU1/RU2 were unhealthy in [0, until], using the control run's observer rounds. */
export function integrateUnhealthy(rounds: [number, boolean][], until: number): number {
  const post = rounds.filter(([t]) => t >= 0 && t <= 40);
  let acc = 0;
  for (let i = 0; i + 1 < post.length; i++) {
    const [t0, ok] = post[i];
    if (t0 >= until) break;
    const t1 = Math.min(post[i + 1][0], until);
    if (!ok) acc += t1 - t0;
  }
  return acc;
}

/** Benign and ambiguous cases are where a disruptive action is harm (H3 / H4 definitions). */
export function isHarmCase(cls: string) {
  return cls === "benign" || cls === "healthy" || cls === "ambiguous";
}
