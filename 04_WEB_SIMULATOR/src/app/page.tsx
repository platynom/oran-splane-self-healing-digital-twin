import Link from "next/link";
import { Simulator } from "@/components/sim/Simulator";
import { ResultsContent } from "@/components/ResultsContent";
import { LessonPlayer } from "@/components/LessonPlayer";
import { Sandbox } from "@/components/Sandbox";
import { CatalogueExplorer } from "@/components/CatalogueExplorer";
import { DatasetsPanel } from "@/components/sim/DatasetsPanel";
import { getScenarios } from "@/lib/data";
import { prisma } from "@/lib/db";
import { LESSONS, lessonById } from "@/lib/lessons";
import { loadLessonData } from "@/lib/lessonData";
import { DEFAULT_STATE, parseState, serializeState, type SimState } from "@/lib/sim/state";

export const dynamic = "force-dynamic";

type SP = Record<string, string | string[] | undefined>;

async function renderPanel(st: SimState, scenarios: { id: string; code: string; title: string; cls: string }[]) {
  const p = st.panel;
  if (!p) return null;
  const tpl = serializeState({ ...st, panel: "__PANEL__" });
  const href = (id: string | null) => tpl.replace("__PANEL__", id ? `lesson:${id}` : "lessons");
  if (p === "lessons") {
    return (
      <div>
        <h2 className="text-xl font-semibold">Lessons</h2>
        <ol className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="lesson-list">
          {LESSONS.map((l) => (
            <li key={l.id}>
              <Link href={href(l.id)} scroll={false} className="block h-full rounded-xl border border-line bg-surface-2 p-3 hover:border-accent">
                <span className="text-xs font-semibold text-accent">Lesson {l.n} · {l.minutes} min</span>
                <span className="mt-1 block font-semibold">{l.title}</span>
                <span className="mt-1 block text-sm text-muted">{l.summary}</span>
              </Link>
            </li>
          ))}
        </ol>
      </div>
    );
  }
  if (p.startsWith("lesson:")) {
    const lesson = lessonById(p.slice(7));
    if (!lesson) return <p>Unknown lesson.</p>;
    const data = await loadLessonData(lesson);
    const idx = LESSONS.findIndex((l) => l.id === lesson.id);
    const next = LESSONS[idx + 1];
    return <LessonPlayer key={lesson.id} lesson={lesson} data={data} next={next ? { id: next.id, title: next.title } : null} embedded hrefTemplate={tpl} />;
  }
  if (p === "sandbox") {
    return (
      <div>
        <h2 className="mb-3 text-xl font-semibold">What-if sandbox</h2>
        <Sandbox scenarios={scenarios} />
      </div>
    );
  }
  if (p === "catalogue") {
    const faults = await prisma.fault.findMany({ orderBy: { id: "asc" } });
    return (
      <div>
        <h2 className="mb-3 text-xl font-semibold">Fault catalogue</h2>
        <CatalogueExplorer faults={faults} />
      </div>
    );
  }
  if (p === "datasets") return <DatasetsPanel />;
  return null;
}

export default async function Home({ searchParams }: { searchParams: Promise<SP> }) {
  const st = parseState(await searchParams);
  const scenarios = (await getScenarios()).map(({ id, code, title, cls }) => ({ id, code, title, cls }));
  if (!scenarios.some((s) => s.id === st.scenario)) st.scenario = DEFAULT_STATE.scenario;
  const hwAll = await prisma.fault.findMany({ where: { testbedRequired: { startsWith: "HARDWARE" } }, select: { id: true, name: true }, orderBy: { id: "asc" } });
  // B6's physical premise was measured off the testbed on two laptops (outputs/B6_two_machine_2026-10-02). The workbook's
  // "HARDWARE required" describes detection on the testbed and is unchanged by that run (B6 record §7), so B6 is shown
  // as measured-elsewhere instead of "not measured", and only while its measurement rows are loaded.
  const b6 = await prisma.b6Measurement.findMany({ select: { id: true, verdict: true }, orderBy: { id: "asc" } });
  const b6Fault = b6.length ? hwAll.find((f) => f.id === "B6") : undefined;
  const hw = hwAll.filter((f) => f !== b6Fault);
  return (
    <Simulator
      scenarios={scenarios}
      initial={st}
      results={st.results ? <ResultsContent /> : null}
      panel={await renderPanel(st, scenarios)}
      hwFaults={hw}
      b6Measured={b6Fault ? { id: b6Fault.id, name: b6Fault.name, runs: b6 } : null}
    />
  );
}
