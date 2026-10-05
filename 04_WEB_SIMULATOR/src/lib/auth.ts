import type { NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";
import EmailProvider from "next-auth/providers/email";
import { PrismaAdapter } from "@next-auth/prisma-adapter";
import { prisma } from "./db";

/** Providers are enabled only when their environment variables are present (see README / .env.example). */
export function enabledProviders() {
  return {
    github: !!(process.env.GITHUB_ID && process.env.GITHUB_SECRET),
    email: !!(process.env.EMAIL_SERVER && process.env.EMAIL_FROM),
  };
}

const p = enabledProviders();

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  session: { strategy: "database" },
  secret: process.env.NEXTAUTH_SECRET,
  pages: { signIn: "/signin", verifyRequest: "/signin?check=email" },
  providers: [
    ...(p.github ? [GitHubProvider({ clientId: process.env.GITHUB_ID!, clientSecret: process.env.GITHUB_SECRET! })] : []),
    ...(p.email ? [EmailProvider({ server: process.env.EMAIL_SERVER, from: process.env.EMAIL_FROM })] : []),
  ],
  callbacks: {
    session({ session, user }) {
      if (session.user) (session.user as { id?: string }).id = user.id;
      return session;
    },
  },
};
