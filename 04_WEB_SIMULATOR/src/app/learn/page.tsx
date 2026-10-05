import type { Metadata } from "next";
import { PageTitle } from "@/components/ui";
import { LearningPath } from "@/components/LearningPath";
import { LESSONS } from "@/lib/lessons";

export const metadata: Metadata = { title: "Learn" };

export default function LearnPage() {
  return (
    <>
      <PageTitle
        title="Learning path"
        lead="Seven short lessons, each with 2–3 interactive steps and a 3-question check. Lessons 5 and 6 replay recorded runs. Progress, XP and streak are saved in the database for your account or guest session."
      />
      <LearningPath lessons={LESSONS.map(({ id, n, title, summary, minutes, steps, quiz }) => ({ id, n, title, summary, minutes, nSteps: steps.length, nQuiz: quiz.length }))} />
    </>
  );
}
