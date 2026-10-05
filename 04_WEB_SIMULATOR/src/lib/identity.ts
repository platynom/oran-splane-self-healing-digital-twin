import "server-only";
import { cookies } from "next/headers";
import { getServerSession } from "next-auth";
import { authOptions } from "./auth";
import { prisma } from "./db";

export const GUEST_COOKIE = "splane_gid";

/**
 * The learner behind this request: the signed-in user, else the guest user named by the guest cookie.
 * With create=true a guest user is created (and the cookie set) when neither exists.
 * When a guest signs in, the guest's progress is merged into the account once.
 */
export async function currentUser(create: boolean) {
  const session = await getServerSession(authOptions);
  const jar = await cookies();
  const gid = jar.get(GUEST_COOKIE)?.value;
  const sid = (session?.user as { id?: string } | undefined)?.id;
  if (sid) {
    if (gid) {
      await mergeGuest(gid, sid);
      jar.delete(GUEST_COOKIE);
    }
    return prisma.user.findUnique({ where: { id: sid } });
  }
  if (gid) {
    const g = await prisma.user.findFirst({ where: { id: gid, isGuest: true } });
    if (g) return g;
  }
  if (!create) return null;
  const g = await prisma.user.create({ data: { isGuest: true, name: "Guest" } });
  jar.set(GUEST_COOKIE, g.id, { httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production", maxAge: 60 * 60 * 24 * 365, path: "/" });
  return g;
}

async function mergeGuest(guestId: string, userId: string) {
  const guest = await prisma.user.findFirst({ where: { id: guestId, isGuest: true }, include: { progress: true } });
  if (!guest) return;
  const mine = await prisma.lessonProgress.findMany({ where: { userId } });
  for (const gp of guest.progress) {
    const m = mine.find((x) => x.lessonId === gp.lessonId);
    if (!m) {
      await prisma.lessonProgress.update({ where: { id: gp.id }, data: { userId } });
    } else {
      await prisma.lessonProgress.update({
        where: { id: m.id },
        data: {
          stepsCompleted: [...new Set([...m.stepsCompleted, ...gp.stepsCompleted])],
          quizBest: Math.max(m.quizBest, gp.quizBest),
          completedAt: m.completedAt ?? gp.completedAt,
        },
      });
    }
  }
  const u = await prisma.user.findUnique({ where: { id: userId } });
  await prisma.user.update({
    where: { id: userId },
    data: { xp: (u?.xp ?? 0) + guest.xp, streak: Math.max(u?.streak ?? 0, guest.streak), lastActiveDay: u?.lastActiveDay ?? guest.lastActiveDay },
  });
  await prisma.user.delete({ where: { id: guestId } });
}
