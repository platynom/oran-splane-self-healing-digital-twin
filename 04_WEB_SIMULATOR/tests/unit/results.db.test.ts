/**
 * Reproduces the headline numbers of 03_RECOVERY_LOOP_S-PLANE/RESULTS_2026-10-05.md and of the 168-run campaign
 * (EVALUATION_V4.json) FROM THE DATABASE ROWS. Needs a database loaded with `npm run db:setup`.
 */
import "dotenv/config";
import { readFileSync } from "node:fs";
import path from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { PrismaClient } from "@prisma/client";
import { computeRunMetrics, isHealthy, legitParentsFor, median, wilson } from "@/lib/metrics";
import { evaluateHypotheses, type Agg } from "@/lib/hypotheses";
import { getCampaignSummary, getLatencySummary, getRunFacts } from "@/lib/data";

const prisma = new PrismaClient();
const REPO = path.resolve(__dirname, "..", "..", "..");
const EVAL_RL = JSON.parse(readFileSync(path.join(REPO, "03_RECOVERY_LOOP_S-PLANE/results/EVALUATION_RL.json"), "utf8")) as {
  runs: Record<string, unknown>[];
  summary: Record<string, Record<string, { unhealthy_s_median: number; restored_at_end: number }>>;
};
const r1 = (x: number) => Math.round(x * 10) / 10;

let aggs: Agg[] = [];
const agg = (sc: string, arm: string) => aggs.find((a) => a.scenarioId === sc && a.arm === arm)!;

beforeAll(async () => {
  aggs = (await prisma.scenarioAggregate.findMany()) as Agg[];
});
afterAll(async () => prisma.$disconnect());

describe("dataset loaded", () => {
  it("has 140 recovery runs (14 scenarios x 2 arms x 5 replicates) and 168 campaign runs", async () => {
    expect(await prisma.run.count()).toBe(140);
    expect(await prisma.run.count({ where: { arm: "loop" } })).toBe(70);
    expect((await prisma.run.findMany({ distinct: ["rep"], select: { rep: true } })).map((r) => r.rep).sort()).toEqual([13, 14, 15, 16, 17]);
    expect(await prisma.campaignRun.count()).toBe(168);
    expect(aggs).toHaveLength(28);
  });
});

describe("RESULTS_2026-10-05.md section 1 headline (median RU1/RU2 unhealthy seconds of 40)", () => {
  const cases: [string, number, number][] = [
    ["A1_rogue_master", 38.5, 2.0],
    ["C1_removal", 39.0, 2.5],
    ["C3_wholesecond", 38.5, 2.0],
  ];
  it.each(cases)("%s: control %s s vs loop %s s", (sc, ctrl, loop) => {
    expect(r1(agg(sc, "control").unhealthyMedian)).toBe(ctrl);
    expect(r1(agg(sc, "loop").unhealthyMedian)).toBe(loop);
    expect(agg(sc, "control").restoredAtEnd).toBe(0); // "5/5 never recovered"
    expect(agg(sc, "loop").restoredAtEnd).toBe(5);
  });
  it("A2, A3, A5, A8, C2: 0 s impact in both arms, isolation executed and verified 5/5", () => {
    for (const sc of ["A2_sync_spoof", "A3_replay", "A5_dos_flood", "A8_rogue_bc", "C2_malformed"]) {
      expect(agg(sc, "control").unhealthyMedian).toBe(0);
      expect(agg(sc, "loop").unhealthyMedian).toBe(0);
      expect(agg(sc, "loop").disruptiveExecuted).toBe(5);
      expect(agg(sc, "loop").verifyOk).toBe(5);
    }
  });
  it("matches EVALUATION_RL.json summary for every scenario and arm", () => {
    for (const [sc, arms] of Object.entries(EVAL_RL.summary)) {
      for (const [arm, s] of Object.entries(arms)) {
        expect(agg(sc, arm).unhealthyMedian).toBe(s.unhealthy_s_median);
        expect(agg(sc, arm).restoredAtEnd).toBe(s.restored_at_end);
      }
    }
  });
});

