export type ThemeName = "dark" | "projector";
export type TextSize = "normal" | "large";
export type QualityLevel = "high" | "medium" | "low";

export interface ScenePalette {
  bg: string;
  fog: string;
  ground: string;
  grid: string;
  tier1: string;
  tier2: string;
  tier3: string;
  dimmed: string;
  edge: string;
  splane: string;
  mplane: string;
  cplane: string;
  uplane: string;
  synce: string;
  attack: string;
  ink: string;
  glow: number; // emissive intensity multiplier
  lineWidth: number;
}

export const PALETTES: Record<ThemeName, ScenePalette> = {
  dark: {
    bg: "#070d18", fog: "#070d18", ground: "#0b1424", grid: "#17304f",
    tier1: "#2fe0d0", tier2: "#6aa8ff", tier3: "#ffc15a", dimmed: "#4a5568", edge: "#bfe9ff",
    splane: "#2fe0d0", mplane: "#6aa8ff", cplane: "#c58bff", uplane: "#ffc15a", synce: "#ff9f5a", attack: "#ff5a5a", ink: "#e6edf7", glow: 1, lineWidth: 3,
  },
  projector: {
    bg: "#ffffff", fog: "#ffffff", ground: "#eef1f5", grid: "#9aa7b8",
    tier1: "#006b66", tier2: "#0b3d91", tier3: "#8a4b00", dimmed: "#9aa3ad", edge: "#000000",
    splane: "#006b66", mplane: "#0b3d91", cplane: "#5b2a99", uplane: "#8a4b00", synce: "#a33a00", attack: "#b00020", ink: "#000000", glow: 0.35, lineWidth: 5,
  },
};

export interface QualitySettings {
  dpr: [number, number];
  particles: number; // packets per flowing link
  antialias: boolean;
  segments: number;
}
export const QUALITY: Record<QualityLevel, QualitySettings> = {
  high: { dpr: [1, 2], particles: 14, antialias: true, segments: 24 },
  medium: { dpr: [1, 1.5], particles: 8, antialias: true, segments: 14 },
  low: { dpr: [0.75, 1], particles: 0, antialias: false, segments: 8 },
};
export const DOWN: Record<QualityLevel, QualityLevel> = { high: "medium", medium: "low", low: "low" };

/** Initial quality guess for weak devices; the PerformanceMonitor lowers it further if frames are slow. */
export function initialQuality(env: { cores?: number; memory?: number; width: number; reducedMotion: boolean }): QualityLevel {
  if (env.reducedMotion) return "low";
  if ((env.memory !== undefined && env.memory <= 2) || (env.cores !== undefined && env.cores <= 2)) return "low";
  if ((env.memory !== undefined && env.memory <= 4) || (env.cores !== undefined && env.cores <= 4) || env.width < 700) return "medium";
  return "high";
}
