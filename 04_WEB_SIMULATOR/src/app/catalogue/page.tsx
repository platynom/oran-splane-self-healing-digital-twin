import type { Metadata } from "next";
import { CatalogueExplorer } from "@/components/CatalogueExplorer";
import { MeasuredLabel, PageTitle } from "@/components/ui";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Fault catalogue" };

export default async function CataloguePage() {
  const faults = await prisma.fault.findMany({ orderBy: { id: "asc" } });
  return (
    <>
      <PageTitle
        title="Fault catalogue"
        lead="The 16 catalogue faults (A1–A8, B1–B8) and the campaign-only scenarios (C1–C3, planned BC replacement, unplanned failover), with Source, Destination, Attack devices, Consequence and citations, as published in the 5 Oct 2026 workbooks. Bracketed tags are the workbooks' own source tags."
      >
        <div>
          <MeasuredLabel>Source: 2026-10-05 workbooks</MeasuredLabel>
        </div>
      </PageTitle>
      <CatalogueExplorer faults={faults} />
    </>
  );
}
