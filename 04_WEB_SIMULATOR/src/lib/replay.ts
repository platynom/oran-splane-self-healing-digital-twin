/**
 * Pure helpers that turn one recorded run (observer samples, loop events, ptp4l log lines and packet
 * counts, all from the database) into the state shown at replay time t. Nothing here invents data: every
 * field is a lookup into the recorded series at or before t.
 */

export type Device = "gma" | "gmb" | "bc" | "bcs" | "bc2" | "rbc" | "rogue" | "injector" | "ru1" | "ru2" | "ru3";

export interface ReplaySample {
  round: number;
  t: number;
  node: string;
  portState: string | null;
  parent: string | null;
  parentPort: string | null;
  gm: string | null;
  stepsRemoved: number | null;
  healthy: boolean;
}

export interface ReplayEvent {
  t: number;
  source: string; // loop | ptp4l
  kind: string;
  node: string | null;
  verdict: string | null;
  hint: string | null;
  action: string | null;
  target: string | null;
  ok: boolean | null;
  detail: Record<string, unknown> | null;
}

export type PacketBin = [seg: "dn" | "up", t: number, sender: string, msgType: string, count: number];

export interface ReplayRun {
  id: string;
  scenarioId: string;
  rep: number;
  arm: "control" | "loop";
  tStartRel: number;
  tEndRel: number;
  params: Record<string, unknown>;
  nftFinal: string;
  unhealthyS: number;
  restoredAtEnd: boolean;
  firstActionS: number | null;
  firstAttackVerdictS: number | null;
  samples: ReplaySample[];
  events: ReplayEvent[];
  packets: PacketBin[];
}

export const DEVICE_LABEL: Record<Device, string> = {
  gma: "GM-A",
  gmb: "GM-B",
  bc: "BC",
  bcs: "Standby BC",
  bc2: "Replacement BC",
  rbc: "Rogue BC",
  rogue: "Rogue GM",
  injector: "Injector",
  ru1: "RU1",
  ru2: "RU2",
  ru3: "RU3",
};

export const PORT_OF: Record<string, Device> = {
  "p-v-bc-dn": "bc",
  "p-bcs-dn": "bcs",
  "p-bc2-dn": "bc2",
  "p-rogue": "rogue",
  "p-rbc-dn": "rbc",
  "p-v-ru1": "ru1",
  "p-v-ru2": "ru2",
  "p-v-ru3": "ru3",
};

const OWN: Record<string, string> = { ru1: "020000fffe00000c", ru2: "020000fffe00000d", ru3: "020000fffe00000e" };

/** Map a parent clockIdentity seen by an RU to the device that owns it in this run. */
export function deviceOfIdentity(id: string | null, node: string, scenarioId: string, params: Record<string, unknown>): Device | "self" | null {
  if (!id) return null;
  if (id === OWN[node]) return "self";
  if (id === "020000fffe000001") return "bc";
  if (id === "020000fffe0000c5") return "bcs";
  if (id === "020000fffe0000b1") return "bc2";
  if (id === params.rogue_id) return "rogue";
  if (id === params.rbc_id_up) return "rbc";
  // C3: the forger in RU3's namespace uses GM-A's identity directly on the RU segment (RESULTS s4)
  if (scenarioId === "C3_wholesecond" && id === "020000fffe00000a") return "injector";
  if (id === "020000fffe00000a") return "gma";
  if (id === "020000fffe00000b") return "gmb";
  return null;
}

export interface NodeView {
  node: string;
  portState: string | null;
  parentDevice: Device | "self" | null;
  parentPort: string | null;
  gm: string | null;
  stepsRemoved: number | null;
  healthy: boolean;
  t: number | null;
}

export interface ReplayState {
  t: number;
  nodes: Record<string, NodeView>;
  isolatedPorts: string[]; // executed isolations (loop arm)
  wouldIsolate: string[]; // logged would_act isolations (control arm)
  standbyActive: boolean; // executed failover
  standbyWouldAct: boolean;
  faultActive: boolean;
  bcDownstreamDown: boolean; // C1
  bcReplaced: boolean; // B_bc_replacement: primary BC withdrawn at T0
  gmaDown: boolean; // B2 / B_unplanned: GM-A stopped at T0
  ru3LinkDown: boolean; // B7: RU3 link bounced for about 8 s
  verdict: string | null;
  hint: string | null;
  unhealthySoFar: number;
}

