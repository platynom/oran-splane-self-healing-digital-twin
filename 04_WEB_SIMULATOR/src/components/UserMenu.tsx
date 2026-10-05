"use client";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { useProgress } from "@/lib/useProgress";

export function UserMenu() {
  const { data: session } = useSession();
  const { stats } = useProgress();
  return (
    <div className="flex items-center gap-3 text-sm">
      {stats && (
        <span className="hidden items-center gap-2 2xl:flex" aria-label={`${stats.xp} XP, ${stats.streak} day streak`}>
          <span className="num rounded-full bg-accent-soft px-2.5 py-1 font-semibold">{stats.xp} XP</span>
          <span className="num rounded-full bg-warn-soft px-2.5 py-1 font-semibold text-warn">{stats.streak} day streak</span>
        </span>
      )}
      {session?.user ? (
        <button type="button" onClick={() => signOut()} className="whitespace-nowrap rounded-md border border-line px-3 py-2 hover:bg-surface-2">
          Sign out
        </button>
      ) : (
        <Link href="/signin" className="whitespace-nowrap rounded-md border border-line px-3 py-2 hover:bg-surface-2">
          {stats?.isGuest ? "Guest · sign in" : "Sign in"}
        </Link>
      )}
    </div>
  );
}
