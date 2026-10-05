/**
 * Outcome metrics for one recovery-loop run, computed from the passive-observer samples exactly as
 * 03_RECOVERY_LOOP_S-PLANE/PREREGISTRATION.md section 4 defines them (and as code/analyse.py implements them).
 *
 * Pure functions: no database access. scripts/ingest.ts stores the results on the Run rows, and the unit
 * tests re-run them on rows read back from PostgreSQL.
 */

export const ALLOW_GM = new Set(["020000fffe00000a", "020000fffe00000b"]);
export const LEGIT_PARENT = ["020000fffe000001", "020000fffe0000c5"]; // primary BC, standby BC
export const PRIMARY_NODES = ["ru1", "ru2"] as const;
export const OWN_IDENTITY: Record<string, string> = {
  ru1: "020000fffe00000c",
  ru2: "020000fffe00000d",
  ru3: "020000fffe00000e",
};
export const WINDOW_S = 40; // [T0, T0 + 40 s]
export const TAIL_S = 5; // "restored at end" = healthy throughout the final 5 s
export const DISRUPTIVE = new Set(["ISOLATE_PTP_AT_PORT", "ACTIVATE_STANDBY_BC"]);

export interface SampleLike {
  round: number;
  tMono: number; // raw CLOCK_MONOTONIC stamp from observer.jsonl
  t: number; // seconds relative to T0 (display; rounded to ms)
  node: string;
  portState: string | null;
  parent: string | null;
  gm: string | null;
}

export interface EventLike {
  t: number;
  tMono?: number | null;
  source: string;
  kind: string;
  verdict?: string | null;
  action?: string | null;
  target?: string | null;
  ok?: boolean | null;
}

/** PREREGISTRATION.md s4: parent in the provisioned set, GM in the allow-list, portState SLAVE or UNCALIBRATED. */
export function isHealthy(s: Pick<SampleLike, "portState" | "parent" | "gm">, legit: Set<string>): boolean {
  return (
    (s.portState === "SLAVE" || s.portState === "UNCALIBRATED") &&
    s.parent !== null &&
    legit.has(s.parent) &&
    s.gm !== null &&
    ALLOW_GM.has(s.gm)
  );
}

export function legitParentsFor(secondaryBc?: string | null): Set<string> {
  const s = new Set(LEGIT_PARENT);
  if (secondaryBc) s.add(secondaryBc);
  return s;
}

type Round = { t: number; nodes: Map<string, SampleLike> };

/**
 * Group samples into observer poll rounds; a round's time is its earliest raw stamp minus T0
 * (analyse.py t_of). Using the raw CLOCK_MONOTONIC stamps keeps the floating-point arithmetic identical
 * to analyse.py, so sums round to exactly the same hundredths.
 */
export function toRounds(samples: SampleLike[], t0Mono: number): Round[] {
  const by = new Map<number, Round>();
  for (const s of samples) {
    let r = by.get(s.round);
    if (!r) {
      r = { t: Infinity, nodes: new Map() };
      by.set(s.round, r);
    }
    r.nodes.set(s.node, s);
    r.t = Math.min(r.t, s.tMono);
  }
  for (const r of by.values()) r.t = r.t - t0Mono;
  return [...by.entries()].sort((a, b) => a[0] - b[0]).map(([, r]) => r);
}

/**
 * Python's round(x, n): decimal rounding of the exact binary value, with exact ties going to the even digit
 * (round(2.125, 2) == 2.12 in Python, while (2.125).toFixed(2) == "2.13" in JavaScript).
 */
export function pyRound(x: number, n: number): number {
  const neg = x < 0;
  const s = Math.abs(x).toFixed(Math.min(100, n + 40)); // exact decimal digits of the double, far past any tie
  const [ip, fp = ""] = s.split(".");
  const keep = fp.slice(0, n);
  const tail = fp.slice(n);
  if (/^50*$/.test(tail)) {
    const last = Number(n > 0 ? keep[n - 1] : ip[ip.length - 1]);
    const base = Number(n > 0 ? `${ip}.${keep}` : ip);
    const v = last % 2 === 0 ? base : base + 10 ** -n;
    const r = Number(v.toFixed(n));
    return neg ? -r : r;
  }
  const r = Number(Math.abs(x).toFixed(n));
  return neg ? -r : r;
}
const round2 = (x: number) => pyRound(x, 2);
const round3 = (x: number) => pyRound(x, 3);

