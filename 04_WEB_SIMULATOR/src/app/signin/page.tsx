import type { Metadata } from "next";
import Link from "next/link";
import { Card, PageTitle } from "@/components/ui";
import { SignInButtons } from "@/components/SignInButtons";
import { enabledProviders } from "@/lib/auth";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Sign in" };

export default async function SignIn({ searchParams }: { searchParams: Promise<{ check?: string; error?: string }> }) {
  const sp = await searchParams;
  const p = enabledProviders();
  return (
    <div className="mx-auto max-w-xl">
      <PageTitle title="Sign in" lead="Progress, XP and streak are stored in the database. Sign in to keep them across devices, or continue as a guest on this browser." />
      {sp.check === "email" && (
        <p role="status" className="mb-4 rounded-md border border-ok bg-ok-soft p-3 text-ok">
          Check your inbox for the sign-in link.
        </p>
      )}
      {sp.error && (
        <p role="alert" className="mb-4 rounded-md border border-danger bg-danger-soft p-3 text-danger">
          Sign-in failed ({sp.error}). You can continue as a guest.
        </p>
      )}
      <Card className="flex flex-col gap-4">
        <SignInButtons github={p.github} email={p.email} />
        {!p.github && !p.email && (
          <p className="text-sm text-muted">
            No sign-in provider is configured on this deployment (set GITHUB_ID/GITHUB_SECRET or EMAIL_SERVER/EMAIL_FROM). Guest mode
            works without one.
          </p>
        )}
        <div className="border-t border-line pt-4">
          <Link href="/learn" className="inline-block rounded-md border border-line px-4 py-2 font-semibold hover:bg-surface-2" data-testid="guest-continue">
            Continue as guest
          </Link>
          <p className="mt-2 text-xs text-muted">
            Guest progress is tied to a cookie on this browser. If you sign in later, it is merged into your account.
          </p>
        </div>
      </Card>
    </div>
  );
}
