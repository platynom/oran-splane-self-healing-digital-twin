"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

// No sign-in or progress UI (simulator brief); the auth routes remain in the code but are not linked.
const NAV = [
  { href: "/", label: "Simulator" },
  { href: "/live", label: "Live", localOnly: true },
  { href: "/about", label: "About & limits" },
];

/** showLive: the live page is only offered when the app is not deployed (it needs a localhost service). */
export function SiteHeader({ showLive = false }: { showLive?: boolean }) {
  const nav = NAV.filter((n) => !n.localOnly || showLive);
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight" aria-label="S-Plane Recovery Simulator, home">
          <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
            <rect x="1" y="1" width="26" height="26" rx="6" fill="var(--accent)" />
            <path d="M6 18 L11 10 L15 16 L18 12 L22 18" stroke="var(--accent-ink)" strokeWidth="2.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="hidden sm:inline">S-Plane Recovery Simulator</span>
          <span className="sm:hidden">S-Plane</span>
        </Link>
        <nav aria-label="Main" className="ml-auto hidden md:block">
          <ul className="flex items-center gap-1">
            {nav.map((n) => {
              const active = n.href === "/" ? path === "/" : path === n.href || path.startsWith(n.href + "/");
              return (
                <li key={n.href}>
                  <Link
                    href={n.href}
                    aria-current={active ? "page" : undefined}
                    className={`whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium ${active ? "bg-accent-soft text-ink" : "text-muted hover:bg-surface-2 hover:text-ink"}`}
                  >
                    {n.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <button
          type="button"
          className="ml-auto rounded-md border border-line px-3 py-2 text-sm md:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((o) => !o)}
        >
          Menu
        </button>
      </div>
      {open && (
        <nav id="mobile-nav" aria-label="Main" className="border-t border-line md:hidden">
          <ul className="mx-auto grid max-w-7xl grid-cols-2 gap-1 px-4 py-3 sm:grid-cols-4">
            {nav.map((n) => (
              <li key={n.href}>
                <Link href={n.href} onClick={() => setOpen(false)} className="block rounded-md px-3 py-2 text-sm font-medium hover:bg-surface-2">
                  {n.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}
