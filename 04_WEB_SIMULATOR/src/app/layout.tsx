import type { Metadata, Viewport } from "next";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";
import { SessionProviders } from "@/components/SessionProviders";

export const metadata: Metadata = {
  title: { default: "S-Plane Recovery Simulator", template: "%s · S-Plane Recovery Simulator" },
  description:
    "O-RAN Open Fronthaul S-plane timing security and recovery loop: replays of 140 recorded testbed runs, a labelled decision model and short lessons.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <SessionProviders>
          <SiteHeader />
          <main id="main" className="mx-auto w-full max-w-7xl px-4 pb-16 pt-6 sm:px-6">
            {children}
          </main>
          <footer className="border-t border-line bg-surface">
            <div className="mx-auto max-w-7xl px-4 py-6 text-sm text-muted sm:px-6">
              <p>
                Samsung PRISM worklet · O-RAN Open Fronthaul S-plane timing security. Every measured value on this site comes
                from the project&apos;s recorded run archives (140 recovery-loop runs, 168-run detection campaign); modelled
                content is labelled <strong className="text-ink">MODEL</strong>.
              </p>
              <p className="mt-2">
                Testbed limits: software timestamping, <code>free_running 1</code> (clocks never steered), network namespaces
                on one host, nftables bridge filter as a stand-in for a switch ACL, no digital twin.{" "}
                <a className="underline" href="/about">
                  Details and data provenance
                </a>
                .
              </p>
            </div>
          </footer>
        </SessionProviders>
      </body>
    </html>
  );
}
