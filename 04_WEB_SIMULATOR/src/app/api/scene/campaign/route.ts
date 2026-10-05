import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

/** Read-only: per-scenario campaign evidence summary; ?scenario=A1_rogue_master&rep=7 returns one run's evidence. */
export async function GET(req: Request) {
  const u = new URL(req.url);
  const scenario = u.searchParams.get("scenario");
  const rep = Number(u.searchParams.get("rep"));
  if (scenario && Number.isInteger(rep) && rep > 0) {
    const r = await prisma.campaignRun.findUnique({ where: { id: `${scenario}__r${rep}` }, include: { evidence: true } });
    return r ? NextResponse.json(r) : NextResponse.json({ error: "not found" }, { status: 404 });
  }
  const rows = await prisma.campaignRun.findMany({ include: { evidence: { select: { csvRows: true, msgTypeCounts: true } } }, orderBy: [{ scenarioId: "asc" }, { rep: "asc" }] });
  const by = new Map<string, { scenario: string; expected: string; runs: number; v3Correct: number; frames: number }>();
  for (const r of rows) {
    const s = by.get(r.scenarioId) ?? { scenario: r.scenarioId, expected: r.expected, runs: 0, v3Correct: 0, frames: 0 };
    s.runs++;
    if (r.v3Verdict === r.expected) s.v3Correct++;
    s.frames += r.evidence?.csvRows ?? 0;
    by.set(r.scenarioId, s);
  }
  return NextResponse.json({ runs: rows.length, scenarios: [...by.values()] });
}
