/**
 * Simulator view state. Every field round-trips through the URL query string so any view (level, element,
 * scenario, replicate, arm, time, open panel) is a deep link.
 */
export type Level = 1 | 2 | 3 | 4;
export type Arm = "side" | "control" | "loop";
export type Lls = "c1" | "c2" | "c3" | "c4";

export interface SimState {
  level: Level;
  lls: Lls;
  focus: string | null; // architecture element id shown in the side panel
  scenario: string;
  rep: number;
  arm: Arm;
  t: number; // seconds relative to fault onset T0
  results: boolean;
  pkt: "exchange" | "bmca" | "attack" | "counts";
  panel: string | null; // lessons | lesson:<id> | sandbox | catalogue | datasets (server-rendered below the diagram)
}

export const PANEL_RE = /^(lessons|lesson:[a-z-]{1,40}|sandbox|catalogue|datasets)$/;

export const T_MIN = -20;
export const T_MAX = 41;
export const REPS = [13, 14, 15, 16, 17];
export const DEFAULT_STATE: SimState = {
  level: 1, lls: "c3", focus: null, scenario: "A1_rogue_master", rep: 13, arm: "side", t: -3, results: false, pkt: "exchange", panel: null,
};

const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));

export function parseState(q: URLSearchParams | Record<string, string | string[] | undefined>): SimState {
  const get = (k: string) => {
    if (q instanceof URLSearchParams) return q.get(k) ?? undefined;
    const v = q[k];
    return Array.isArray(v) ? v[0] : v;
  };
  const s = { ...DEFAULT_STATE };
  const lv = Number(get("level"));
  if ([1, 2, 3, 4].includes(lv)) s.level = lv as Level;
  const lls = get("lls");
  if (lls && ["c1", "c2", "c3", "c4"].includes(lls)) s.lls = lls as Lls;
  const focus = get("focus");
  if (focus && /^[a-z0-9-]{1,40}$/.test(focus)) s.focus = focus;
  const sc = get("scenario");
  if (sc && /^[A-Za-z0-9_]{1,40}$/.test(sc)) s.scenario = sc;
  const rep = Number(get("rep"));
  if (REPS.includes(rep)) s.rep = rep;
  const arm = get("arm");
  if (arm === "side" || arm === "control" || arm === "loop") s.arm = arm;
  const t = Number(get("t"));
  if (get("t") !== undefined && Number.isFinite(t)) s.t = clamp(Math.round(t * 10) / 10, T_MIN, T_MAX);
  s.results = get("results") === "1";
  const pkt = get("pkt");
  if (pkt === "exchange" || pkt === "bmca" || pkt === "attack" || pkt === "counts") s.pkt = pkt;
  const panel = get("panel");
  if (panel && PANEL_RE.test(panel)) s.panel = panel;
  return s;
}

/** Only non-default fields are written, so the home URL stays "/". */
export function serializeState(s: SimState): string {
  const p = new URLSearchParams();
  const d = DEFAULT_STATE;
  if (s.level !== d.level) p.set("level", String(s.level));
  if (s.lls !== d.lls) p.set("lls", s.lls);
  if (s.focus) p.set("focus", s.focus);
  if (s.level >= 3) {
    if (s.scenario !== d.scenario) p.set("scenario", s.scenario);
    if (s.rep !== d.rep) p.set("rep", String(s.rep));
    if (s.arm !== d.arm) p.set("arm", s.arm);
    if (s.t !== d.t) p.set("t", s.t.toFixed(1));
    if (s.level === 3 && s.pkt !== d.pkt) p.set("pkt", s.pkt);
  }
  if (s.panel) p.set("panel", s.panel);
  if (s.results) p.set("results", "1");
  const str = p.toString();
  return str ? `/?${str}` : "/";
}

/** Esc / Back: close the results overlay, else close the panel, else go up one level (clearing the selection); at level 1 clear the selection. */
export function up(s: SimState): SimState {
  if (s.results) return { ...s, results: false };
  if (s.panel) return { ...s, panel: null };
  if (s.level > 1) return { ...s, level: (s.level - 1) as Level, focus: null };
  if (s.focus) return { ...s, focus: null };
  return s;
}

/** Which level an element click zooms into (null = stay, just focus). */
export const ZOOM_TARGET: Record<string, Level> = {
  "fh-splane": 2, "o-du": 2, "o-ru": 2, "lls-c1": 2, "lls-c2": 2, "lls-c3": 2, "lls-c4": 2,
  bc: 3, "bc-standby": 3, "gm-a": 3, "gm-b": 3, injector: 3,
  "smo-nonrt": 4, "recovery-loop": 4,
};

export function select(s: SimState, id: string): SimState {
  const lv = ZOOM_TARGET[id];
  const next: SimState = { ...s, focus: id };
  if (lv && lv > s.level) next.level = lv;
  if (id.startsWith("lls-")) next.lls = id.slice(4) as Lls;
  return next;
}

export const LEVEL_NAME: Record<Level, string> = {
  1: "O-RAN architecture",
  2: "Open fronthaul (LLS)",
  3: "S-plane testbed",
  4: "Recovery loop",
};
