/**
 * Scene layout (data only): where each architecture element is drawn at each level, and the guided camera poses.
 * Every drawn id must exist in content/architecture.json and list the level in its `levels` (checked by unit tests),
 * so no part can appear without content behind it.
 */
import type { LlsId } from "./explorerState";

export type V3 = [number, number, number];

export type Shape = "rack" | "oru" | "cloud" | "sat" | "slab" | "block" | "phone" | "rings" | "chip" | "injector" | "standby";

export interface PartSpec {
  id: string; // architecture element id
  shape: Shape;
  pos: V3;
  /** camera offset from the part when focused */
  view: V3;
  label?: string; // short floating label (defaults to a short form of the element name)
  size?: V3;
  /** drawn dimmed because the part is not in the testbed's configuration (level 2, LLS-C1/C2/C4) */
  ghost?: boolean;
}

export interface LinkSpec {
  id: string; // architecture element id the link represents (clickable)
  points: V3[];
  role: "splane" | "mplane" | "cplane" | "uplane" | "synce" | "plain";
  /** packets animate along this link (ILLUSTRATIVE) */
  flow?: boolean;
  ghost?: boolean;
  label?: string;
}

export interface Pose {
  position: V3;
  target: V3;
  minDistance: number;
  maxDistance: number;
}

/** Orbit limits shared by the scene and the pose data. Every pose is clamped into them so a flight always ends. */
export const POLAR_MIN = 0.35;
export const POLAR_MAX = 1.5;
export const AZIMUTH_LIMIT = 0.95;
const POLAR_SAFE: [number, number] = [POLAR_MIN + 0.05, POLAR_MAX - 0.05];

export function clampPose(p: Pose): Pose {
  const o = [p.position[0] - p.target[0], p.position[1] - p.target[1], p.position[2] - p.target[2]];
  let r = Math.hypot(o[0], o[1], o[2]);
  r = Math.min(p.maxDistance, Math.max(p.minDistance, r));
  let phi = Math.acos(Math.max(-1, Math.min(1, (p.position[1] - p.target[1]) / (Math.hypot(...o) || 1))));
  let theta = Math.atan2(o[0], o[2]);
  phi = Math.min(POLAR_SAFE[1], Math.max(POLAR_SAFE[0], phi));
  theta = Math.min(AZIMUTH_LIMIT - 0.05, Math.max(-AZIMUTH_LIMIT + 0.05, theta));
  const position: V3 = [p.target[0] + r * Math.sin(phi) * Math.sin(theta), p.target[1] + r * Math.cos(phi), p.target[2] + r * Math.sin(phi) * Math.cos(theta)];
  return { ...p, position };
}

export const SHORT: Record<string, string> = {
  "gm-a": "GM-A", "gm-b": "GM-B", bc: "BC", "bc-standby": "Standby BC", "o-ru": "O-RU", "fh-splane": "S-plane", injector: "Injector",
  "o-du": "O-DU", "fh-mplane": "M-plane", "smo-nonrt": "SMO / Non-RT RIC", "gnss-time": "GNSS / PRTC", synce: "SyncE", "osc-drift": "Oscillator (B6)",
  "fh-cplane": "C-plane", "fh-uplane": "U-plane", "air-interface": "Air interface", ue: "UE", "near-rt-ric": "Near-RT RIC", "o-cu": "O-CU",
  "core-5g": "5G Core", "o-cloud": "O-Cloud",
};

