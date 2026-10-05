import "server-only";
import { prisma } from "./db";
import { evaluateHypotheses, type Agg, type RunFacts } from "./hypotheses";
import { DISRUPTIVE, median } from "./metrics";

export async function getScenarios() {
  return prisma.scenario.findMany({ orderBy: { sortOrder: "asc" } });
}

export async function getAggregates() {
  return prisma.scenarioAggregate.findMany({ orderBy: [{ scenarioId: "asc" }, { arm: "asc" }] });
}

export async function getRunFacts(): Promise<RunFacts[]> {
  const runs = await prisma.run.findMany({
    select: {
      scenarioId: true, arm: true, rep: true, nftFinal: true, standbyLogPresent: true,
      events: { where: { source: "loop", kind: { in: ["act", "verify"] } }, select: { kind: true, action: true, ok: true } },
    },
  });
  return runs.map((r) => ({
    scenarioId: r.scenarioId, arm: r.arm, rep: r.rep, nftFinal: r.nftFinal, standbyLogPresent: r.standbyLogPresent,
    isolateVerifiedOk: r.events.some((e) => e.kind === "verify" && e.action === "ISOLATE_PTP_AT_PORT" && e.ok),
    standbyVerifiedOk: r.events.some((e) => e.kind === "verify" && e.action === "ACTIVATE_STANDBY_BC" && e.ok),
    executedActions: r.events.filter((e) => e.kind === "act" && DISRUPTIVE.has(e.action ?? "")).length,
  }));
}

export async function getHypotheses() {
  const [aggs, facts] = await Promise.all([getAggregates(), getRunFacts()]);
  return evaluateHypotheses(aggs as Agg[], facts);
}

/** Loop-arm timing summary across all executed actions: detection and action latency after T0. */
export async function getLatencySummary() {
  const aggs = await prisma.scenarioAggregate.findMany({ where: { arm: "loop" } });
  const det = aggs.flatMap((a) => (a.scenarioId.startsWith("A") || a.scenarioId.startsWith("C") ? a.firstAttackVerdictEach : []));
  const act = aggs.flatMap((a) => (a.scenarioId.startsWith("A") || a.scenarioId.startsWith("C") ? a.firstActionEach : []));
  const verifies = await prisma.event.findMany({ where: { source: "loop", kind: { in: ["act", "verify"] } }, orderBy: [{ runId: "asc" }, { t: "asc" }] });
  const lag: number[] = [];
  let lastAct: { runId: string; t: number } | null = null;
  for (const e of verifies) {
    if (e.kind === "act") lastAct = { runId: e.runId, t: e.t };
    else if (lastAct && lastAct.runId === e.runId) lag.push(e.t - lastAct.t);
  }
  return { detectionMedian: median(det), actionMedian: median(act), verifyLagMedian: median(lag), verifyLagMax: Math.max(...lag), n: det.length };
}

export async function getCampaignSummary() {
  const rows = await prisma.campaignRun.findMany();
  const ALIAS: Record<string, string> = { A_intercept: "C1", A_malformed: "C2", A_wholesecond: "C3" };
  const score = (v: "baseVerdict" | "v2Verdict" | "v3Verdict", h: "baseHint" | "v2Hint" | "v3Hint") => {
    const A = rows.filter((r) => r.expected === "ATTACK"), B = rows.filter((r) => r.expected === "BENIGN"), U = rows.filter((r) => r.expected === "UNKNOWN");
    const perScenario: Record<string, { correct: number; n: number; expected: string }> = {};
    for (const r of rows) {
      const p = (perScenario[r.scenarioId] ??= { correct: 0, n: 0, expected: r.expected });
      p.n++;
      if (r[v] === r.expected) p.correct++;
    }
    return {
      tp: A.filter((r) => r[v] === "ATTACK").length, nAttack: A.length,
      tn: B.filter((r) => r[v] === "BENIGN").length, nBenign: B.length,
      abstain: U.filter((r) => r[v] === "UNKNOWN" && r[h] === "B2?").length, nUnknown: U.length,
      attributed: A.filter((r) => (ALIAS[r[h] ?? ""] ?? r[h]) === r.truthFault).length,
      perScenario,
    };
  };
  return { n: rows.length, base: score("baseVerdict", "baseHint"), v2: score("v2Verdict", "v2Hint"), v3: score("v3Verdict", "v3Hint") };
}

export async function getRunIndex() {
  return prisma.run.findMany({
    select: { id: true, scenarioId: true, rep: true, arm: true, unhealthyS: true, firstActionS: true },
    orderBy: [{ scenarioId: "asc" }, { rep: "asc" }, { arm: "asc" }],
  });
}

export async function getProvenance() {
  const d = await prisma.datasetInfo.findUnique({ where: { id: 1 } });
  return d;
}