describe("pre-registered hypotheses (RESULTS section 2)", () => {
  it("H1 PASS, H2 PASS, H3 FAIL (1/25), H4 PASS, control integrity PASS", async () => {
    const h = evaluateHypotheses(aggs, await getRunFacts());
    const v = Object.fromEntries(h.map((x) => [x.id, x.pass]));
    expect(v).toEqual({ H1: true, H2: true, H3: false, H4: true, CI: true });
    const h3 = h.find((x) => x.id === "H3")!;
    expect(h3.summary).toContain("1 disruptive action in 25 benign loop runs");
    expect(h3.summary).toContain("[0.007, 0.195]");
    expect(h3.detail).toEqual(["B3_pdv_congestion r17: 1 executed disruptive action(s)"]);
  });
  it("Wilson 95 % interval of 1/25 is [0.007, 0.195]", () => {
    const [, lo, hi] = wilson(1, 25);
    expect(lo.toFixed(3)).toBe("0.007");
    expect(hi.toFixed(3)).toBe("0.195");
  });
  it("control integrity: 0 executed in 70 control runs, 41 would_act logged, no rl table, no bcs.log", async () => {
    const facts = await getRunFacts();
    const ctrl = facts.filter((f) => f.arm === "control");
    expect(ctrl).toHaveLength(70);
    expect(ctrl.reduce((a, f) => a + f.executedActions, 0)).toBe(0);
    expect(aggs.filter((a) => a.arm === "control").reduce((a, x) => a + x.disruptiveWouldAct, 0)).toBe(41);
    expect(ctrl.filter((f) => /table bridge rl/.test(f.nftFinal))).toHaveLength(0);
    expect(ctrl.filter((f) => f.standbyLogPresent)).toHaveLength(0);
  });
  it("section 5 artefact cross-check: 35/35 isolations in the final nft ruleset, 6/6 standby activations with a bcs.log", async () => {
    const loopRuns = await prisma.run.findMany({ where: { arm: "loop" }, include: { events: { where: { kind: "act" } } } });
    const iso = loopRuns.flatMap((r) => r.events.filter((e) => e.action === "ISOLATE_PTP_AT_PORT").map((e) => ({ r, e })));
    expect(iso).toHaveLength(35);
    expect(iso.every(({ r, e }) => r.nftFinal.includes(`rl-isolate-${e.target}`))).toBe(true);
    const sb = loopRuns.filter((r) => r.events.some((e) => e.action === "ACTIVATE_STANDBY_BC"));
    expect(sb).toHaveLength(6);
    expect(sb.every((r) => r.standbyLogPresent)).toBe(true);
  });
});

describe("timing (RESULTS: detection about 1.1 s, action about 2.1 s, verification within about 1 s)", () => {
  it("medians over attack-scenario loop runs", async () => {
    const l = await getLatencySummary();
    expect(l.detectionMedian).toBeGreaterThan(1.0);
    expect(l.detectionMedian).toBeLessThan(1.2);
    expect(l.actionMedian).toBeGreaterThan(2.0);
    expect(l.actionMedian).toBeLessThan(2.2);
    expect(l.verifyLagMedian).toBeLessThan(1.5);
  });
});

describe("RESULTS section 3: B3 replicate 17", () => {
  it("control 16.5 s unhealthy, loop 3.5 s, standby activated at about T0 + 5.1 s", async () => {
    const c = await prisma.run.findUniqueOrThrow({ where: { id: "B3_pdv_congestion__r17__control" } });
    const l = await prisma.run.findUniqueOrThrow({ where: { id: "B3_pdv_congestion__r17__loop" }, include: { events: { where: { kind: "act" } } } });
    expect(r1(c.unhealthyS)).toBe(16.5);
    expect(r1(l.unhealthyS)).toBe(3.5);
    expect(l.events).toHaveLength(1);
    expect(l.events[0].action).toBe("ACTIVATE_STANDBY_BC");
    expect(l.firstActionS).toBeCloseTo(5.07, 2); // analyse.py's first_action_s; RESULTS quotes "T0 + 5.1 s"
    expect(l.events[0].t).toBeCloseTo(l.firstActionS!, 1);
  });
});

describe("RESULTS section 4: corrected measurements", () => {
  it("A8 control: RU1/RU2 parent never left the real BC", async () => {
    const n = await prisma.sample.count({ where: { run: { scenarioId: "A8_rogue_bc", arm: "control" }, node: { in: ["ru1", "ru2"] }, t: { gte: 0 }, NOT: { parent: "020000fffe000001" } } });
    expect(n).toBe(0);
  });
  it("C3 control: RU1/RU2 re-parented to the forger 020000.fffe.00000a-2", async () => {
    const forger = await prisma.sample.findMany({ where: { run: { scenarioId: "C3_wholesecond", arm: "control" }, parentPort: "020000.fffe.00000a-2" }, distinct: ["runId"], select: { runId: true } });
    expect(forger).toHaveLength(5);
  });
});

