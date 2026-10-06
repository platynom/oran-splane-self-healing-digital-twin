/**
 * Load the derived dataset (data/derived/*.json.gz, produced by ingest/extract.py from the real archives)
 * into PostgreSQL, then recompute every run metric and per-scenario aggregate FROM THE DATABASE ROWS.
 *
 *   npm run db:ingest            (after `npm run db:push`)
 *
 * The script refuses to finish if a metric recomputed from the DB differs from the value the extractor
 * recomputed independently in Python (which itself matched EVALUATION_RL.json).
 */
import { PrismaClient, Prisma } from "@prisma/client";
import { existsSync, readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import path from "node:path";
import { ingestExtra } from "./ingest-extra";
import { computeRunMetrics, DISRUPTIVE, legitParentsFor, median } from "../src/lib/metrics";

const prisma = new PrismaClient();
const DIR = path.join(__dirname, "..", "data", "derived");
const load = <T>(f: string): T => JSON.parse(gunzipSync(readFileSync(path.join(DIR, f))).toString("utf8")) as T;

/* eslint-disable @typescript-eslint/no-explicit-any */
type DerivedRun = any;

const SCENARIO_ORDER = [
  "A1_rogue_master", "A2_sync_spoof", "A3_replay", "A5_dos_flood", "A8_rogue_bc", "C1_removal", "C2_malformed",
  "C3_wholesecond", "baseline", "B2_gm_failover", "B3_pdv_congestion", "B7_topology_change", "B_bc_replacement",
  "B_unplanned_failover",
];

async function main() {
  const scenarios = load<any[]>("scenarios.json.gz");
  const runs = load<DerivedRun[]>("recovery_runs.json.gz");
  const camp = load<any[]>("campaign_runs.json.gz");
  const { faults, lookAlikes } = load<{ faults: any[]; lookAlikes: any[] }>("faults.json.gz");
  const provenance = JSON.parse(readFileSync(path.join(DIR, "provenance.json"), "utf8"));

  if (process.argv.includes("--if-empty") && (await prisma.run.count()) > 0) {
    if ((await prisma.campaignEvidence.count()) === 0) await ingestExtra(prisma); // database created by an older version
    console.log("evidence tables already loaded (--if-empty): skipping ingest");
    return;
  }
  console.log("clearing evidence tables");
  await prisma.$transaction([
    prisma.sample.deleteMany(), prisma.event.deleteMany(), prisma.packetSeries.deleteMany(), prisma.ruleWindow.deleteMany(),
    prisma.scenarioAggregate.deleteMany(), prisma.run.deleteMany(), prisma.campaignRun.deleteMany(),
    prisma.fault.deleteMany(), prisma.lookAlike.deleteMany(), prisma.scenario.deleteMany(), prisma.datasetInfo.deleteMany(),
  ]);

  await prisma.scenario.createMany({
    data: scenarios.map((s) => ({
      id: s.id, code: s.code, cls: s.cls, title: s.title, expectedVerdict: s.expectedVerdict, source: s.source,
      destination: s.destination, attackDevices: s.attackDevices, consequence: s.consequence,
      sortOrder: SCENARIO_ORDER.indexOf(s.id),
    })),
  });

  console.log(`loading ${runs.length} recovery runs`);
  for (const r of runs) {
    await prisma.run.create({
      data: {
        id: r.id, scenarioId: r.scenario, rep: r.rep, arm: r.arm, t0Mono: r.t0Mono, tStartRel: r.tStartRel,
        tEndRel: r.tEndRel, maintenanceWindowOpen: r.maintenanceWindowOpen, params: r.params, state: r.state,
        legitParents: r.legitParents, nftFinal: r.nftFinal, standbyLogPresent: r.standbyLogPresent,
        pcapAnchor: r.pcapAnchor, maxProvisionedAnnounceGapS: r.maxProvisionedAnnounceGapS, announceGaps: r.announceGaps ?? [],
        // placeholders, replaced below by values recomputed from the stored rows
        unhealthyS: -1, ru3UnhealthyS: -1, rogueParentS: -1, restoredAtEnd: false, preT0ServiceOk: -1,
      },
    });
    await prisma.sample.createMany({
      data: r.samples.map((s: any) => ({
        runId: r.id, round: s.round, tMono: s.tMono, t: s.t, tRound: s.tRound, node: s.node, portState: s.portState, parent: s.parent,
        parentPort: s.parentPort, gm: s.gm, gmClockClass: s.gmClockClass, stepsRemoved: s.stepsRemoved, healthy: s.healthy,
      })),
    });
    const ev = [
      ...r.events.map((e: any) => ({
        runId: r.id, t: e.t, tMono: e.tMono, source: "loop", kind: e.kind, verdict: e.verdict ?? null, hint: e.hint ?? null,
        action: e.action ?? null, target: e.target ?? null, ok: e.ok ?? null, detail: e.detail ?? Prisma.JsonNull,
      })),
      ...r.ptp4l.map((e: any) => {
        const { t, node, kind, ...rest } = e;
        return { runId: r.id, t, source: "ptp4l", kind, node, detail: rest };
      }),
    ];
    await prisma.event.createMany({ data: ev });
    await prisma.packetSeries.create({ data: { runId: r.id, bins: r.packets } });
  }

  console.log("recomputing run metrics from the database rows");
  const mismatches: string[] = [];
  const dbRuns = await prisma.run.findMany({ select: { id: true, scenarioId: true, legitParents: true, t0Mono: true } });
  const pyCheck = new Map(runs.map((r) => [r.id, r.crossCheck]));
  for (const run of dbRuns) {
    const samples = await prisma.sample.findMany({ where: { runId: run.id }, orderBy: [{ round: "asc" }, { id: "asc" }] });
    const events = await prisma.event.findMany({ where: { runId: run.id }, orderBy: [{ t: "asc" }, { id: "asc" }] });
    const m = computeRunMetrics(samples, events, new Set(run.legitParents), run.t0Mono);
    const py = pyCheck.get(run.id);
    for (const k of ["unhealthy_s", "ru3_unhealthy_s", "restored_at_end", "pre_t0_service_ok_fraction"] as const) {
      const mine = { unhealthy_s: m.unhealthyS, ru3_unhealthy_s: m.ru3UnhealthyS, restored_at_end: m.restoredAtEnd,
        pre_t0_service_ok_fraction: m.preT0ServiceOk }[k];
      if (py[k] !== mine) mismatches.push(`${run.id} ${k}: db=${mine} extractor=${py[k]}`);
    }
    // the healthy flag stored per sample must equal the definition applied to the stored fields
    const legit = legitParentsFor(run.legitParents.find((p) => !["020000fffe000001", "020000fffe0000c5"].includes(p)));
    const { isHealthy } = await import("../src/lib/metrics");
    for (const s of samples) if (s.healthy !== isHealthy(s, legit)) mismatches.push(`${run.id} sample ${s.id} healthy flag`);
    await prisma.run.update({ where: { id: run.id }, data: m });
  }
  if (mismatches.length) {
    console.error(mismatches.slice(0, 20).join("\n"));
    throw new Error(`${mismatches.length} metric mismatches between DB recomputation and extractor`);
  }

  console.log("computing per-scenario aggregates from the database");
  for (const sc of scenarios) {
    for (const arm of ["control", "loop"]) {
      const rr = await prisma.run.findMany({ where: { scenarioId: sc.id, arm }, orderBy: { rep: "asc" },
        include: { events: { where: { source: "loop" } } } });
      if (!rr.length) continue;
      const acts = rr.flatMap((r) => r.events.filter((e) => (e.kind === "act" || e.kind === "would_act") && DISRUPTIVE.has(e.action ?? "")));
      const verifies = rr.flatMap((r) => r.events.filter((e) => e.kind === "verify"));
      await prisma.scenarioAggregate.create({
        data: {
          scenarioId: sc.id, arm, n: rr.length,
          unhealthyMedian: median(rr.map((r) => r.unhealthyS)),
          unhealthyEach: rr.map((r) => r.unhealthyS),
          restoredAtEnd: rr.filter((r) => r.restoredAtEnd).length,
          ru3UnhealthyEach: rr.map((r) => r.ru3UnhealthyS),
          firstAttackVerdictEach: rr.map((r) => r.firstAttackVerdictS ?? NaN).filter((x) => !Number.isNaN(x)),
          firstActionEach: rr.map((r) => r.firstActionS ?? NaN).filter((x) => !Number.isNaN(x)),
          disruptiveExecuted: acts.filter((a) => a.kind === "act").length,
          disruptiveWouldAct: acts.filter((a) => a.kind === "would_act").length,
          actionKinds: [...new Set(acts.map((a) => `${a.action}:${a.target}`))].sort(),
          verifyOk: verifies.filter((v) => v.ok).length,
          verifyTotal: verifies.length,
          rollbacks: rr.flatMap((r) => r.events.filter((e) => e.kind === "rollback")).length,
          runsWithEscalation: rr.filter((r) => r.events.some((e) => e.kind === "escalate")).length,
        },
      });
    }
  }

  console.log(`loading ${camp.length} campaign runs, ${faults.length} faults, ${lookAlikes.length} look-alikes`);
  await prisma.campaignRun.createMany({
    data: camp.map((c) => ({
      id: c.id, scenarioId: c.scenario, rep: c.rep, expected: c.expected, truthClass: c.truthClass, truthFault: c.truthFault,
      description: c.description, nPackets: c.nPackets, baseVerdict: c.baseVerdict, baseHint: c.baseHint,
      v2Verdict: c.v2Verdict, v2Hint: c.v2Hint, v3Verdict: c.v3Verdict, v3Hint: c.v3Hint, v3Reason: c.v3Reason,
    })),
  });
  await prisma.fault.createMany({
    data: faults.map((f) => ({
      id: f.id, scenarioId: f.scenario ?? null, name: f.name, cls: f.cls, kind: f.kind, source: f.source,
      destination: f.destination, attackDevices: f.attackDevices, consequence: f.consequence, detectableNow: f.detectableNow,
      evidence: f.evidence, thresholdBasis: f.thresholdBasis ?? null, missing: f.missing ?? null, mechanism: f.mechanism ?? null,
      signature: f.signature ?? null, reasoning: f.reasoning ?? null, lookAlike: f.lookAlike ?? null, citations: f.citations ?? null,
      testbedRequired: f.testbedRequired ?? null, threatId: f.threatId ?? null, sourceFile: f.sourceFile,
    })),
  });
  await prisma.lookAlike.createMany({
    data: lookAlikes.map((l) => ({
      symptom: l["Shared symptom"], benign: l["Benign explanation"], attack: l["Attack explanation"],
      discriminator: l["THE discriminator (decisive test)"], within2s: l["Decidable within 2 s?"], citations: l["Standard / source"],
    })),
  });
  const rwPath = path.join(DIR, "rule_windows.json.gz");
  if (existsSync(rwPath)) {
    const rw = load<{ summary: Record<string, unknown>; runs: Record<string, Record<string, unknown[]>> }>("rule_windows.json.gz");
    const rows = Object.entries(rw.runs).flatMap(([runId, byW]) => Object.entries(byW).map(([w, seq]) => ({ runId, window: Number(w), seq: seq as Prisma.InputJsonValue })));
    await prisma.ruleWindow.createMany({ data: rows });
    provenance.ruleWindows = rw.summary;
    console.log(`loaded ${rows.length} rule-window verdict sequences (W=6 agreement with live verdicts: ${rw.summary.agreement_w6})`);
  } else {
    console.warn("rule_windows.json.gz not found: the sandbox will only offer the pre-registered 6 s window");
  }
  await prisma.datasetInfo.create({ data: { id: 1, provenance } });
  const counts = await Promise.all([prisma.run.count(), prisma.sample.count(), prisma.event.count(), prisma.campaignRun.count(), prisma.fault.count()]);
  await ingestExtra(prisma);
  console.log(`done: runs=${counts[0]} samples=${counts[1]} events=${counts[2]} campaign=${counts[3]} faults=${counts[4]}`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
