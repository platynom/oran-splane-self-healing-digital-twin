import type { Metadata } from "next";
import { Card, PageTitle } from "@/components/ui";
import { LimitsPanel } from "@/components/LimitsPanel";
import { getProvenance } from "@/lib/data";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "About & limits" };

interface Prov {
  sources: { path: string; sha256: string; verified_against: string | null }[];
  notes: { topic: string; detail: string }[];
  counts: Record<string, number>;
}

export default async function About() {
  const info = await getProvenance();
  const prov = (info?.provenance ?? { sources: [], notes: [], counts: {} }) as unknown as Prov;
  return (
    <>
      <PageTitle
        title="About this app, its data and its limits"
        lead="What is measured, what is modelled, and what the testbed cannot show."
      />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h2 className="font-semibold">Replay: measured</h2>
          <p className="mt-2 text-sm">
            Animates the recorded runs exactly as stored: observer samples, loop events, ptp4l log lines and per-0.5 s frame counts from
            the captures. Works everywhere, including Vercel.
          </p>
        </Card>
        <Card>
          <h2 className="font-semibold">Sandbox: model</h2>
          <p className="mt-2 text-sm">
            A deterministic model of the loop&apos;s decision flow, fed by recorded verdict sequences and Announce gaps. It is not measured
            data, is labelled as such on screen, and always names the closest recorded run.
          </p>
        </Card>
        <Card>
          <h2 className="font-semibold">Live: localhost only</h2>
          <p className="mt-2 text-sm">
            Optional. A local FastAPI service runs the project&apos;s own run_one.py (real linuxptp in network namespaces) and streams its
            logs. It refuses to run unless the host is Linux, the service runs as root and <code>freeze.py --verify</code> passes. It is
            disabled on Vercel.
          </p>
        </Card>
      </div>

      <section className="mt-10" aria-labelledby="lim">
        <h2 id="lim" className="text-xl font-semibold">Testbed limits</h2>
        <LimitsPanel />
      </section>

      <section className="mt-10" aria-labelledby="prov">
        <h2 id="prov" className="text-xl font-semibold">Data provenance</h2>
        <p className="mt-1 text-sm text-muted">
          ingest/extract.py reads the archives below (sha256-checked against the published hashes before opening), recomputes every
          per-run value and checks it against EVALUATION_RL.json and EVALUATION_V4.json. scripts/ingest.ts loads the result into
          PostgreSQL and recomputes the metrics again from the stored rows. Both checks passed with zero discrepancies.
        </p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
                <th className="py-2">File</th>
                <th>sha256</th>
                <th>Checked against</th>
              </tr>
            </thead>
            <tbody>
              {prov.sources.map((s) => (
                <tr key={s.path} className="border-b border-line align-top">
                  <td className="py-1.5 pr-3 font-mono text-xs break-all">{s.path}</td>
                  <td className="pr-3 font-mono text-xs break-all">{s.sha256.slice(0, 16)}…</td>
                  <td className="text-xs">{s.verified_against ?? "recorded only"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-sm">
          Counts: {Object.entries(prov.counts).map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join(" · ")}
          {info && <> · ingested {info.ingestedAt.toISOString().slice(0, 16).replace("T", " ")} UTC</>}
        </p>
        <h3 className="mt-6 font-semibold">Notes found while ingesting</h3>
        <ul className="mt-2 list-disc space-y-2 pl-5 text-sm">
          {prov.notes.map((n) => (
            <li key={n.topic}>
              <span className="font-semibold">{n.topic}:</span> {n.detail}
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
