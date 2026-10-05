"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { UserMenu } from "./UserMenu";

const NAV = [
  { href: "/learn", label: "Learn" },
  { href: "/replay", label: "Replay" },
  { href: "/sandbox", label: "Sandbox" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/catalogue", label: "Fault catalogue" },
  { href: "/live", label: "Live" },
  { href: "/about", label: "About & limits" },
];

export function SiteHeader() {
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
        <nav aria-label="Main" className="ml-auto hidden xl:block">
          <ul className="flex items-center gap-1">
            {NAV.map((n) => {
              const active = path === n.href || path.startsWith(n.href + "/");
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
        <div className="ml-auto xl:ml-2">
          <UserMenu />
        </div>
        <button
          type="button"
          className="rounded-md border border-line px-3 py-2 text-sm xl:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((o) => !o)}
        >
          Menu
        </button>
      </div>
      {open && (
        <nav id="mobile-nav" aria-label="Main" className="border-t border-line xl:hidden">
          <ul className="mx-auto grid max-w-7xl grid-cols-2 gap-1 px-4 py-3 sm:grid-cols-4">
            {NAV.map((n) => (
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