// ------------------------------------------------------------------ level 1: whole O-RAN
export const L1_PARTS: PartSpec[] = [
  { id: "core-5g", shape: "cloud", pos: [-25, 3.2, -2], view: [0, 3, 14] },
  { id: "o-cloud", shape: "rack", pos: [-20, 0, 6], size: [2.6, 3.4, 1.6], view: [0, 3, 12] },
  { id: "smo-nonrt", shape: "slab", pos: [-13, 8.5, -9], size: [6, 0.5, 2.6], view: [2, 3, 14] },
  { id: "near-rt-ric", shape: "slab", pos: [-13, 4.4, -5], size: [4.4, 0.5, 2.2], view: [0, 3, 13] },
  { id: "o-cu", shape: "rack", pos: [-6, 0, -1], size: [2.4, 3.6, 1.6], view: [0, 3, 12] },
  { id: "o-du", shape: "rack", pos: [3, 0, 0], size: [2.4, 3.6, 1.6], view: [0, 3, 12] },
  { id: "gnss-time", shape: "sat", pos: [-8, 16, 2], view: [0, -1, 14] },
  { id: "gm-a", shape: "rack", pos: [-14.5, 0, 8], size: [1.8, 3, 1.4], view: [2, 3, 10] },
  { id: "gm-b", shape: "rack", pos: [-9.5, 0, 8], size: [1.8, 3, 1.4], view: [-2, 3, 10] },
  { id: "bc", shape: "block", pos: [8, 0, 6], size: [2.4, 1.8, 1.4], view: [0, 3, 10] },
  { id: "o-ru", shape: "oru", pos: [16, 7.4, 0.8], size: [1.5, 2.1, 0.7], view: [-3, 1.5, 11] },
  { id: "osc-drift", shape: "chip", pos: [20, 3.4, 2.6], size: [0.9, 0.35, 0.9], view: [0, 1.5, 6] },
  { id: "injector", shape: "injector", pos: [11.2, 2.4, 3.6], view: [0, 2, 8] },
  { id: "air-interface", shape: "rings", pos: [23, 7.4, 0.8], view: [0, 1, 14] },
  { id: "ue", shape: "phone", pos: [29, 0.9, 2.5], size: [0.6, 1.1, 0.12], view: [0, 2, 9] },
];
export const L1_LINKS: LinkSpec[] = [
  // S-plane follows the LLS-C3 structure: grandmasters -> boundary clock -> O-RU (not through the O-DU)
  { id: "fh-splane", role: "splane", flow: true, points: [[-14.5, 1.6, 8], [-2, 0.9, 7.5], [8, 0.9, 6], [11.2, 2.4, 3.6], [16, 6.4, 0.8]], label: "S-plane (PTP)" },
  { id: "synce", role: "synce", points: [[-9.5, 2.2, 8.4], [2, 1.5, 9], [8.6, 1.5, 7.2], [14.4, 4, 2.6], [16.4, 6.3, 1.2]] },
  { id: "fh-mplane", role: "mplane", points: [[3.4, 3.0, 0.4], [10, 5, 0.2], [15.4, 7.2, 0.5]] },
  { id: "fh-cplane", role: "cplane", points: [[3.4, 2.4, 0], [10, 4.5, -0.3], [15.4, 7.6, 0.6]] },
  { id: "fh-uplane", role: "uplane", points: [[3.4, 1.8, -0.4], [10, 4.0, -0.8], [15.4, 8.0, 0.4]] },
];
export const L1_POSE: Pose = { position: [3, 11, 58], target: [3, 4.5, 0], minDistance: 20, maxDistance: 100 };

