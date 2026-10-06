import type { Metadata } from "next";
import { ResultsContent } from "@/components/ResultsContent";

// Reached only if the /dashboard redirect in next.config.ts is removed; the simulator shows this as its Results overlay.
export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Dashboard" };

export default function Dashboard() {
  return <ResultsContent />;
}
