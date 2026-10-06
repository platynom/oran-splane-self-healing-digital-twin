import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

/** Read-only: 13 Sep pilot summaries (S11, S15) and per-run labels. */
export async function GET() {
  const [summaries, runs] = await Promise.all([
    prisma.pilotSummary.findMany({ orderBy: { id: "asc" } }),
    prisma.pilotRun.findMany({ select: { id: true, milestone: true, grp: true, label: true, triggered: true, actionExecuted: true, outcome: true }, orderBy: { id: "asc" } }),
  ]);
  return NextResponse.json({ summaries, runs });
}
