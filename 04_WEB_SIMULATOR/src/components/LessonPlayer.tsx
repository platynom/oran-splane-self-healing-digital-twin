"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import clsx from "clsx";
import type { LookAlike } from "@prisma/client";
import type { Lesson } from "@/lib/lessons";
import { Widget } from "./lesson/Widgets";
import type { ScenarioOpt } from "./ReplayViewer";

export interface GameRun {
  id: string;
  scenarioId: string;
  expected: string;
  description: string | null;
  v3Verdict: string;
  v3Hint: string | null;
  v3Reason: string | null;
  nPackets: number | null;
}

export interface LessonData {
  scenarios?: ScenarioOpt[];
  lookAlikes?: LookAlike[];
  game?: GameRun[];
  a8?: { id: string; onBc: number; total: number }[];
}

/** No sign-in, no XP: progress lives only in this component's state (simulator brief: no gamification). */
export function LessonPlayer({ lesson, data, next, hrefTemplate = "/?panel=__PANEL__", embedded = false }: {
  lesson: Lesson;
  data: LessonData;
  next: { id: string; title: string } | null;
  /** URL with __PANEL__ where the panel id goes (a string, so a server component can pass it). */
  hrefTemplate?: string;
  embedded?: boolean;
}) {
  const hrefFor = (id: string | null) => hrefTemplate.replace("__PANEL__", id ? `lesson:${id}` : "lessons");
  const reduce = useReducedMotion();
  const total = lesson.steps.length + 1; // + quiz
  const [idx, setIdx] = useState(0);
  const [doneSteps, setDoneSteps] = useState<Set<string>>(new Set());

  const step = idx < lesson.steps.length ? lesson.steps[idx] : null;
  const [widgetDone, setWidgetDone] = useState(false);
  useEffect(() => setWidgetDone(false), [idx]);

  const onContinue = useCallback(() => {
    if (!step) return;
    setDoneSteps((s) => new Set(s).add(step.id));
    setIdx((i) => i + 1);
    if (!embedded && typeof window !== "undefined") window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  }, [step, reduce, embedded]);

  const canContinue = widgetDone || (step ? doneSteps.has(step.id) : false);

  return (
    <div className={embedded ? "" : "mx-auto max-w-5xl"}>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Link href={hrefFor(null)} className="text-sm text-muted underline">
          Lessons
        </Link>
        <span className="text-sm text-muted">/</span>
        <span className="text-sm font-semibold">Lesson {lesson.n}</span>
      </div>
      <h2 className="text-2xl font-semibold tracking-tight">{lesson.title}</h2>
      <div className="mt-4 flex items-center gap-3">
        <div className="h-3 flex-1 rounded-full bg-surface-2" role="progressbar" aria-label="Lesson progress" aria-valuemin={0} aria-valuemax={total} aria-valuenow={Math.min(idx, total)}>
          <motion.div className="h-3 rounded-full bg-accent" animate={{ width: `${(Math.min(idx, total) / total) * 100}%` }} transition={{ duration: reduce ? 0 : 0.4 }} />
        </div>
        <span className="num text-sm text-muted">
          {Math.min(idx + 1, total)}/{total}
        </span>
      </div>
      <ol className="mt-3 flex flex-wrap gap-2 text-xs" aria-label="Steps">
        {lesson.steps.map((s, i) => (
          <li key={s.id}>
            <button
              type="button"
              onClick={() => (doneSteps.has(s.id) || i <= idx ? setIdx(i) : undefined)}
              disabled={!(doneSteps.has(s.id) || i <= idx)}
              aria-current={i === idx ? "step" : undefined}
              className={clsx("rounded-full border px-3 py-1", i === idx ? "border-accent bg-accent-soft font-semibold" : doneSteps.has(s.id) ? "border-ok text-ok" : "border-line text-muted")}
            >
              {doneSteps.has(s.id) ? "✓ " : ""}
              {s.title}
            </button>
          </li>
        ))}
        <li>
          <span className={clsx("inline-block rounded-full border px-3 py-1", idx === lesson.steps.length ? "border-accent bg-accent-soft font-semibold" : "border-line text-muted")}>Check</span>
        </li>
      </ol>


      <div className="mt-6">
        {step ? (
          <section aria-labelledby="step-title" key={step.id}>
            <h2 id="step-title" className="text-xl font-semibold">
              {step.title}
            </h2>
            {step.body.map((p, i) => (
              <p key={i} className="mt-2 max-w-3xl">
                {p}
              </p>
            ))}
            <div className="mt-4 rounded-xl border border-line bg-surface p-4">
              <Widget widget={step.widget} data={data} onDone={() => setWidgetDone(true)} stepId={step.id} />
            </div>
            <p className="mt-2 text-xs text-muted">Source: {step.source}</p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={onContinue}
                disabled={!canContinue}
                className="rounded-md bg-accent px-5 py-2.5 font-semibold text-accent-ink disabled:cursor-not-allowed disabled:opacity-50"
                data-testid="step-continue"
              >
                Continue
              </button>
              {!canContinue && step.task && <span className="text-sm text-muted">To continue: {step.task}</span>}
            </div>
          </section>
        ) : (
          <Quiz
            lesson={lesson}
            allStepsDone={lesson.steps.every((s) => doneSteps.has(s.id))}
            next={next}
            hrefFor={hrefFor}
          />
        )}
      </div>
    </div>
  );
}

