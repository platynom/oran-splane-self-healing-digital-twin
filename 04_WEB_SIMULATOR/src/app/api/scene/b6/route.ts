import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

/** Read-only: B6 two-laptop drift analysis outputs. Raw per-sample files are not in the repository; none are returned. */
export async function GET() {
  const rows = await prisma.b6Measurement.findMany({ orderBy: { id: "asc" } });
  return NextResponse.json({ measurements: rows, rawSamplesAvailable: false });
}
