/** Explorer view state and its URL form. Pure functions, shared by the UI and the tests. */
import { architecture, getElement, type Architecture } from "./architecture";

export type LlsId = "c1" | "c2" | "c3" | "c4";
export const LLS_IDS: LlsId[] = ["c1", "c2", "c3", "c4"];
export const TESTBED_LLS: LlsId = "c3";
export const MAX_IMPLEMENTED_LEVEL = 2; // levels 3-5 are phase 2+

export interface ViewState {
  level: number; // 1 whole O-RAN, 2 open fronthaul, 3-5 reserved
  lls: LlsId;
  focus: string | null;
}
export const DEFAULT_VIEW: ViewState = { level: 1, lls: TESTBED_LLS, focus: null };

export const LEVEL_NAMES: Record<number, string> = {
  1: "Whole O-RAN",
  2: "Open Fronthaul",
  3: "S-plane testbed",
  4: "Packet level",
  5: "Recovery loop",
};

export function parseView(params: URLSearchParams, arch: Architecture = architecture): ViewState {
  const lv = Number(params.get("level"));
  const level = Number.isInteger(lv) && lv >= 1 && lv <= 5 ? lv : 1;
  const lls = (LLS_IDS as string[]).includes(params.get("lls") ?? "") ? (params.get("lls") as LlsId) : TESTBED_LLS;
  const f = params.get("focus");
  const el = f ? getElement(f, arch) : undefined;
  // a focus is restored only if the element exists, is clickable and belongs to the requested level
  const focus = el && el.tier !== "dimmed" && el.levels.includes(Math.min(level, MAX_IMPLEMENTED_LEVEL)) ? el.id : null;
  return { level, lls, focus };
}

export function serializeView(v: ViewState): string {
  const p = new URLSearchParams();
  if (v.level !== 1) p.set("level", String(v.level));
  if (v.level === 2 && v.lls !== TESTBED_LLS) p.set("lls", v.lls);
  if (v.focus) p.set("focus", v.focus);
  const s = p.toString();
  return s ? `?${s}` : "";
}

export interface Crumb {
  label: string;
  view: ViewState;
}
export function breadcrumb(v: ViewState, arch: Architecture = architecture): Crumb[] {
  const out: Crumb[] = [{ label: LEVEL_NAMES[1], view: { ...v, level: 1, focus: null } }];
  if (v.level >= 2) {
    const l = `${LEVEL_NAMES[2]} (LLS-${v.lls.toUpperCase()})`;
    out.push({ label: l, view: { ...v, level: 2, focus: null } });
  }
  if (v.focus) out.push({ label: getElement(v.focus, arch)?.name ?? v.focus, view: v });
  return out;
}

/** What Esc / Back does: clear the focus first, then go up one level. */
export function up(v: ViewState): ViewState {
  if (v.focus) return { ...v, focus: null };
  if (v.level > 1) return { ...v, level: v.level - 1, focus: null };
  return v;
}

/**
 * Where selecting an element from `from` leads. Tier 1 and the O-DU/oscillator elements that live at level 2 fly to
 * level 2; everything else stays in the current level and just focuses.
 */
export function select(from: ViewState, id: string, arch: Architecture = architecture): ViewState {
  const el = getElement(id, arch);
  if (!el || el.tier === "dimmed") return from;
  if (from.level === 1 && el.levels.includes(2) && (el.tier === 1 || el.id === "o-du")) return { ...from, level: 2, focus: el.id };
  return { ...from, focus: el.id };
}
