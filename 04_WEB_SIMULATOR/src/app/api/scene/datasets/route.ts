import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

/** Read-only: which datasets are loaded, with row counts and the status the project documents give them. */
export async function GET() {
  const [runs, camp, evid, pilot, b6, frames] = await Promise.all([
    prisma.run.count(),
    prisma.campaignRun.count(),
    prisma.campaignEvidence.count(),
    prisma.pilotRun.count(),
    prisma.b6Measurement.findMany({ select: { id: true, verdict: true, relativePpm: true, rawCsvPresent: true } }),
    prisma.campaignEvidence.aggregate({ _sum: { csvRows: true } }),
  ]);
  const s15 = await prisma.pilotSummary.findUnique({ where: { id: "S15" }, select: { status: true } });
  return NextResponse.json({
    datasets: [
      { id: "recovery-140", name: "Recovery-loop runs", rows: runs, kind: "MEASURED", status: "pre-registered; H3 failed", note: "14 scenarios x 2 arms x 5 replicates" },
      { id: "campaign-168", name: "Detector campaign", rows: camp, evidenceRows: evid, frames: frames._sum.csvRows ?? 0, kind: "MEASURED", status: "corrected archive 2026-09-20", note: "14 scenarios x 12 replicates" },
      { id: "pilot-13sep", name: "13 Sep pilot (S11 + S15)", rows: pilot, kind: "MEASURED", status: `independent validation S15 ${s15?.status === "NOT_ESTABLISHED" ? "not established" : (s15?.status ?? "n/a")}`, note: "software testbed" },
      { id: "b6", name: "B6 oscillator drift (two laptops)", rows: b6.length, kind: "MEASURED", status: b6.map((b) => `${b.id} ${b.verdict.toLowerCase().replace("_", " ")}`).join("; "), rawCsvPresent: b6.some((b) => b.rawCsvPresent), note: "derived analysis only; raw per-sample files not in repo" },
    ],
  });
}