export interface RunMetrics {
  unhealthyS: number;
  ru3UnhealthyS: number;
  rogueParentS: number;
  restoredAtEnd: boolean;
  preT0ServiceOk: number;
  firstUnhealthyS: number | null;
  outageS: number | null;
  firstAttackVerdictS: number | null;
  firstActionS: number | null;
}

export function computeRunMetrics(
  samples: SampleLike[],
  events: EventLike[],
  legit: Set<string>,
  t0Mono: number,
): RunMetrics {
  const rounds = toRounds(samples, t0Mono);
  const post = rounds.filter((r) => r.t >= 0 && r.t <= WINDOW_S);
  const pre = rounds.filter((r) => r.t >= -10 && r.t < 0);
  const ok = (r: Round, nodes: readonly string[] = PRIMARY_NODES) =>
    nodes.every((n) => {
      const s = r.nodes.get(n);
      return s !== undefined && isHealthy(s, legit);
    });
  const sumWhile = (pred: (r: Round) => boolean) => {
    let acc = 0;
    for (let i = 0; i + 1 < post.length; i++) if (pred(post[i])) acc += post[i + 1].t - post[i].t;
    return acc;
  };
  const unhealthy = sumWhile((r) => !ok(r));
  const ru3 = sumWhile((r) => !ok(r, ["ru3"]));
  const foreign = (r: Round) =>
    PRIMARY_NODES.some((n) => {
      const s = r.nodes.get(n);
      if (!s) return false;
      const p = s.parent ?? "";
      return !(legit.has(p) || p === "" || p === OWN_IDENTITY[n]);
    });
  const rogue = sumWhile(foreign);
  const tail = post.filter((r) => r.t >= WINDOW_S - TAIL_S);
  const restored = tail.length > 0 && tail.every((r) => ok(r));
  const preOk = pre.filter((r) => ok(r)).length / Math.max(1, pre.length);
  const firstBad = post.find((r) => !ok(r));
  let outage: number | null = null;
  if (firstBad && restored) {
    const bad = post.filter((r) => !ok(r));
    const lastBad = Math.max(...bad.map((r) => r.t));
    const nxt = post.find((r) => r.t > lastBad);
    outage = round2((nxt ? nxt.t : lastBad) - firstBad.t);
  }
  // analyse.py: te = round(t_mono - t0, 2), compared against 0 after rounding
  const loopEv = events
    .filter((e) => e.source === "loop")
    .map((e) => ({ ...e, te: e.tMono != null ? round2(e.tMono - t0Mono) : round2(e.t) }));
  const firstAttack = loopEv.find((e) => e.kind === "eval" && e.verdict === "ATTACK" && e.te >= 0);
  const firstAction = loopEv.find((e) => (e.kind === "act" || e.kind === "would_act") && e.te >= 0);
  return {
    unhealthyS: round2(unhealthy),
    ru3UnhealthyS: round2(ru3),
    rogueParentS: round2(rogue),
    restoredAtEnd: restored,
    preT0ServiceOk: round3(preOk),
    firstUnhealthyS: firstBad ? firstBad.t : null,
    outageS: outage,
    firstAttackVerdictS: firstAttack ? firstAttack.te : null,
    firstActionS: firstAction ? firstAction.te : null,
  };
}

export function median(xs: number[]): number {
  if (xs.length === 0) return NaN;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** Wilson score interval, as used in RESULTS_2026-10-05.md and evaluate_v4.py. */
export function wilson(k: number, n: number, z = 1.96): [number, number, number] {
  if (n === 0) return [NaN, NaN, NaN];
  const p = k / n;
  const d = 1 + (z * z) / n;
  const c = (p + (z * z) / (2 * n)) / d;
  const h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  const r4 = (x: number) => Math.round(x * 1e4) / 1e4;
  return [r4(p), r4(Math.max(0, c - h)), r4(Math.min(1, c + h))];
}

/** Display rule used throughout the UI: one decimal, as in RESULTS_2026-10-05.md. */
export function fmtS(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "–";
  return `${x.toFixed(digits)} s`;
}
