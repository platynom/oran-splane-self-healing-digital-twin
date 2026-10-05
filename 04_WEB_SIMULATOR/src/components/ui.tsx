import clsx from "clsx";

export function Card({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx("rounded-xl border border-line bg-surface p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]", className)} {...rest}>
      {children}
    </div>
  );
}

type Tone = "neutral" | "accent" | "ok" | "warn" | "danger";
const TONE: Record<Tone, string> = {
  neutral: "bg-surface-2 text-ink border-line",
  accent: "bg-accent-soft text-ink border-accent/40",
  ok: "bg-ok-soft text-ok border-ok/40",
  warn: "bg-warn-soft text-warn border-warn/40",
  danger: "bg-danger-soft text-danger border-danger/40",
};

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: React.ReactNode; className?: string }) {
  return <span className={clsx("inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold", TONE[tone], className)}>{children}</span>;
}

/** Marks modelled or illustrative (not measured) content. */
export function ModelLabel({ children = "MODEL — not measured data" }: { children?: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded border-2 border-dashed border-warn px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-warn">
      {children}
    </span>
  );
}

export function MeasuredLabel({ children = "Measured — recorded run data" }: { children?: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded border border-ok px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-ok">{children}</span>
  );
}

export function PageTitle({ title, lead, children }: { title: string; lead?: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-2">
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
      {lead && <p className="max-w-3xl text-muted">{lead}</p>}
      {children}
    </div>
  );
}

export function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="num mt-1 text-2xl font-semibold">{value}</div>
      {sub && <div className="mt-1 text-sm text-muted">{sub}</div>}
    </div>
  );
}

/** Per-element provenance badge for animated or explanatory content (simulator brief: MEASURED vs ILLUSTRATIVE on every animated element). */
export function KindBadge({ kind, title }: { kind: "MEASURED" | "CONFIGURED" | "ILLUSTRATIVE" | "UNKNOWN" | "REFERENCE"; title?: string }) {
  const cls = {
    MEASURED: "border-ok text-ok",
    CONFIGURED: "border-accent text-ink",
    ILLUSTRATIVE: "border-dashed border-warn text-warn",
    UNKNOWN: "border-line text-muted",
    REFERENCE: "border-line text-muted",
  }[kind];
  return (
    <span title={title} data-kind-badge={kind} className={clsx("inline-flex items-center rounded border px-1.5 py-0 text-[10px] font-bold uppercase tracking-wide", cls)}>
      {kind}
    </span>
  );
}
