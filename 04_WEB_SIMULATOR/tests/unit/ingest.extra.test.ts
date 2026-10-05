/** Row-count and idempotency checks for the 168-run campaign evidence, the 13 Sep pilot and B6 (database must be loaded). */
import "dotenv/config";
import { readFileSync } from "node:fs";
import path from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { PrismaClient } from "@prisma/client";
import { ingestExtra, loadExtra } from "../../scripts/ingest-extra";

const prisma = new PrismaClient();
afterAll(async () => prisma.$disconnect());
const inv = JSON.parse(readFileSync(path.join(__dirname, "..", "..", "data", "derived", "inventory_counts.json"), "utf8"));

describe("extra.json.gz (extraction output)", () => {
  it("all extraction checks passed", () => {
    const x = loadExtra();
    expect(x.checks.length).toBeGreaterThanOrEqual(14);
    expect(x.checks.filter((c: { ok: boolean }) => !c.ok)).toEqual([]);
  });
  it("counts equal the counts read from the source archives and JSON files (inventory)", () => {
    const x = loadExtra();
    expect(x.counts.campaign).toBe(inv.campaign_run_dirs_in_archive);
    expect(x.pilot.filter((p: { milestone: string }) => p.milestone === "S11")).toHaveLength(inv.s11_runs);
    expect(x.pilot.filter((p: { milestone: string }) => p.milestone === "S15")).toHaveLength(inv.s15_runs);
    expect(x.counts.campaignCsvRows).toBe(1451909); // "1,451,909 packet records with 56 fields each" (story guide)
  });
});

describe("database rows", () => {
  it("campaign evidence: 168 rows, one per CampaignRun, deep-CSV rows equal evidence.n_packets in every run", async () => {
    expect(await prisma.campaignEvidence.count()).toBe(168);
    expect(await prisma.campaignRun.count()).toBe(168);
    const ev = await prisma.campaignEvidence.findMany();
    expect(ev.filter((e) => e.csvRows !== e.nPacketsClaimed)).toEqual([]);
    expect(ev.reduce((a, e) => a + e.csvRows, 0)).toBe(1451909);
    for (const e of ev) expect(Object.values(e.msgTypeCounts as Record<string, number>).reduce((a, b) => a + b, 0), e.runId).toBe(e.csvRows);
  });
  it("campaign evidence supports the A1 r1 worked example (157 self-announces by the off-allow-list clock)", async () => {
    const e = await prisma.campaignEvidence.findUniqueOrThrow({ where: { runId: "A1_rogue_master__r1" } });
    const sa = (e.evidence as { unknown_selfannouncing_sources: Record<string, { self_announce_pkts: number }> }).unknown_selfannouncing_sources;
    expect(Object.values(sa)[0].self_announce_pkts).toBe(157);
  });
  it("pilot: 10 S11 + 30 S15 runs; S11 5/5 vs 0/5; S15 NOT ESTABLISHED with 14/15 and 8/15", async () => {
    expect(await prisma.pilotRun.count({ where: { milestone: "S11" } })).toBe(10);
    expect(await prisma.pilotRun.count({ where: { milestone: "S15" } })).toBe(30);
    const s11 = await prisma.pilotSummary.findUniqueOrThrow({ where: { id: "S11" } });
    const d11 = s11.data as { primary_outcome_summary: { action: { k: number }; no_action: { k: number } } };
    expect([d11.primary_outcome_summary.action.k, d11.primary_outcome_summary.no_action.k]).toEqual([5, 0]);
    const s15 = await prisma.pilotSummary.findUniqueOrThrow({ where: { id: "S15" } });
    expect(s15.status).toBe("NOT_ESTABLISHED");
    const d15 = s15.data as { sensitivity_trigger_rate_among_above_boundary: { k: number; n: number }; specificity_no_trigger_rate_among_below_boundary: { k: number; n: number } };
    expect([d15.sensitivity_trigger_rate_among_above_boundary.k, d15.sensitivity_trigger_rate_among_above_boundary.n, d15.specificity_no_trigger_rate_among_below_boundary.k, d15.specificity_no_trigger_rate_among_below_boundary.n]).toEqual([14, 15, 8, 15]);
  });
  it("B6: run 1 NOT ESTABLISHED (+20.161 ppm), run 2 ESTABLISHED (+21.013 ppm [20.623, 21.403]); raw CSVs not present", async () => {
    const b = await prisma.b6Measurement.findMany({ orderBy: { id: "asc" } });
    expect(b.map((x) => x.verdict)).toEqual(["NOT_ESTABLISHED", "ESTABLISHED"]);
    expect(b[0].relativePpm.toFixed(3)).toBe("20.161");
    expect(b[1].relativePpm.toFixed(3)).toBe("21.013");
    expect(b[1].ci95.map((x) => x.toFixed(3))).toEqual(["20.623", "21.403"]);
    expect(b.every((x) => x.rawCsvPresent === false)).toBe(true);
  });
  it("ingestExtra is idempotent: running it again leaves identical counts", async () => {
    const before = [await prisma.campaignEvidence.count(), await prisma.pilotRun.count(), await prisma.pilotSummary.count(), await prisma.b6Measurement.count()];
    const a = await ingestExtra(prisma);
    const b = await ingestExtra(prisma);
    expect(a).toEqual(b);
    const after = [await prisma.campaignEvidence.count(), await prisma.pilotRun.count(), await prisma.pilotSummary.count(), await prisma.b6Measurement.count()];
    expect(after).toEqual(before);
    expect(after).toEqual([168, 40, 2, 2]);
  });
  it("detector-campaign totals shown by the datasets API source: 14 scenarios x 12 replicates", async () => {
    const g = await prisma.campaignRun.groupBy({ by: ["scenarioId"], _count: true });
    expect(g).toHaveLength(14);
    expect(g.every((x) => x._count === 12)).toBe(true);
  });
});
