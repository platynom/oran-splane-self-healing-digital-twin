"use client";
import Link from "next/link";
import clsx from "clsx";
import { useProgress } from "@/lib/useProgress";

interface L {
  id: string;
  n: number;
  title: string;
  summary: string;
  minutes: number;
  nSteps: number;
  nQuiz: number;
}

export function LearningPath({ lessons }: { lessons: L[] }) {
  const { progress, stats, loaded } = useProgress();
  const done = (id: string) => progress.find((p) => p.lessonId === id)?.completed ?? false;
  const nextId = lessons.find((l) => !done(l.id))?.id;
  const completed = lessons.filter((l) => done(l.id)).length;
  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_280px]">
      <ol className="relative flex flex-col gap-4" aria-label="Lessons">
        {lessons.map((l, i) => {
          const p = progress.find((x) => x.lessonId === l.id);
          const isDone = !!p?.completed;
          const isNext = l.id === nextId;
          const stepsDone = p?.stepsCompleted.length ?? 0;
          return (
            <li key={l.id} className={clsx("flex gap-4", i % 2 === 1 && "sm:pl-16")}>
              <div
                aria-hidden="true"
                className={clsx(
                  "num flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-4 text-lg font-bold",
                  isDone ? "border-ok bg-ok text-surface" : isNext ? "border-accent bg-accent-soft text-ink" : "border-line bg-surface text-muted",
                )}
              >
                {isDone ? "✓" : l.n}
              </div>
              <Link
                href={`/learn/${l.id}`}
                className={clsx("flex-1 rounded-xl border bg-surface p-4 hover:border-accent", isNext ? "border-accent" : "border-line")}
                data-testid={`lesson-card-${l.id}`}
              >
                <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                  Lesson {l.n} · {l.minutes} min · {l.nSteps} steps + {l.nQuiz} questions
                </span>
                <span className="mt-1 block text-lg font-semibold">{l.title}</span>
                <span className="mt-1 block text-sm text-muted">{l.summary}</span>
                <span className="mt-2 block text-sm font-semibold">
                  {isDone ? <span className="text-ok">Completed · quiz {p!.quizBest}/{l.nQuiz}</span> : stepsDone > 0 ? `${stepsDone}/${l.nSteps} steps done` : isNext ? "Start here" : ""}
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
      <aside className="h-fit rounded-xl border border-line bg-surface p-5" aria-label="Your progress">
        <h2 className="font-semibold">Your progress</h2>
        {!loaded ? (
          <p className="mt-2 text-sm text-muted">Loading…</p>
        ) : (
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted">Lessons</dt>
              <dd className="num text-xl font-semibold" data-testid="path-completed">{completed}/{lessons.length}</dd>
            </div>
            <div>
              <dt className="text-muted">XP</dt>
              <dd className="num text-xl font-semibold">{stats?.xp ?? 0}</dd>
            </div>
            <div>
              <dt className="text-muted">Streak</dt>
              <dd className="num text-xl font-semibold">{stats?.streak ?? 0} d</dd>
            </div>
            <div>
              <dt className="text-muted">Account</dt>
              <dd className="font-semibold">{stats ? (stats.isGuest ? "Guest" : stats.name ?? "Signed in") : "Not started"}</dd>
            </div>
          </dl>
        )}
        <div className="mt-4 h-2 rounded bg-surface-2" role="progressbar" aria-valuemin={0} aria-valuemax={lessons.length} aria-valuenow={completed} aria-label="Lessons completed">
          <div className="h-2 rounded bg-ok" style={{ width: `${(completed / lessons.length) * 100}%` }} />
        </div>
        <p className="mt-3 text-xs text-muted">+10 XP per step, +5 per correct answer (best attempt), +20 when a lesson is complete. A streak counts consecutive UTC days with activity.</p>
      </aside>
    </div>
  );
}
