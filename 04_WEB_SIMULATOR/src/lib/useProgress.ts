"use client";
import { useCallback, useEffect, useSyncExternalStore } from "react";

export interface Stats {
  xp: number;
  streak: number;
  isGuest: boolean;
  name: string | null;
}
export interface LessonProg {
  lessonId: string;
  stepsCompleted: string[];
  quizBest: number;
  completed: boolean;
}
interface Snap {
  stats: Stats | null;
  progress: LessonProg[];
  loaded: boolean;
  lastGain: number;
}

let snap: Snap = { stats: null, progress: [], loaded: false, lastGain: 0 };
const subs = new Set<() => void>();
const emit = () => subs.forEach((f) => f());
let inflight: Promise<void> | null = null;

async function load() {
  if (inflight) return inflight;
  inflight = fetch("/api/progress", { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : { stats: null, progress: [] }))
    .then((d) => {
      snap = { ...snap, stats: d.stats, progress: d.progress, loaded: true };
      emit();
    })
    .catch(() => {
      snap = { ...snap, loaded: true };
      emit();
    })
    .finally(() => {
      inflight = null;
    });
  return inflight;
}

/** Learner progress shared across components; persisted in PostgreSQL via /api/progress (guest or signed in). */
export function useProgress() {
  const s = useSyncExternalStore(
    (f) => {
      subs.add(f);
      return () => subs.delete(f);
    },
    () => snap,
    () => snap,
  );
  useEffect(() => {
    if (!snap.loaded) void load();
  }, []);
  const record = useCallback(async (body: { lessonId: string; stepId?: string; quizScore?: number }) => {
    const r = await fetch("/api/progress", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) return null;
    const d = await r.json();
    snap = { stats: d.stats, progress: d.progress, loaded: true, lastGain: d.gained };
    emit();
    return d as { gained: number; lessonCompletedNow: boolean };
  }, []);
  return { ...s, record, reload: load };
}
