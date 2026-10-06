/**
 * Architecture content (content/architecture.json) and its rendering rules.
 *
 * Rule 1: a sentence is rendered only if its citation is complete and its status is not SOURCE_NEEDED.
 * Rule 2: UNVERIFIED sentences are rendered with an UNVERIFIED tag. VERIFIED is shown only for sentences that carry an
 *         independent auditor's verbatim quote of the cited source ("verification"); validateArchitecture enforces it.
 * Rule 3: kinds (MEASURED / CONFIGURED / ILLUSTRATIVE / UNKNOWN / REFERENCE) are always shown next to the sentence.
 */
import raw from "../../content/architecture.json";

export type Kind = "MEASURED" | "CONFIGURED" | "ILLUSTRATIVE" | "UNKNOWN" | "REFERENCE";
export type CitationStatus = "UNVERIFIED" | "SOURCE_NEEDED" | "VERIFIED";
export type Tier = 1 | 2 | 3 | "dimmed";

export interface Citation {
  source: string | null;
  source_id: string | null;
  clause: string | null;
  locator: string | null;
  url_or_repo_path: string | null;
  status: CitationStatus;
}
export interface Verification {
  by: string;
  quote: string;
  where: string;
}
export interface Sentence {
  id: string;
  kind: Kind;
  text: string;
  citation: Citation;
  verification?: Verification;
}
export interface Element {
  id: string;
  tier: Tier;
  levels: number[];
  name: string;
  role: string;
  sentences: Sentence[];
  sub_elements?: string[];
  consequence_card?: boolean;
  outside_project?: boolean;
  lls?: { testbed: boolean };
}
export interface Source {
  id: string;
  title: string;
  path_or_url: string;
  openable_in_this_session: boolean;
  note: string;
}
export interface Check {
  id: string;
  question: string;
  result: string;
  finding: string;
  evidence: string[];
  element_ids: string[];
}
export interface Architecture {
  schema_version: number;
  generated: string;
  status_note: string;
  kinds: Record<Kind, string>;
  sources: Source[];
  checks: Check[];
  tier_log: { element: string; requested: number | string; final: number | string; result: string; basis: string }[];
  elements: Element[];
}

export const architecture = raw as unknown as Architecture;

export const REPO_BLOB = "https://github.com/platynom/oran-splane-self-healing-digital-twin/blob/full-project-2026-10-05/";
export const APP_BLOB = "https://github.com/platynom/oran-splane-self-healing-digital-twin/blob/webapp-sim/";

export function isRenderable(s: Sentence): boolean {
  const c = s.citation;
  return (
    !!c &&
    c.status !== "SOURCE_NEEDED" &&
    (c.status === "UNVERIFIED" || c.status === "VERIFIED") &&
    !!c.source &&
    !!c.source_id &&
    !!c.url_or_repo_path &&
    !!c.clause &&
    s.text.trim().length > 0
  );
}

export function renderableSentences(el: Element): Sentence[] {
  return el.sentences.filter(isRenderable);
}
export function hiddenSentenceCount(el: Element): number {
  return el.sentences.length - renderableSentences(el).length;
}

export function getElement(id: string, arch: Architecture = architecture): Element | undefined {
  return arch.elements.find((e) => e.id === id);
}

/** A tier 1/2/3 element can be selected; a dimmed element cannot (hover tooltip only). */
export function isClickable(el: Element): boolean {
  return el.tier !== "dimmed";
}

export function referenceUrl(c: Citation): string | null {
  const p = c.url_or_repo_path;
  if (!p) return null;
  if (/^https?:\/\//.test(p)) return p;
  // this app's own files exist only on the webapp branches, not on the project snapshot branch
  const base = p.startsWith("04_WEB_SIMULATOR/") ? APP_BLOB : REPO_BLOB;
  return base + p.split("/").map(encodeURIComponent).join("/");
}

export function contentStats(arch: Architecture = architecture) {
  const all = arch.elements.flatMap((e) => e.sentences);
  const by = (st: CitationStatus) => all.filter((s) => s.citation.status === st).length;
  return {
    elements: arch.elements.length,
    sentences: all.length,
    unverified: by("UNVERIFIED"),
    sourceNeeded: by("SOURCE_NEEDED"),
    verified: by("VERIFIED"),
    rendered: all.filter(isRenderable).length,
    hidden: all.filter((s) => !isRenderable(s)).length,
  };
}

/** Structural problems with the content file; empty when the file obeys the schema and the project's rules. */
export function validateArchitecture(arch: Architecture = architecture): string[] {
  const errs: string[] = [];
  const ids = new Set<string>();
  const srcIds = new Set(arch.sources.map((s) => s.id));
  for (const e of arch.elements) {
    if (ids.has(e.id)) errs.push(`duplicate element ${e.id}`);
    ids.add(e.id);
    if (!e.sentences.length) errs.push(`${e.id}: no sentences`);
    for (const s of e.sentences) {
      if (!s.citation) errs.push(`${s.id}: missing citation`);
      if (s.citation.status === "VERIFIED" && !(s.verification?.quote?.trim() && s.verification.where?.trim() && s.verification.by?.trim()))
        errs.push(`${s.id}: VERIFIED without an auditor's quote and location`);
      if (s.citation.status === "UNVERIFIED" || s.citation.status === "VERIFIED") {
        for (const f of ["source", "source_id", "clause", "locator", "url_or_repo_path"] as const) if (!s.citation[f]) errs.push(`${s.id}: ${s.citation.status} citation lacks ${f}`);
        if (s.citation.source_id && !srcIds.has(s.citation.source_id)) errs.push(`${s.id}: unknown source ${s.citation.source_id}`);
      }
      if (!["MEASURED", "CONFIGURED", "ILLUSTRATIVE", "UNKNOWN", "REFERENCE"].includes(s.kind)) errs.push(`${s.id}: bad kind ${s.kind}`);
    }
  }
  return errs;
}
