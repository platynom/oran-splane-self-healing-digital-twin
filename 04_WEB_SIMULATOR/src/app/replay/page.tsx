import type { Metadata } from "next";
import { ReplayViewer } from "@/components/ReplayViewer";
import { PageTitle } from "@/components/ui";
import { getScenarios } from "@/lib/data";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Replay" };

export default async function ReplayPage({ searchParams }: { searchParams: Promise<{ scenario?: string; rep?: string }> }) {
  const sp = await searchParams;
  const scenarios = await getScenarios();
  const ids = scenarios.map((s) => s.id);
  const scenario = sp.scenario && ids.includes(sp.scenario) ? sp.scenario : "A1_rogue_master";
  const rep = [13, 14, 15, 16, 17].includes(Number(sp.rep)) ? Number(sp.rep) : 13;
  return (
    <>
      <PageTitle
        title="Replay recorded runs"
        lead={
          <>
            Every frame of this replay is a lookup into one recorded run: RU state from the passive pmc observer (every 0.5 s), loop
            decisions from <code>loop.jsonl</code>, port changes from the ptp4l logs, and packet counts from the run&apos;s captures. The
            control and loop arms ran the same scenario, replicate and randomised parameters.
          </>
        }
      />
      <ReplayViewer scenarios={scenarios.map(({ id, code, title, cls }) => ({ id, code, title, cls }))} initialScenario={scenario} initialRep={rep} syncUrl />
    </>
  );
}
