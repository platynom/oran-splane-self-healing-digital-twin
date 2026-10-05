import type { Metadata } from "next";
import { Sandbox } from "@/components/Sandbox";
import { PageTitle } from "@/components/ui";
import { getScenarios } from "@/lib/data";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "What-if sandbox (model)" };

export default async function SandboxPage() {
  const scenarios = (await getScenarios()).map(({ id, code, title, cls }) => ({ id, code, title, cls }));
  return (
    <>
      <PageTitle
        title="What-if sandbox"
        lead="Change the loop's evidence window, persistence and service-loss threshold and see how the decision flow would change. Everything here is a MODEL built on recorded inputs; the measured runs are shown beside it."
      />
      <Sandbox scenarios={scenarios} />
    </>
  );
}
