import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/db";
import { currentUser } from "@/lib/identity";
import { LESSONS } from "@/lib/lessons";
import { dayKey, nextStreak, xpFor } from "@/lib/xp";

export const dynamic = "force-dynamic";

async function snapshot(userId: string | null) {
  if (!userId) return { stats: null, progress: [] };
  const u = await prisma.user.findUnique({ where: { id: userId }, include: { progress: true } });
  if (!u) return { stats: null, progress: [] };
  return {
    stats: { xp: u.xp, streak: u.streak, isGuest: u.isGuest, name: u.name ?? u.email ?? null },
    progress: u.progress.map((p) => ({ lessonId: p.lessonId, stepsCompleted: p.stepsCompleted, quizBest: p.quizBest, completed: !!p.completedAt })),
  };
}

export async function GET() {
  const u = await currentUser(false);
  return NextResponse.json(await snapshot(u?.id ?? null));
}

const Body = z.object({
  lessonId: z.string(),
  stepId: z.string().optional(),
  quizScore: z.number().int().min(0).max(10).optional(),
});

export async function POST(req: Request) {
  const parsed = Body.safeParse(await req.json().catch(() => null));
  if (!parsed.success) return NextResponse.json({ error: "bad request" }, { status: 400 });
  const { lessonId, stepId, quizScore } = parsed.data;
  const lesson = LESSONS.find((l) => l.id === lessonId);
  if (!lesson) return NextResponse.json({ error: "unknown lesson" }, { status: 404 });
  if (stepId && !lesson.steps.some((s) => s.id === stepId)) return NextResponse.json({ error: "unknown step" }, { status: 404 });
  if (quizScore !== undefined && quizScore > lesson.quiz.length) return NextResponse.json({ error: "bad score" }, { status: 400 });

  const user = await currentUser(true);
  if (!user) return NextResponse.json({ error: "no user" }, { status: 500 });
  const prev = await prisma.lessonProgress.findUnique({ where: { userId_lessonId: { userId: user.id, lessonId } } });
  const steps = new Set(prev?.stepsCompleted ?? []);
  const newSteps = stepId && !steps.has(stepId) ? 1 : 0;
  if (stepId) steps.add(stepId);
  const quizBest = Math.max(prev?.quizBest ?? 0, quizScore ?? 0);
  const allSteps = lesson.steps.every((s) => steps.has(s.id));
  const done = allSteps && quizBest === lesson.quiz.length;
  const lessonCompletedNow = done && !prev?.completedAt;
  const gained = xpFor({ newSteps, quizImprovement: quizBest - (prev?.quizBest ?? 0), lessonCompletedNow });
  const now = new Date();
  await prisma.$transaction([
    prisma.lessonProgress.upsert({
      where: { userId_lessonId: { userId: user.id, lessonId } },
      create: { userId: user.id, lessonId, stepsCompleted: [...steps], quizBest, quizTotal: lesson.quiz.length, completedAt: done ? now : null },
      update: { stepsCompleted: [...steps], quizBest, completedAt: prev?.completedAt ?? (done ? now : null) },
    }),
    prisma.user.update({
      where: { id: user.id },
      data: { xp: { increment: gained }, streak: nextStreak(user.lastActiveDay, user.streak, now), lastActiveDay: dayKey(now) },
    }),
  ]);
  return NextResponse.json({ gained, lessonCompletedNow, ...(await snapshot(user.id)) });
}