// ------------------------------------------------------------------ level 2: open fronthaul, per LLS configuration
export interface Level2Layout {
  parts: PartSpec[];
  links: LinkSpec[];
  bars?: { y: number; x0: number; x1: number; label: string }[]; // bridge bars
  note: string; // diagram-only note (instructional)
  testbed: boolean;
  /** extra non-element blocks (labelled with the source wording) */
  decor?: { id: string; pos: V3; label: string; size?: V3; ghost?: boolean }[];
  pose: Pose;
}
const B: V3 = [3.6, 1.7, 1.2];
const view2: V3 = [0, 1.5, 15];
export function level2(lls: LlsId): Level2Layout {
  switch (lls) {
    case "c3":
      return {
        testbed: true, note: "Testbed configuration (LLS-C3 structure). Motion on the links is illustrative.",
        parts: [
          { id: "gm-a", shape: "block", pos: [-13, 3, 0], size: B, view: view2 },
          { id: "gm-b", shape: "block", pos: [-13, -3, 0], size: B, view: view2 },
          { id: "bc", shape: "block", pos: [-3, 0, 0], size: B, view: view2 },
          { id: "bc-standby", shape: "standby", pos: [-3, -5, 0], size: B, view: view2 },
          { id: "o-ru", shape: "oru", pos: [9, 0, 0], size: [3.4, 6.4, 1.2], view: [0, 1, 13], label: "RU1 · RU2 · RU3" },
          { id: "injector", shape: "injector", pos: [14, -3.2, 0.6], view: [0, 1, 9] },
          { id: "o-du", shape: "rack", pos: [-3, 6.2, -2], size: [2.6, 2.2, 1.4], view: [0, 0, 10] },
        ],
        links: [
          { id: "fh-splane", role: "splane", flow: true, points: [[-11.2, 3, 0], [-7.5, 3, 0], [-7.5, 0, 0], [-4.8, 0, 0]], label: "brUP" },
          { id: "fh-splane", role: "splane", flow: true, points: [[-11.2, -3, 0], [-7.5, -3, 0], [-7.5, 0, 0]] },
          { id: "fh-splane", role: "splane", flow: true, points: [[-1.2, 0, 0], [2.5, 0, 0], [7.2, 0, 0]], label: "brDN" },
          { id: "fh-splane", role: "splane", points: [[-7.5, 0, 0], [-7.5, -5, 0], [-4.8, -5, 0]], ghost: true },
          { id: "fh-splane", role: "splane", points: [[-1.2, -5, 0], [2.5, -5, 0], [2.5, 0, 0]], ghost: true },
          { id: "fh-mplane", role: "mplane", points: [[-1.7, 6.2, -2], [9, 6.2, -2], [9, 3.4, -0.4]], ghost: true, label: "not in the timing chain" },
        ],
        pose: { position: [0.5, 3, 41], target: [0.5, 0, 0], minDistance: 14, maxDistance: 60 },
      };
    case "c1":
      return {
        testbed: false, note: "Not the testbed's configuration (the testbed has no O-DU in its timing chain).",
        parts: [
          { id: "o-du", shape: "rack", pos: [-8, 0, 0], size: [2.8, 3.2, 1.4], view: view2, ghost: true },
          { id: "o-ru", shape: "oru", pos: [8, 0, 0], size: [3, 4, 1.2], view: view2, ghost: true },
        ],
        links: [{ id: "fh-splane", role: "splane", points: [[-6.4, 0, 0], [0, 0, 0], [6.4, 0, 0]], ghost: true, label: "direct link" }],
        pose: { position: [0, 2, 28], target: [0, 0, 0], minDistance: 12, maxDistance: 46 },
      };
    case "c2":
      return {
        testbed: false, note: "Not the testbed's configuration (the testbed has no O-DU in its timing chain).",
        parts: [
          { id: "o-du", shape: "rack", pos: [-11, 0, 0], size: [2.8, 3.2, 1.4], view: view2, ghost: true },
          { id: "o-ru", shape: "oru", pos: [11, 0, 0], size: [3, 4, 1.2], view: view2, ghost: true },
        ],
        decor: [{ id: "switch", pos: [0, 0, 0], label: "Ethernet switch(es)", size: [3.6, 1.4, 1.2], ghost: true }],
        links: [
          { id: "fh-splane", role: "splane", points: [[-9.4, 0, 0], [-1.9, 0, 0]], ghost: true },
          { id: "fh-splane", role: "splane", points: [[1.9, 0, 0], [9.4, 0, 0]], ghost: true },
        ],
        pose: { position: [0, 2, 32], target: [0, 0, 0], minDistance: 12, maxDistance: 48 },
      };
    case "c4":
    default:
      return {
        testbed: false, note: "Not the testbed's configuration (the testbed has no GNSS receiver).",
        parts: [
          { id: "gnss-time", shape: "sat", pos: [0, 7, 0], view: [0, -1, 11], ghost: true },
          { id: "o-ru", shape: "oru", pos: [0, -2, 0], size: [3, 4, 1.2], view: view2, ghost: true },
        ],
        decor: [{ id: "gnss-rx", pos: [6.5, -2, 0], label: "local GNSS receiver (typical)", size: [3.2, 1.2, 1], ghost: true }],
        links: [
          { id: "gnss-time", role: "plain", points: [[0, 5.6, 0], [0, 0.5, 0]], ghost: true, label: "no network timing" },
        ],
        pose: { position: [0, 2, 24], target: [0, 1, 0], minDistance: 12, maxDistance: 40 },
      };
  }
}

export function partsAt(level: number, lls: LlsId): PartSpec[] {
  return level === 1 ? L1_PARTS : level === 2 ? level2(lls).parts : [];
}
export function linksAt(level: number, lls: LlsId): LinkSpec[] {
  return level === 1 ? L1_LINKS : level === 2 ? level2(lls).links : [];
}
export function drawnIds(level: number, lls: LlsId): string[] {
  return [...new Set([...partsAt(level, lls).map((p) => p.id), ...linksAt(level, lls).map((l) => l.id).filter((id) => id !== "gnss-time")])];
}

export function poseFor(level: number, lls: LlsId, focus: string | null): Pose {
  return clampPose(rawPose(level, lls, focus));
}

function rawPose(level: number, lls: LlsId, focus: string | null): Pose {
  const base = level === 1 ? L1_POSE : level2(lls).pose;
  if (!focus) return base;
  const part = partsAt(level, lls).find((p) => p.id === focus);
  if (part) {
    const t = part.pos;
    return { position: [t[0] + part.view[0], t[1] + part.view[1], t[2] + part.view[2]], target: t, minDistance: 4, maxDistance: 30 };
  }
  const link = linksAt(level, lls).find((l) => l.id === focus);
  if (link) {
    const m = link.points[Math.floor(link.points.length / 2)];
    return { position: [m[0], m[1] + 3, m[2] + 12], target: m, minDistance: 5, maxDistance: 32 };
  }
  return base;
}
