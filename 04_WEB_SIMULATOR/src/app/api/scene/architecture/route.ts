import { NextResponse } from "next/server";
import { architecture, contentStats, hiddenSentenceCount, renderableSentences } from "@/lib/architecture";

export const dynamic = "force-static";

/** Read-only: architecture content with SOURCE_NEEDED (and any citation-less) sentences removed server-side. */
export function GET() {
  const elements = architecture.elements.map((e) => ({ ...e, sentences: renderableSentences(e), hiddenSentences: hiddenSentenceCount(e) }));
  return NextResponse.json({ ...architecture, elements, stats: contentStats() });
}