/** Last recorded sample per RU at or before t. */
export function stateAt(run: ReplayRun, t: number): ReplayState {
  const nodes: Record<string, NodeView> = {};
  for (const n of ["ru1", "ru2", "ru3"]) {
    nodes[n] = { node: n, portState: null, parentDevice: null, parentPort: null, gm: null, stepsRemoved: null, healthy: false, t: null };
  }
  for (const s of run.samples) {
    if (s.t > t) break;
    nodes[s.node] = {
      node: s.node,
      portState: s.portState,
      parentDevice: deviceOfIdentity(s.parent, s.node, run.scenarioId, run.params),
      parentPort: s.parentPort,
      gm: s.gm,
      stepsRemoved: s.stepsRemoved,
      healthy: s.healthy,
      t: s.t,
    };
  }
  const past = run.events.filter((e) => e.source === "loop" && e.t <= t);
  const isolated = past.filter((e) => e.kind === "act" && e.action === "ISOLATE_PTP_AT_PORT").map((e) => e.target!);
  const rolledBack = past.filter((e) => e.kind === "rollback").map((e) => e.target);
  const would = past.filter((e) => e.kind === "would_act" && e.action === "ISOLATE_PTP_AT_PORT").map((e) => e.target!);
  const lastEval = [...past].reverse().find((e) => e.kind === "eval");
  const sc = run.scenarioId;
  const ru3Down = run.events.find((e) => e.source === "ptp4l" && e.node === "ru3" && e.t >= 0 && e.kind === "port_state" && e.detail?.to === "FAULTY");
  const ru3Up = run.events.find((e) => e.source === "ptp4l" && e.node === "ru3" && ru3Down && e.t > ru3Down.t && e.kind === "port_state" && e.detail?.from_ === "FAULTY");
  return {
    t,
    nodes,
    isolatedPorts: isolated.filter((p) => !rolledBack.includes(p)),
    wouldIsolate: would,
    standbyActive: past.some((e) => e.kind === "act" && e.action === "ACTIVATE_STANDBY_BC"),
    standbyWouldAct: past.some((e) => e.kind === "would_act" && e.action === "ACTIVATE_STANDBY_BC"),
    faultActive: t >= 0 && sc !== "baseline",
    bcDownstreamDown: sc === "C1_removal" && t >= 0,
    bcReplaced: sc === "B_bc_replacement" && t >= 0,
    gmaDown: (sc === "B2_gm_failover" || sc === "B_unplanned_failover") && t >= 0,
    ru3LinkDown: sc === "B7_topology_change" && !!ru3Down && t >= ru3Down.t && (!ru3Up || t < ru3Up.t),
    verdict: lastEval?.verdict ?? null,
    hint: lastEval?.hint ?? null,
    unhealthySoFar: unhealthyUpTo(run, t),
  };
}

/** Seconds in [0, t] during which RU1 or RU2 was unhealthy (same round arithmetic as the primary metric). */
export function unhealthyUpTo(run: ReplayRun, t: number): number {
  const rounds = new Map<number, { t: number; ok: boolean; n: number }>();
  for (const s of run.samples) {
    if (s.node !== "ru1" && s.node !== "ru2") continue;
    const r = rounds.get(s.round) ?? { t: Infinity, ok: true, n: 0 };
    r.t = Math.min(r.t, s.t);
    r.ok = r.ok && s.healthy;
    r.n++;
    rounds.set(s.round, r);
  }
  const post = [...rounds.values()].map((r) => ({ t: r.t, ok: r.ok && r.n === 2 })).filter((r) => r.t >= 0 && r.t <= Math.min(40, t)).sort((a, b) => a.t - b.t);
  let acc = 0;
  for (let i = 0; i + 1 < post.length; i++) if (!post[i].ok) acc += post[i + 1].t - post[i].t;
  return acc;
}

/** Frame counts per sender for the 0.5 s bin containing t (segment brDN by default). */
export function packetsAt(run: ReplayRun, t: number, seg: "dn" | "up" = "dn") {
  const b = Math.floor(t / 0.5) * 0.5;
  const out: Record<string, Record<string, number>> = {};
  for (const [s, bt, sender, type, n] of run.packets) {
    if (s !== seg || Math.abs(bt - b) > 1e-6) continue;
    (out[sender] ??= {})[type] = n;
  }
  return out;
}

export interface TimelineMarker {
  t: number;
  kind: string;
  label: string;
  tone: "neutral" | "warn" | "danger" | "ok" | "accent";
}

const ACTION_LABEL: Record<string, string> = {
  ISOLATE_PTP_AT_PORT: "Isolate PTP at port",
  ACTIVATE_STANDBY_BC: "Activate standby BC",
};

/** The v3 rule's detector labels for the C scenarios (alias map from evaluate_v4.py). */
export const HINT_ALIAS: Record<string, string> = { A_intercept: "C1", A_malformed: "C2", A_wholesecond: "C3", "B2?": "unknown intent" };
export function hintLabel(h: string | null | undefined) {
  if (!h) return "";
  return HINT_ALIAS[h] ? `${h} = ${HINT_ALIAS[h]}` : h;
}

export function actionLabel(a: string | null | undefined) {
  return a ? ACTION_LABEL[a] ?? a : "";
}

export function markers(run: ReplayRun): TimelineMarker[] {
  const m: TimelineMarker[] = [];
  if (run.scenarioId !== "baseline") m.push({ t: 0, kind: "onset", label: "Fault onset (T0)", tone: "warn" });
  const firstAttack = run.events.find((e) => e.source === "loop" && e.kind === "eval" && e.verdict === "ATTACK" && e.t >= 0);
  if (firstAttack) m.push({ t: firstAttack.t, kind: "detect", label: `First ATTACK verdict (${hintLabel(firstAttack.hint) || "?"})`, tone: "danger" });
  for (const e of run.events) {
    if (e.source !== "loop") continue;
    if (e.kind === "act") m.push({ t: e.t, kind: "act", label: `${actionLabel(e.action)} ${e.target}`, tone: "accent" });
    if (e.kind === "would_act") m.push({ t: e.t, kind: "would_act", label: `Would ${actionLabel(e.action).toLowerCase()} ${e.target} (not executed)`, tone: "neutral" });
    if (e.kind === "verify") m.push({ t: e.t, kind: "verify", label: `Verification ${e.ok ? "passed" : "FAILED"}`, tone: e.ok ? "ok" : "danger" });
    if (e.kind === "rollback") m.push({ t: e.t, kind: "rollback", label: `Rollback ${e.target}`, tone: "danger" });
    if (e.kind === "escalate") m.push({ t: e.t, kind: "escalate", label: "Escalated to operator", tone: "warn" });
  }
  return m.sort((a, b) => a.t - b.t);
}
