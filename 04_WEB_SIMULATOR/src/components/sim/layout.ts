/**
 * 2D positions for the level-1 O-RAN diagram and the level-2 fronthaul zoom. Positions are ILLUSTRATIVE
 * (drawing layout only); which elements exist, their tier and their text come from content/architecture.json.
 */
import type { Lls } from "@/lib/sim/state";

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export const NODES: Record<string, Box> = {
  "smo-nonrt": { x: 300, y: 16, w: 420, h: 62 },
  "near-rt-ric": { x: 760, y: 20, w: 190, h: 50 },
  "o-cloud": { x: 990, y: 20, w: 180, h: 50 },
  "o-du": { x: 520, y: 110, w: 200, h: 56 },
  "o-cu": { x: 760, y: 112, w: 190, h: 50 },
  "core-5g": { x: 990, y: 112, w: 180, h: 50 },
  "gnss-time": { x: 30, y: 110, w: 190, h: 50 },
  "gm-a": { x: 30, y: 196, w: 190, h: 56 },
  "gm-b": { x: 30, y: 284, w: 190, h: 56 },
  synce: { x: 30, y: 372, w: 190, h: 44 },
  bc: { x: 280, y: 236, w: 190, h: 56 },
  "bc-standby": { x: 280, y: 324, w: 190, h: 50 },
  "fh-mplane": { x: 520, y: 200, w: 200, h: 42 },
  "fh-splane": { x: 520, y: 258, w: 200, h: 54 },
  "fh-cplane": { x: 520, y: 330, w: 96, h: 40 },
  "fh-uplane": { x: 624, y: 330, w: 96, h: 40 },
  "o-ru": { x: 790, y: 200, w: 200, h: 176 },
  injector: { x: 520, y: 410, w: 200, h: 50 },
  "osc-drift": { x: 30, y: 440, w: 220, h: 50 },
  "air-interface": { x: 1030, y: 236, w: 150, h: 50 },
  ue: { x: 1030, y: 320, w: 150, h: 50 },
};

export const RU_SUB = ["RU1", "RU2", "RU3"];

/** [from, to, kind]; kind drives the stroke. */
export const LINKS: [string, string, "sync" | "mgmt" | "data" | "attack" | "dim" | "standby" | "freq" | "radio"][] = [
  ["gnss-time", "gm-a", "sync"],
  ["gm-a", "bc", "sync"],
  ["gm-b", "bc", "sync"],
  ["synce", "bc", "freq"],
  ["bc", "fh-splane", "sync"],
  ["bc-standby", "fh-splane", "standby"],
  ["fh-splane", "o-ru", "sync"],
  ["o-du", "fh-mplane", "mgmt"],
  ["fh-mplane", "o-ru", "mgmt"],
  ["fh-cplane", "o-ru", "data"],
  ["fh-uplane", "o-ru", "data"],
  ["o-du", "fh-cplane", "data"],
  ["o-du", "fh-uplane", "data"],
  ["injector", "fh-splane", "attack"],
  ["smo-nonrt", "o-du", "mgmt"],
  ["near-rt-ric", "o-du", "dim"],
  ["o-cu", "o-du", "dim"],
  ["core-5g", "o-cu", "dim"],
  ["o-ru", "air-interface", "radio"],
  ["air-interface", "ue", "radio"],
];

export const VIEWBOX: Record<"l1" | "l2" | "splane", [number, number, number, number]> = {
  l1: [0, 0, 1200, 500],
  l2: [260, 90, 760, 330], // the open fronthaul between O-DU, timing chain and O-RU
  splane: [270, 220, 520, 180], // zoom target before switching to the level-3 testbed replay
};

export const center = (b: Box) => ({ x: b.x + b.w / 2, y: b.y + b.h / 2 });

/** Edge point of box a towards box b (keeps arrows off the labels). */
export function edge(a: Box, b: Box) {
  const ca = center(a), cb = center(b);
  const dx = cb.x - ca.x, dy = cb.y - ca.y;
  const sx = dx === 0 ? Infinity : a.w / 2 / Math.abs(dx);
  const sy = dy === 0 ? Infinity : a.h / 2 / Math.abs(dy);
  const s = Math.min(sx, sy);
  return { x: ca.x + dx * s, y: ca.y + dy * s };
}

/**
 * Level 2: the timing path each low-layer split configuration implies (drawn over the zoomed diagram).
 * Points are drawing coordinates; the meaning of each configuration is in the lls-c* content sentences.
 */
export const LLS_PATH: Record<Lls, { d: string; glyph?: { x: number; y: number; label: string } }> = {
  c1: { d: "M 720 150 C 760 160, 780 190, 800 210" },
  c2: { d: "M 720 150 L 755 182 L 800 214", glyph: { x: 755, y: 182, label: "switch" } },
  c3: { d: "M 220 224 L 280 258 L 470 266 L 520 282 L 720 286 L 790 288" },
  c4: { d: "M 890 160 L 890 200", glyph: { x: 890, y: 150, label: "local GNSS" } },
};