describe("every run re-scored from the database equals EVALUATION_RL.json", () => {
  it("all 140 runs, all outcome fields", async () => {
    const runs = await prisma.run.findMany({ include: { samples: true, events: { where: { source: "loop" } } } });
    let checked = 0;
    for (const run of runs) {
      const ref = EVAL_RL.runs.find((x) => x.run === run.id)! as Record<string, unknown>;
      const samples = [...run.samples].sort((a, b) => a.round - b.round || a.id - b.id);
      const events = [...run.events].sort((a, b) => a.t - b.t || a.id - b.id);
      const m = computeRunMetrics(samples, events, new Set(run.legitParents), run.t0Mono);
      expect(m.unhealthyS, run.id).toBe(ref.unhealthy_s);
      expect(m.ru3UnhealthyS, run.id).toBe(ref.ru3_unhealthy_s);
      expect(m.rogueParentS, run.id).toBe(ref.rogue_parent_s);
      expect(m.restoredAtEnd, run.id).toBe(ref.restored_at_end);
      expect(m.preT0ServiceOk, run.id).toBe(ref.pre_t0_service_ok_fraction);
      expect(m.outageS, run.id).toBe(ref.outage_s);
      expect(m.firstAttackVerdictS, run.id).toBe(ref.first_attack_verdict_s);
      expect(m.firstActionS, run.id).toBe(ref.first_action_s);
      // the stored healthy flag is exactly the pre-registered definition applied to the stored fields
      const legit = legitParentsFor(run.legitParents.find((p) => p === "020000fffe0000b1"));
      for (const s of samples) expect(s.healthy).toBe(isHealthy(s, legit));
      checked++;
    }
    expect(checked).toBe(140);
  });
});

describe("168-run detection campaign (EVALUATION_V4.json)", () => {
  it("v3: sensitivity 95/96 = 0.990, specificity 47/60 = 0.783, abstention 12/12, attribution 84/96 = 0.875", async () => {
    const c = await getCampaignSummary();
    expect([c.v3.tp, c.v3.nAttack]).toEqual([95, 96]);
    expect((c.v3.tp / c.v3.nAttack).toFixed(3)).toBe("0.990");
    expect([c.v3.tn, c.v3.nBenign]).toEqual([47, 60]);
    expect((c.v3.tn / c.v3.nBenign).toFixed(3)).toBe("0.783");
    expect([c.v3.abstain, c.v3.nUnknown]).toEqual([12, 12]);
    expect(c.v3.attributed).toBe(84);
  });
  it("pre-frozen base rule: sensitivity 60/96 = 0.625; v2 gives the same verdicts as v3 on all 168 runs", async () => {
    const c = await getCampaignSummary();
    expect(c.base.tp).toBe(60);
    const rows = await prisma.campaignRun.findMany();
    expect(rows.filter((r) => r.v2Verdict !== r.v3Verdict)).toHaveLength(0);
    // additive-only: no run where the base rule said ATTACK and v3 did not
    expect(rows.filter((r) => r.baseVerdict === "ATTACK" && r.v3Verdict !== "ATTACK")).toHaveLength(0);
  });
  it("B_bc_replacement is the open failure (0/12) and the ambiguous case abstains 12/12", async () => {
    const c = await getCampaignSummary();
    expect(c.v3.perScenario.B_bc_replacement).toMatchObject({ correct: 0, n: 12 });
    expect(c.v3.perScenario.B_unplanned_failover).toMatchObject({ correct: 12, n: 12 });
  });
});

describe("fault catalogue", () => {
  it("contains A1-A8 and B1-B8 with Source, Destination, Attack devices and Consequence", async () => {
    const f = await prisma.fault.findMany({ where: { kind: "catalogue" } });
    expect(f.map((x) => x.id).sort()).toEqual(["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]);
    for (const x of f) {
      expect(x.source, x.id).toBeTruthy();
      expect(x.destination, x.id).toBeTruthy();
      expect(x.attackDevices, x.id).toBeTruthy();
      expect(x.consequence, x.id).toBeTruthy();
    }
    expect(await prisma.fault.count({ where: { kind: "campaign scenario" } })).toBe(6);
  });
});

describe("provenance", () => {
  it("records the archive hashes that match the published SHA256SUMS", async () => {
    const info = await prisma.datasetInfo.findUniqueOrThrow({ where: { id: 1 } });
    const prov = info.provenance as { sources: { path: string; sha256: string }[]; ruleWindows?: { agreement_w6: number } };
    const sums = readFileSync(path.join(REPO, "03_RECOVERY_LOOP_S-PLANE/results/SHA256SUMS.txt"), "utf8");
    const tgz = prov.sources.find((s) => s.path.endsWith("recovery_eval_runs_r13-r17.tgz"))!;
    expect(sums).toContain(`${tgz.sha256}  recovery_eval_runs_r13-r17.tgz`);
    const camp = prov.sources.find((s) => s.path.endsWith("splane_campaign_CORRECTED_2026-09-20.tgz"))!;
    expect(camp.sha256.startsWith("6149b4fb")).toBe(true);
    expect(prov.ruleWindows?.agreement_w6).toBeGreaterThan(0.99);
  });
  it("median helper", () => {
    expect(median([38.51, 38.51, 38.52, 38.53, 38.52])).toBe(38.52);
  });
});
