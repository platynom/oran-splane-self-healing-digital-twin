import "server-only";
import type { LessonData } from "@/components/LessonPlayer";
import { prisma } from "@/lib/db";
import { getScenarios } from "@/lib/data";
import type { Lesson } from "@/lib/lessons";

/** Real campaign runs used in the "You are the rule" step (lesson 4). */
const GAME_RUNS = [
  "A1_rogue_master__r1",
  "B2_gm_failover__r1",
  "B_unplanned_failover__r1",
  "B_bc_replacement__r1",
  "C3_wholesecond__r1",
  "B3_pdv_congestion__r4",
];

/** Database rows a lesson's widgets need (shared by the simulator side panel and the legacy /learn route). */
export async function loadLessonData(lesson: Lesson): Promise<LessonData> {
  const needs = new Set(lesson.steps.map((s) => s.widget.type));
  const data: LessonData = {};
  if (needs.has("replay")) {
    data.scenarios = (await getScenarios()).map(({ id, code, title, cls }) => ({ id, code, title, cls }));
  }
  if (needs.has("lookalikes")) {
    data.lookAlikes = await prisma.lookAlike.findMany({ orderBy: { id: "asc" } });
  }
  if (needs.has("verdict-game")) {
    const rows = await prisma.campaignRun.findMany({ where: { id: { in: GAME_RUNS } } });
    data.game = GAME_RUNS.map((id) => rows.find((r) => r.id === id)!).filter(Boolean).map((r) => ({
      id: r.id, scenarioId: r.scenarioId, expected: r.expected, description: r.description, v3Verdict: r.v3Verdict, v3Hint: r.v3Hint, v3Reason: r.v3Reason, nPackets: r.nPackets,
    }));
  }
  if (needs.has("steps-removed")) {
    const runs = await prisma.run.findMany({ where: { scenarioId: "A8_rogue_bc", arm: "control" }, select: { id: true } });
    data.a8 = await Promise.all(
      runs.map(async ({ id }) => {
        const where = { runId: id, node: { in: ["ru1", "ru2"] }, t: { gte: 0, lte: 40 } };
        const [onBc, total] = await Promise.all([prisma.sample.count({ where: { ...where, parent: "020000fffe000001" } }), prisma.sample.count({ where })]);
        return { id, onBc, total };
      }),
    );
  }
  return data;
}
