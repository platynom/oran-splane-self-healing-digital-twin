"use client";
import { signIn } from "next-auth/react";
import { useState } from "react";

export function SignInButtons({ github, email }: { github: boolean; email: boolean }) {
  const [addr, setAddr] = useState("");
  return (
    <div className="flex flex-col gap-4">
      {github && (
        <button type="button" onClick={() => signIn("github", { callbackUrl: "/learn" })} className="rounded-md bg-ink px-4 py-2 font-semibold text-bg">
          Continue with GitHub
        </button>
      )}
      {email && (
        <form
          className="flex flex-col gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void signIn("email", { email: addr, callbackUrl: "/learn" });
          }}
        >
          <label htmlFor="email" className="text-sm font-medium">
            Email magic link
          </label>
          <div className="flex gap-2">
            <input id="email" type="email" required value={addr} onChange={(e) => setAddr(e.target.value)} className="flex-1 rounded-md border border-line bg-surface px-3 py-2" autoComplete="email" />
            <button type="submit" className="rounded-md bg-accent px-4 py-2 font-semibold text-accent-ink">
              Send link
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
