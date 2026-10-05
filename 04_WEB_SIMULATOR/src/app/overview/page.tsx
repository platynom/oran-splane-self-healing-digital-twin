import Link from "next/link";
import { Badge, Card } from "@/components/ui";
import { ControlLoopBars } from "@/components/ControlLoopBars";
import { getAggregates, getHypotheses, getScenarios } from "@/lib/data";
import { LESSONS } from "@/lib/lessons";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [aggs, hyps, scenarios] = await Promise.all([getAggregates(), getHypotheses(), getScenarios()]);
  const get = (s: string, a: string) => aggs.find((x) => x.scenarioId === s && x.arm === a);
  const head = ["A1_rogue_master", "C1_removal", "C3_wholesecond"].map((id) => ({
    sc: scenarios.find((s) => s.id === id)!,
    c: get(id, "control")!,
    l: get(id, "loop")!,
  }));
  return (
    <div className="flex flex-col gap-10">
      <section className="grid gap-6 lg:grid-cols-[1.3fr_1fr] lg:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-accent">O-RAN Open Fronthaul · S-plane</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Timing security and an automated recovery loop, on recorded evidence</h1>
          <p className="mt-4 max-w-2xl text-lg text-muted">
            Radio units must agree on time to within nanoseconds, and that time arrives as ordinary Ethernet frames. This app replays the
            project&apos;s 140 pre-registered recovery-loop runs on real linuxptp daemons, lets you explore the decision logic as a labelled
            model, and teaches the S-plane in seven short lessons.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/learn" className="rounded-md bg-accent px-5 py-3 font-semibold text-accent-ink">Start learning</Link>
            <Link href="/replay?scenario=A1_rogue_master&rep=13" className="rounded-md border border-line bg-surface px-5 py-3 font-semibold hover:bg-surface-2">
              Replay A1: control vs loop
            </Link>
            <Link href="/dashboard" className="rounded-md border border-line bg-surface px-5 py-3 font-semibold hover:bg-surface-2">Results dashboard</Link>
          </div>
        </div>
        <Card>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Pre-registered hypotheses</h2>
          <ul className="mt-3 space-y-2">
            {hyps.map((h) => (
              <li key={h.id} className="flex items-start gap-3">
                <Badge tone={h.pass ? "ok" : "danger"}>{h.id === "CI" ? "Control" : h.id} {h.pass ? "PASS" : "FAIL"}</Badge>
                <span className="text-sm">
                  <span className="font-semibold">{h.title}.</span> {h.summary}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted">Evaluated live from the database rows; criteria from PREREGISTRATION.md §5.</p>
        </Card>
      </section>

      <section aria-labelledby="headline">
        <h2 id="headline" className="text-xl font-semibold">Where the attacker captured the radio units</h2>
        <p className="mt-1 text-sm text-muted">Median seconds (of 40) that RU1 or RU2 was not following a legitimate parent, 5 replicates per arm.</p>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {head.map(({ sc, c, l }) => (
            <Card key={sc.id}>
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">
                  {sc.code} · {sc.title}
                </h3>
              </div>
              <div className="mt-3">
                <ControlLoopBars control={c.unhealthyMedian} loop={l.unhealthyMedian} label={sc.title} />
              </div>
              <p className="mt-3 text-xs text-muted">
                Loop restored {l.restoredAtEnd}/{l.n}; control restored {c.restoredAtEnd}/{c.n}.{" "}
                <Link className="underline" href={`/replay?scenario=${sc.id}&rep=13`}>
                  Replay
                </Link>
              </p>
            </Card>
          ))}
        </div>
      </section>

      <section aria-labelledby="path">
        <h2 id="path" className="text-xl font-semibold">Learning path</h2>
        <ol className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {LESSONS.map((l) => (
            <li key={l.id}>
              <Link href={`/learn/${l.id}`} className="block h-full rounded-xl border border-line bg-surface p-4 hover:border-accent">
                <span className="text-xs font-semibold text-accent">Lesson {l.n} · {l.minutes} min</span>
                <span className="mt-1 block font-semibold">{l.title}</span>
                <span className="mt-1 block text-sm text-muted">{l.summary}</span>
              </Link>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