function Quiz({ lesson, allStepsDone, next, hrefFor }: {
  lesson: Lesson;
  allStepsDone: boolean;
  next: { id: string; title: string } | null;
  hrefFor: (lessonId: string | null) => string;
}) {
  const [qi, setQi] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);
  const q = lesson.quiz[qi];

  if (finished) {
    const perfect = score === lesson.quiz.length;
    return (
      <section aria-labelledby="quiz-done" className="rounded-xl border border-line bg-surface p-6" data-testid="quiz-result">
        <h2 id="quiz-done" className="text-xl font-semibold">
          {perfect ? "Lesson check passed" : "Lesson check finished"}
        </h2>
        <p className="num mt-2 text-lg" data-testid="quiz-score">
          {score}/{lesson.quiz.length} correct
        </p>
        {perfect && allStepsDone && (
          <p className="mt-2 font-semibold text-ok" data-testid="lesson-complete">
            Lesson {lesson.n} complete.
          </p>
        )}
        {!perfect && <p className="mt-2 text-muted">A lesson is complete when every step is done and the check is 3/3.</p>}
        <div className="mt-4 flex flex-wrap gap-3">
          {!perfect && (
            <button
              type="button"
              onClick={() => {
                setQi(0);
                setPicked(null);
                setScore(0);
                setFinished(false);
              }}
              className="rounded-md border border-line px-4 py-2 font-semibold hover:bg-surface-2"
            >
              Retry the check
            </button>
          )}
          {next && (
            <Link href={hrefFor(next.id)} className="rounded-md bg-accent px-4 py-2 font-semibold text-accent-ink">
              Next: {next.title}
            </Link>
          )}
          <Link href={hrefFor(null)} className="rounded-md border border-line px-4 py-2 font-semibold hover:bg-surface-2">
            Learning path
          </Link>
        </div>
      </section>
    );
  }

  const answered = picked !== null;
  const correct = picked === q.answer;
  return (
    <section aria-labelledby="quiz-title">
      <h2 id="quiz-title" className="text-xl font-semibold">
        Check {qi + 1} of {lesson.quiz.length}
      </h2>
      <p className="mt-2 max-w-3xl text-lg" id={`q-${q.id}`}>
        {q.prompt}
      </p>
      <div role="radiogroup" aria-labelledby={`q-${q.id}`} className="mt-4 flex flex-col gap-2">
        {q.options.map((o, i) => {
          const isPicked = picked === i;
          const isAnswer = i === q.answer;
          return (
            <button
              key={i}
              type="button"
              role="radio"
              aria-checked={isPicked}
              disabled={answered}
              onClick={() => {
                setPicked(i);
                if (i === q.answer) setScore((s) => s + 1);
              }}
              className={clsx(
                "rounded-lg border-2 px-4 py-3 text-left",
                !answered && "border-line bg-surface hover:border-accent",
                answered && isAnswer && "border-ok bg-ok-soft",
                answered && isPicked && !isAnswer && "border-danger bg-danger-soft",
                answered && !isPicked && !isAnswer && "border-line opacity-70",
              )}
              data-testid={`quiz-option-${i}`}
            >
              {o}
            </button>
          );
        })}
      </div>
      {answered && (
        <div role="status" className={clsx("mt-4 rounded-lg border p-4", correct ? "border-ok bg-ok-soft" : "border-danger bg-danger-soft")}>
          <p className={clsx("font-semibold", correct ? "text-ok" : "text-danger")}>{correct ? "Correct." : "Not quite."}</p>
          <p className="mt-1 text-ink">{q.explanation}</p>
          <p className="mt-1 text-xs text-muted">Citation: {q.citation}</p>
        </div>
      )}
      <button
        type="button"
        disabled={!answered}
        onClick={() => {
          if (qi + 1 < lesson.quiz.length) {
            setQi(qi + 1);
            setPicked(null);
          } else {
            setFinished(true);
          }
        }}
        className="mt-4 rounded-md bg-accent px-5 py-2.5 font-semibold text-accent-ink disabled:opacity-50"
        data-testid="quiz-next"
      >
        {qi + 1 < lesson.quiz.length ? "Next question" : "Finish"}
      </button>
    </section>
  );
}
