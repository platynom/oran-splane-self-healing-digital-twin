"use client";
import { getElement, hiddenSentenceCount, referenceUrl, renderableSentences } from "@/lib/architecture";
import { KindBadge } from "../ui";

/**
 * Explanatory text of one architecture element. Only sentences with a complete citation are rendered;
 * SOURCE_NEEDED sentences are hidden and counted. Every rendered sentence carries its kind and a
 * citation chip (source, clause, locator, link, status). A VERIFIED chip carries the auditor's quote as its tooltip.
 * Claims confirmed against an opened primary standard also show a PRIMARY ✓ marker and the primary quote in the tooltip.
 */
export function Sentences({ id, compact = false }: { id: string; compact?: boolean }) {
  const el = getElement(id);
  if (!el) return <p className="text-sm text-muted">No content for {id}.</p>;
  const ss = renderableSentences(el);
  const hidden = hiddenSentenceCount(el);
  return (
    <div data-testid={`sentences-${id}`}>
      <ul className={compact ? "space-y-1.5" : "space-y-2.5"}>
        {ss.map((s) => {
          const url = referenceUrl(s.citation);
          return (
            <li key={s.id} className="text-sm" data-sentence={s.id} data-status={s.citation.status}>
              <KindBadge kind={s.kind} /> <span>{s.text}</span>{" "}
              <a
                href={url ?? undefined}
                target="_blank"
                rel="noreferrer"
                className="ml-1 inline-flex items-center gap-1 rounded border border-line px-1.5 text-[11px] text-muted hover:text-ink"
                title={`${s.citation.source}, ${s.citation.clause}, ${s.citation.locator} (${s.citation.url_or_repo_path})${s.verification ? `\nVerified (${s.verification.by}): "${s.verification.quote}" at ${s.verification.where}` : ""}${s.citation.primary ? `\nPrimary ${s.citation.primary.result}: ${s.citation.primary.clause}${s.citation.primary.quote ? ` — "${s.citation.primary.quote}"` : ""} (${s.citation.primary.url})` : ""}`}
                data-testid="cite-chip"
              >
                {s.citation.source_id} · {s.citation.clause} · <span className="font-semibold">{s.citation.status}</span>
                {s.citation.primary?.result === "CONFIRMED" && (
                  <span className="font-semibold text-ok" data-testid="primary-confirmed">PRIMARY ✓</span>
                )}
              </a>
            </li>
          );
        })}
      </ul>
      {hidden > 0 && (
        <p className="mt-2 text-xs text-muted" data-testid="hidden-count">
          {hidden} sentence{hidden > 1 ? "s" : ""} hidden: source needed.
        </p>
      )}
    </div>
  );
}
