import { prisma } from "@/lib/db";
import { readFileSync } from "node:fs";
import path from "node:path";
import { KindBadge } from "../ui";

/** ABSENT rows of docs/3D_DATA_INVENTORY.md (written by ingest/inventory.py): files the project references but the repository lacks. */
function absentFiles(): { item: string; note: string }[] | null {
  try {
    const md = readFileSync(path.join(process.cwd(), "docs", "3D_DATA_INVENTORY.md"), "utf8");
    return md
      .split("\n")
      .filter((l) => l.startsWith("|") && l.includes("ABSENT from repository"))
      .map((l) => {
        const cells = l.split("|").map((c) => c.trim());
        return { item: cells[1].replace(/`/g, ""), note: cells[5] + (cells[6] ? `; ${cells[6]}` : "") };
      });
  } catch {
    return null;
  }
}

/** Datasets loaded in the database, with row counts read at request time. Absent raw files are listed, never approximated. */
export async function DatasetsPanel() {
  const [runs, camp, evid, frames, pilot, s15, s11, b6] = await Promise.all([
    prisma.run.count(),
    prisma.campaignRun.count(),
    prisma.campaignEvidence.count(),
    prisma.campaignEvidence.aggregate({ _sum: { csvRows: true } }),
    prisma.pilotRun.groupBy({ by: ["milestone"], _count: true }),
    prisma.pilotSummary.findUnique({ where: { id: "S15" } }),
    prisma.pilotSummary.findUnique({ where: { id: "S11" } }),
    prisma.b6Measurement.findMany({ orderBy: { id: "asc" } }),
  ]);
  const absent = absentFiles();
  const n = (m: string) => pilot.find((p) => p.milestone === m)?._count ?? 0;
  return (
    <div data-testid="datasets-panel">
      <h2 className="text-xl font-semibold">Datasets</h2>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <thead>
            <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
              <th className="py-2">Dataset</th>
              <th>Rows in database</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-line" data-testid="ds-row-recovery">
              <td className="py-2"><KindBadge kind="MEASURED" /> Recovery-loop runs (14 scenarios × 2 arms × 5 replicates)</td>
              <td className="num" data-testid="ds-recovery-rows">{runs}</td>
              <td>pre-registered; replayable at level 3</td>
            </tr>
            <tr className="border-b border-line" data-testid="ds-row-campaign">
              <td className="py-2"><KindBadge kind="MEASURED" /> Detector campaign (14 scenarios × 12 replicates)</td>
              <td className="num"><span data-testid="ds-campaign-rows">{camp}</span> runs; <span data-testid="ds-campaign-evidence">{evid}</span> with evidence; <span data-testid="ds-campaign-frames">{(frames._sum.csvRows ?? 0).toLocaleString("en-US")}</span> PTP frames</td>
              <td>corrected archive 2026-09-20</td>
            </tr>
            <tr className="border-b border-line" data-testid="ds-row-pilot">
              <td className="py-2"><KindBadge kind="MEASURED" /> 13 Sep pilot, software testbed</td>
              <td className="num"><span data-testid="ds-pilot-s11">{n("S11")}</span> S11 trials; <span data-testid="ds-pilot-s15">{n("S15")}</span> S15 trials</td>
              <td>
                S11: {s11?.status.toLowerCase().replaceAll("_", " ")}. <strong data-testid="ds-pilot-s15-status">independent validation S15 {s15?.status === "NOT_ESTABLISHED" ? "not established" : s15?.status ?? "not loaded"}</strong>
              </td>
            </tr>
            {b6.map((b) => (
              <tr key={b.id} className="border-b border-line" data-testid={`ds-row-b6-${b.id}`}>
                <td className="py-2"><KindBadge kind="MEASURED" /> B6 two-laptop oscillator drift, {b.id}</td>
                <td className="num">
                  <span data-testid={`ds-b6-${b.id}-ppm`}>{b.relativePpm.toFixed(3)}</span> ppm (95% CI <span data-testid={`ds-b6-${b.id}-ci`}>{b.ci95.map((x) => x.toFixed(3)).join(" to ")}</span>)
                </td>
                <td>{b.verdict.toLowerCase().replace("_", " ")}; raw per-sample files: {b.rawCsvPresent ? "present" : "data not in repo"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 className="mt-4 font-semibold">Data not in repo</h3>
      {absent ? (
        <ul className="mt-1 list-disc pl-5 text-sm" data-testid="ds-absent">
          {absent.map((a) => (
            <li key={a.item}>
              <code className="break-all">{a.item}</code>: {a.note}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted">Inventory file not found in this deployment.</p>
      )}
    </div>
  );
}
