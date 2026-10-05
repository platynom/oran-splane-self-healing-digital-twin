import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

/** One recorded run, as stored by scripts/ingest.ts. Eval events are included (they drive the verdict strip). */
export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const run = await prisma.run.findUnique({
    where: { id },
    include: {
      samples: {
        orderBy: [{ round: "asc" }, { id: "asc" }],
        select: { round: true, t: true, node: true, portState: true, parent: true, parentPort: true, gm: true, stepsRemoved: true, healthy: true },
      },
      events: {
        orderBy: [{ t: "asc" }, { id: "asc" }],
        select: { t: true, source: true, kind: true, node: true, verdict: true, hint: true, action: true, target: true, ok: true, detail: true },
      },
      packets: true,
    },
  });
  if (!run) return NextResponse.json({ error: "run not found" }, { status: 404 });
  const { packets, t0Mono: _t0, ...rest } = run;
  void _t0;
  return NextResponse.json(
    { ...rest, packets: packets?.bins ?? [] },
    { headers: { "Cache-Control": "public, max-age=3600, s-maxage=86400" } },
  );
}
