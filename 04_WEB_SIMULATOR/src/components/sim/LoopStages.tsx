"use client";
import { useMemo } from "react";
import clsx from "clsx";
import type { ReplayRun } from "@/lib/replay";
import { keyEvents, stagesAt, stagesInRun, STAGES, type Stage } from "@/lib/sim/events";
import { KindBadge } from "../ui";

const NAME: Record<Stage, string> = { detect: "Detect", localise: "Localise", decide: "Decide", act: "Act", verify: "Verify", rollback: "Rollback" };

/** Level 4: the recovery loop's stages, lit step by step from the run's recorded loop.jsonl events. */
export function LoopStages({ run, t, onFocus }: { run?: ReplayRun; t: number; onFocus: (id: string) => void }) {
  const evs = useMemo(() => (run ? keyEvents(run) : []), [run]);
  const now = stagesAt(evs, t);
  const inRun = stagesInRun(evs);
  return (
    <section className="rounded-xl border border-line bg-surface p-3 sm:p-4" aria-label="Recovery loop stages" data-testid="loop-stages">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold">Recovery loop{run ? `: ${run.arm === "loop" ? "loop arm" : "control arm (observe-only)"}` : ""}</h2>
        <KindBadge kind="MEASURED" title="Stage times are the recorded loop.jsonl timestamps of this run" />
      </div>
      <ol className="mt-3 grid gap-2 sm:grid-cols-3 xl:grid-cols-6">
        {STAGES.map((s) => {
          const hit = now[s];
          const never = run && !inRun.has(s);
          return (
            <li key={s}>
              <button
                type="button"
                onClick={() => onFocus(`loop-${s}`)}
                className={clsx(
                  "flex h-full w-full flex-col items-start rounded-lg border-2 p-2 text-left transition-colors",
                  hit ? "border-accent bg-accent-soft" : never ? "border-dashed border-line" : "border-line",
                )}
                data-testid={`stage-${s}`}
                data-lit={hit ? "true" : "false"}
                data-never={never ? "true" : "false"}
                aria-label={`${NAME[s]}: ${hit ? `reached at T0 + ${hit.t.toFixed(3)} s` : never ? "not reached in this run" : "not yet reached"}`}
              >
                <span className="font-semibold">{NAME[s]}</span>
                <span className="num text-xs text-muted">{hit ? `T0 + ${hit.t.toFixed(3)} s` : never ? "not in this run" : "—"}</span>
                {hit && <span className="mt-1 text-xs">{hit.label}</span>}
              </button>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
