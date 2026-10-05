/**
 * Idempotent load of data/derived/extra.json.gz (campaign evidence, 13 Sep pilot, B6) with row-count checks.
 * Used by scripts/ingest.ts and runnable on its own:  npx tsx scripts/ingest-extra.ts
 * Safe to run any number of times: each table is cleared and reloaded inside one transaction.
 */
import { PrismaClient, Prisma } from "@prisma/client";
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import path from "node:path";

/* eslint-disable @typescript-eslint/no-explicit-any */
export interface ExtraCounts {
  campaign: number;
  campaignCsvRows: number;
  pilot: number;
  pilotSummary: number;
  b6: number;
}

export function loadExtra(): any {
  return JSON.parse(gunzipSync(readFileSync(path.join(__dirname, "..", "data", "derived", "extra.json.gz"))).toString("utf8"));
}

export async function ingestExtra(prisma: PrismaClient): Promise<ExtraCounts> {
  const x = loadExtra();
  const failed = x.checks.filter((c: any) => !c.ok);
  if (failed.length) throw new Error(`extraction checks failed: ${failed.map((c: any) => c.name).join("; ")}`);
  const nCampaignRuns = await prisma.campaignRun.count();
  const known = new Set((await prisma.campaignRun.findMany({ select: { id: true } })).map((r) => r.id));
  const missing = x.campaign.filter((c: any) => !known.has(c.runId)).map((c: any) => c.runId);
  if (missing.length) throw new Error(`campaign evidence for runs not in CampaignRun: ${missing.slice(0, 3).join(", ")}`);
  const J = (v: unknown) => (v === null || v === undefined ? Prisma.JsonNull : (v as Prisma.InputJsonValue));
  await prisma.$transaction([
    prisma.campaignEvidence.deleteMany(),
    prisma.pilotRun.deleteMany(),
    prisma.pilotSummary.deleteMany(),
    prisma.b6Measurement.deleteMany(),
    prisma.campaignEvidence.createMany({
      data: x.campaign.map((c: any) => ({
        runId: c.runId, csvRows: c.csvRows, nPacketsClaimed: c.nPacketsClaimed, nAnnounce: c.nAnnounce, captureSpanS: c.captureSpanS,
        msgTypeCounts: c.msgTypeCounts, senderCounts: c.senderCounts, gmIdentities: c.gmIdentities, evidence: c.evidence,
        reasons: c.reasons, description: c.description,
      })),
    }),
    prisma.pilotRun.createMany({
      data: x.pilot.map((p: any) => ({ id: p.id, milestone: p.milestone, grp: p.group, label: p.label, triggered: p.triggered, actionExecuted: p.actionExecuted, outcome: p.outcome, data: J(p.data) })),
    }),
    prisma.pilotSummary.createMany({ data: x.pilotSummary.map((s: any) => ({ id: s.id, status: s.status, statement: s.statement, limits: J(s.limits), data: J(s.data), sourcePath: s.sourcePath })) }),
    prisma.b6Measurement.createMany({
      data: x.b6.map((b: any) => ({
        id: b.id, verdict: b.verdict, relativePpm: b.relativePpm, ci95: b.ci95, halfwidthPpm: b.halfwidthPpm, armA: J(b.armA), armB: J(b.armB),
        stability: J(b.stability), criteria: J(b.criteria), pairing: J(b.pairing), scopeLimits: J(b.scopeLimits), rawCsvPresent: b.rawCsvPresent,
        sourcePath: b.sourcePath, sourceSha256: b.sourceSha256,
      })),
    }),
  ]);
  // row-count checks against the source files (counts recorded by the extractor from the archives / JSON files)
  const got = {
    campaign: await prisma.campaignEvidence.count(),
    campaignCsvRows: (await prisma.campaignEvidence.aggregate({ _sum: { csvRows: true } }))._sum.csvRows ?? 0,
    pilot: await prisma.pilotRun.count(),
    pilotSummary: await prisma.pilotSummary.count(),
    b6: await prisma.b6Measurement.count(),
  };
  const want: ExtraCounts = x.counts;
  for (const k of Object.keys(want) as (keyof ExtraCounts)[]) {
    if (got[k] !== want[k]) throw new Error(`row-count mismatch for ${k}: database ${got[k]} vs source ${want[k]}`);
  }
  if (got.campaign !== nCampaignRuns) throw new Error(`campaign evidence rows ${got.campaign} != CampaignRun rows ${nCampaignRuns}`);
  console.log(`extra datasets loaded: campaign evidence ${got.campaign} (${got.campaignCsvRows} frames), pilot ${got.pilot}, pilot summaries ${got.pilotSummary}, B6 ${got.b6}; row counts match the source files`);
  return got;
}

if (require.main === module) {
  const prisma = new PrismaClient();
  ingestExtra(prisma)
    .catch((e) => {
      console.error(e);
      process.exit(1);
    })
    .finally(() => prisma.$disconnect());
}
