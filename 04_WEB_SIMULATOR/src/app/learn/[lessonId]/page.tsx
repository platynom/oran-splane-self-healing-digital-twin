import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LessonPlayer } from "@/components/LessonPlayer";
import { loadLessonData } from "@/lib/lessonData";
import { LESSONS, lessonById } from "@/lib/lessons";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ lessonId: string }> }): Promise<Metadata> {
  const l = lessonById((await params).lessonId);
  return { title: l ? `Lesson ${l.n}: ${l.title}` : "Lesson" };
}

export default async function LessonPage({ params }: { params: Promise<{ lessonId: string }> }) {
  const { lessonId } = await params;
  const lesson = lessonById(lessonId);
  if (!lesson) notFound();
  const data = await loadLessonData(lesson);
  const idx = LESSONS.findIndex((l) => l.id === lesson.id);
  const next = LESSONS[idx + 1];
  return <LessonPlayer lesson={lesson} data={data} next={next ? { id: next.id, title: next.title } : null} />;
}
