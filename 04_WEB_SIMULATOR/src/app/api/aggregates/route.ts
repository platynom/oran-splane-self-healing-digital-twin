import { NextResponse } from "next/server";
import { getAggregates, getCampaignSummary, getHypotheses } from "@/lib/data";

export const dynamic = "force-dynamic";

/** Per-scenario aggregates, hypothesis verdicts and campaign summary, as computed from the database rows. */
export async function GET() {
  const [aggregates, hypotheses, campaign] = await Promise.all([getAggregates(), getHypotheses(), getCampaignSummary()]);
  return NextResponse.json({ aggregates, hypotheses, campaign });
}
