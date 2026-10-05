import { NextResponse } from "next/server";
import { buildSandboxData } from "@/lib/sandboxData";

export const dynamic = "force-dynamic";

let memo: { at: number; data: Awaited<ReturnType<typeof buildSandboxData>> } | null = null;

export async function GET() {
  if (!memo || Date.now() - memo.at > 10 * 60 * 1000) memo = { at: Date.now(), data: await buildSandboxData() };
  return NextResponse.json(memo.data, { headers: { "Cache-Control": "public, max-age=600, s-maxage=3600" } });
}
