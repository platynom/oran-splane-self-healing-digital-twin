/** XP and streak rules (pure; applied server-side in /api/progress so the client cannot award itself XP). */
export const XP = { step: 10, quizCorrect: 5, lessonComplete: 20 } as const;

export function dayKey(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function nextStreak(lastActiveDay: string | null, streak: number, now: Date): number {
  const today = dayKey(now);
  if (lastActiveDay === today) return Math.max(1, streak);
  const y = new Date(now);
  y.setUTCDate(y.getUTCDate() - 1);
  return lastActiveDay === dayKey(y) ? streak + 1 : 1;
}

export interface ProgressDelta {
  newSteps: number;
  quizImprovement: number;
  lessonCompletedNow: boolean;
}

export function xpFor(d: ProgressDelta): number {
  return d.newSteps * XP.step + Math.max(0, d.quizImprovement) * XP.quizCorrect + (d.lessonCompletedNow ? XP.lessonComplete : 0);
}
