/**
 * The pre-registered hypotheses of 03_RECOVERY_LOOP_S-PLANE/PREREGISTRATION.md s5, evaluated on the
 * per-scenario aggregates that scripts/ingest.ts computed from the database rows.
 */
import { wilson } from "./metrics";

export const ATTACKS = [
  "A1_rogue_master", "A2_sync_spoof", "A3_replay", "A5_dos_flood", "A8_rogue_bc", "C1_removal", "C2_malformed", "C3_wholesecond",
] as const;
export const ISOLATION_SCENARIOS = ATTACKS.filter((s) => s !== "C1_removal");
export const BENIGN = ["baseline", "B2_gm_failover", "B3_pdv_congestion", "B7_topology_change", "B_bc_replacement"] as const;
export const AMBIGUOUS = "B_unplanned_failover";

export interface Agg {
  scenarioId: string;
  arm: string;
  n: number;
  unhealthyMedian: number;
  restoredAtEnd: number;
  disruptiveExecuted: number;
  disruptiveWouldAct: number;
  actionKinds: string[];
  verifyOk: number;
  verifyTotal: number;
  runsWithEscalation: number;
}

export interface RunFacts {
  scenarioId: string;
  arm: string;
  rep: number;
  nftFinal: string;
  standbyLogPresent: boolean;
  isolateVerifiedOk: boolean; // an executed ISOLATE whose verify passed
  standbyVerifiedOk: boolean; // an executed ACTIVATE_STANDBY_BC whose verify passed
  executedActions: number;
}

export interface HypothesisResult {
  id: "H1" | "H2" | "H3" | "H4" | "CI";
  title: string;
  pass: boolean;
  summary: string;
  detail: string[];
}

export function evaluateHypotheses(aggs: Agg[], runs: RunFacts[]): HypothesisResult[] {
  const get = (sc: string, arm: string) => aggs.find((a) => a.scenarioId === sc && a.arm === arm);
  // H1
  const h1d: string[] = [];
  let h1 = true;
  for (const sc of ATTACKS) {
    const c = get(sc, "control"), l = get(sc, "loop");
    if (!c || !l) { h1 = false; h1d.push(`${sc}: missing arm`); continue; }
    const restored = l.restoredAtEnd === l.n;
    const notWorse = l.unhealthyMedian <= c.unhealthyMedian;
    const big = c.unhealthyMedian >= 5;
    const halved = !big || l.unhealthyMedian <= 0.5 * c.unhealthyMedian;
    const ok = restored && notWorse && halved;
    if (!ok) h1 = false;
    const pct = big ? ` (${((100 * l.unhealthyMedian) / c.unhealthyMedian).toFixed(1)} % of control)` : " (no control impact: trivial pass)";
    h1d.push(`${sc}: loop restored ${l.restoredAtEnd}/${l.n}, median ${l.unhealthyMedian.toFixed(2)} s vs control ${c.unhealthyMedian.toFixed(2)} s${pct}`);
  }
  // H2
  const h2d: string[] = [];
  let h2 = true;
  for (const sc of ATTACKS) {
    const lr = runs.filter((r) => r.scenarioId === sc && r.arm === "loop");
    const k = lr.filter((r) => (sc === "C1_removal" ? r.standbyVerifiedOk : r.isolateVerifiedOk)).length;
    if (k < 4) h2 = false;
    h2d.push(`${sc}: ${sc === "C1_removal" ? "standby failover" : "isolation"} executed and verified in ${k}/${lr.length}`);
  }
  // H3
  const benignLoop = runs.filter((r) => (BENIGN as readonly string[]).includes(r.scenarioId) && r.arm === "loop");
  const disruptive = benignLoop.reduce((a, r) => a + r.executedActions, 0);
  const runsWith = benignLoop.filter((r) => r.executedActions > 0);
  const w = wilson(runsWith.length, benignLoop.length);
  // H4
  const amb = get(AMBIGUOUS, "loop");
  const h4 = !!amb && amb.disruptiveExecuted === 0 && amb.runsWithEscalation >= 4;
  // Control integrity
  const ctrl = runs.filter((r) => r.arm === "control");
  const ctrlExec = ctrl.reduce((a, r) => a + r.executedActions, 0);
  const rlTable = ctrl.filter((r) => /table bridge rl/.test(r.nftFinal)).length;
  const bcsLog = ctrl.filter((r) => r.standbyLogPresent).length;
  const wouldAct = aggs.filter((a) => a.arm === "control").reduce((a, x) => a + x.disruptiveWouldAct, 0);
  return [
    { id: "H1", title: "Restoration", pass: h1, summary: h1 ? "Loop restored 5/5 in all 8 attack scenarios" : "Not met", detail: h1d },
    { id: "H2", title: "Containment", pass: h2, summary: h2 ? "Isolation or failover executed and verified in every attack scenario" : "Not met", detail: h2d },
    {
      id: "H3", title: "No harm on benign faults", pass: disruptive === 0,
      summary: `${disruptive} disruptive action${disruptive === 1 ? "" : "s"} in ${benignLoop.length} benign loop runs (Wilson 95 % [${w[1].toFixed(3)}, ${w[2].toFixed(3)}])`,
      detail: runsWith.map((r) => `${r.scenarioId} r${r.rep}: ${r.executedActions} executed disruptive action(s)`),
    },
    {
      id: "H4", title: "Honest abstention", pass: h4,
      summary: amb ? `B_unplanned_failover: ${amb.disruptiveExecuted} actions, escalation in ${amb.runsWithEscalation}/${amb.n}` : "missing",
      detail: [],
    },
    {
      id: "CI", title: "Control integrity", pass: ctrlExec === 0 && rlTable === 0 && bcsLog === 0,
      summary: `${ctrlExec} executed actions in ${ctrl.length} control runs (${wouldAct} would_act logged)`,
      detail: [`control runs with an nft 'rl' table: ${rlTable}`, `control runs with a standby bcs.log: ${bcsLog}`],
    },
  ];
}
