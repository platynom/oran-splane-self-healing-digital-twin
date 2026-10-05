"use client";
import { useState } from "react";
import clsx from "clsx";
import { referenceUrl, type Citation as C } from "@/lib/architecture";

/** Citation chip; clicking shows the reference (source, clause, locator, link, verification status). */
export function CitationChip({ citation, sentenceId }: { citation: C; sentenceId: string }) {
  const [open, setOpen] = useState(false);
  const url = referenceUrl(citation);
  const external = !!citation.url_or_repo_path && /^https?:\/\//.test(citation.url_or_repo_path);
  return (
    <span className="inline-block align-baseline">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={`ref-${sentenceId}`}
        onClick={() => setOpen((o) => !o)}
        className={clsx("ml-1 rounded border px-1.5 py-0.5 text-[0.7rem] font-semibold leading-none", open ? "border-accent bg-accent-soft" : "border-line hover:border-accent")}
        data-testid={`cite-${sentenceId}`}
      >
        [{citation.source_id} · {citation.clause}]
      </button>
      {open && (
        <span id={`ref-${sentenceId}`} role="note" className="mt-1 block rounded-md border border-line bg-surface-2 p-2 text-xs" data-testid={`ref-${sentenceId}`}>
          <span className="block font-semibold">{citation.source}</span>
          <span className="block">
            <span className="text-muted">Clause: </span>
            {citation.clause}
          </span>
          <span className="block">
            <span className="text-muted">Where: </span>
            {citation.locator}
          </span>
          <span className="block break-all">
            <span className="text-muted">{external ? "URL: " : "Repository path: "}</span>
            {url ? (
              <a className="underline" href={url} target="_blank" rel="noreferrer">
                {citation.url_or_repo_path}
              </a>
            ) : (
              "–"
            )}
          </span>
          <span className="mt-1 inline-block rounded border border-warn px-1.5 py-0.5 font-bold uppercase text-warn">{citation.status}</span>
          <span className="ml-2 text-muted">not yet checked by a person</span>
        </span>
      )}
    </span>
  );
}
