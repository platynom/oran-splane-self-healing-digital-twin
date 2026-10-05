import "server-only";
import { prisma } from "./db";
import { median } from "./metrics";
import type { CaseInput, RecoveryLatency, Tick } from "./sandboxModel";

type Act = "ISOLATE_PTP_AT_PORT" | "ACTIVATE_STANDBY_BC";

/** Builds the sandbox model inputs from the database (recorded control runs, loop runs, recomputed rule windows). */
export async function buildSandboxData() {
  const runs = await prisma.run.findMany({
    include: {
      scenario: { select: { cls: true } },
      samples: { where: { node: { in: ["ru1", "ru2"] } }, select: { round: true, tRound: true, healthy: true }, orderBy: [{ round: "asc" }] },
      events: { where: { source: "loop", kind: { in: ["eval", "act", "would_act"] } }, select: { t: true, kind: true, verdict: true, hint: true, action: true, target: true, detail: true }, orderBy: [{ t: "asc" }] },
      windows: true,
    },
    orderBy: [{ scenarioId: "asc" }, { rep: "asc" }],
  });
  const rounds = (r: (typeof runs)[number]) => {
    const m = new Map<number, { t: number; ok: boolean; n: number }>();
    for (const s of r.samples) {
      const x = m.get(s.round) ?? { t: s.tRound, ok: true, n: 0 };
      x.ok = x.ok && s.healthy;
      x.n++;
      m.set(s.round, x);
    }
    return [...m.values()].map((x) => [x.t, x.ok && x.n === 2] as [number, boolean]).sort((a, b) => a[0] - b[0]);
  };
  // measured recovery latency after the first executed action, per scenario and action (loop runs)
  const latAll: Record<Act, number[]> = { ISOLATE_PTP_AT_PORT: [], ACTIVATE_STANDBY_BC: [] };
  const latSc: Record<string, Partial<Record<Act, number[]>>> = {};
  for (const r of runs.filter((x) => x.arm === "loop")) {
    const act = r.events.find((e) => e.kind === "act" && e.t >= 0);
    if (!act) continue;
    const rr = rounds(r).filter(([t]) => t >= 0 && t <= 40);
    if (!rr.some(([, ok]) => !ok)) continue; // no harm to recover from
    let lastBad = -1;
    rr.forEach(([t, ok]) => { if (!ok) lastBad = t; });
    const rec = rr.find(([t]) => t > lastBad);
    if (!rec) continue;
    const L = Math.max(0, rec[0] - act.t);
    const a = act.action as Act;
    latAll[a].push(L);
    ((latSc[r.scenarioId] ??= {})[a] ??= []).push(L);
  }
  const latency: RecoveryLatency = {
    ISOLATE_PTP_AT_PORT: median(latAll.ISOLATE_PTP_AT_PORT),
    ACTIVATE_STANDBY_BC: median(latAll.ACTIVATE_STANDBY_BC),
    perScenario: Object.fromEntries(Object.entries(latSc).map(([sc, v]) => [sc, Object.fromEntries(Object.entries(v).map(([a, xs]) => [a, median(xs!)]))])),
  };
  const cases: CaseInput[] = [];
  const windowsAvailable = new Set<number>();
  for (const c of runs.filter((x) => x.arm === "control")) {
    const l = runs.find((x) => x.arm === "loop" && x.scenarioId === c.scenarioId && x.rep === c.rep)!;
    const masters = new Set(["p-v-bc-dn", "p-bcs-dn", ...(c.scenarioId === "B_bc_replacement" ? ["p-bc2-dn"] : [])]);
    const byW = new Map(c.windows.map((w) => [w.window, w.seq as [number, string, string | null][]]));
    byW.forEach((_, w) => windowsAvailable.add(w));
    const evals = c.events.filter((e) => e.kind === "eval");
    const ticks: Tick[] = evals.map((e, i) => {
      const viol = Object.keys(((e.detail as { violations?: Record<string, unknown> } | null)?.violations) ?? {}).filter((p) => !masters.has(p));
      const verdicts: Record<string, string> = { "6": e.verdict ?? "NO_EVIDENCE" };
      const hints: Record<string, string | null> = { "6": e.hint };
      byW.forEach((seq, w) => {
        if (w === 6) return; // the live-logged verdicts are used for the pre-registered window
        const s = seq[i];
        if (s) { verdicts[String(w)] = s[1]; hints[String(w)] = s[2]; }
      });
      return { t: e.t, verdicts, hints, isolatable: viol.length > 0, violatingPorts: viol };
    });
    cases.push({
      scenarioId: c.scenarioId, rep: c.rep, cls: c.scenario.cls, maintenance: c.maintenanceWindowOpen, ticks,
      announceGaps: (c.announceGaps as [number, number | null][]) ?? [],
      controlRounds: rounds(c), controlUnhealthyS: c.unhealthyS,
      controlWouldAct: c.events.filter((e) => e.kind === "would_act").map((e) => ({ t: e.t, action: e.action!, target: e.target! })),
      loop: { unhealthyS: l.unhealthyS, restoredAtEnd: l.restoredAtEnd, actions: l.events.filter((e) => e.kind === "act").map((e) => ({ t: e.t, action: e.action!, target: e.target! })) },
    });
  }
  windowsAvailable.add(6);
  const info = await prisma.datasetInfo.findUnique({ where: { id: 1 } });
  const rw = (info?.provenance as { ruleWindows?: Record<string, unknown> } | null)?.ruleWindows ?? null;
  return { cases, latency, windows: [...windowsAvailable].sort((a, b) => a - b), ruleWindows: rw };
}
