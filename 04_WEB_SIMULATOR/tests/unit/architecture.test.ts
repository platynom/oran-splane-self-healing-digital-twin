/** Content loading and hiding rules for content/architecture.json, view-state logic and scene-layout consistency. */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  architecture, contentStats, getElement, hiddenSentenceCount, isClickable, isRenderable, referenceUrl, renderableSentences, validateArchitecture, type Architecture, type Sentence,
} from "@/lib/architecture";
import { breadcrumb, parseView, select, serializeView, up, DEFAULT_VIEW, type ViewState } from "@/lib/explorerState";
import { AZIMUTH_LIMIT, POLAR_MAX, POLAR_MIN, drawnIds, level2, partsAt, linksAt, poseFor } from "@/lib/sceneLayout";
import { initialQuality } from "@/lib/explorerTheme";
import { LLS_IDS } from "@/lib/explorerState";

const REPO = path.resolve(__dirname, "..", "..", "..");
const cite = (status: "UNVERIFIED" | "SOURCE_NEEDED" | "VERIFIED", over: Record<string, unknown> = {}) => ({
  source: "S", source_id: "GUIDE", clause: "c", locator: "l", url_or_repo_path: "x.md", status, ...over,
});
const sent = (status: "UNVERIFIED" | "SOURCE_NEEDED" | "VERIFIED", over: Record<string, unknown> = {}): Sentence => ({
  id: "t.s1", kind: "REFERENCE", text: "A sentence.", citation: cite(status, over) as Sentence["citation"],
});

describe("architecture.json content rules", () => {
  it("passes the structural validation", () => {
    expect(validateArchitecture()).toEqual([]);
  });
  it("hides SOURCE_NEEDED and citation-less sentences, renders UNVERIFIED ones", () => {
    expect(isRenderable(sent("UNVERIFIED"))).toBe(true);
    expect(isRenderable(sent("SOURCE_NEEDED"))).toBe(false);
    expect(isRenderable(sent("UNVERIFIED", { source_id: null }))).toBe(false);
    expect(isRenderable(sent("UNVERIFIED", { clause: "" }))).toBe(false);
    expect(isRenderable(sent("UNVERIFIED", { url_or_repo_path: null }))).toBe(false);
    expect(isRenderable({ ...sent("UNVERIFIED"), text: "  " })).toBe(false);
  });
  it("renderableSentences / hiddenSentenceCount partition every element's sentences", () => {
    for (const e of architecture.elements) {
      expect(renderableSentences(e).length + hiddenSentenceCount(e)).toBe(e.sentences.length);
      expect(renderableSentences(e).every((s) => s.citation.status !== "SOURCE_NEEDED")).toBe(true);
    }
  });
  it("every sentence in this session's file is UNVERIFIED or SOURCE_NEEDED, never VERIFIED", () => {
    const all = architecture.elements.flatMap((e) => e.sentences);
    expect(all.every((s) => s.citation.status === "UNVERIFIED" || s.citation.status === "SOURCE_NEEDED")).toBe(true);
  });
  it("counts (recorded in the phase 1 handoff)", () => {
    expect(contentStats()).toMatchObject({ elements: 25, sentences: 69, unverified: 65, sourceNeeded: 4, verified: 0, rendered: 65, hidden: 4 });
  });
  it("every UNVERIFIED citation points at a repository file that exists and is flagged openable", () => {
    const src = new Map(architecture.sources.map((s) => [s.id, s]));
    for (const e of architecture.elements)
      for (const s of e.sentences.filter((x) => x.citation.status === "UNVERIFIED")) {
        const c = s.citation;
        expect(src.get(c.source_id!)?.openable_in_this_session, s.id).toBe(true);
        expect(existsSync(path.join(REPO, c.url_or_repo_path!)), `${s.id} -> ${c.url_or_repo_path}`).toBe(true);
      }
  });
  it("SOURCE_NEEDED sentences explain why", () => {
    for (const e of architecture.elements) for (const s of e.sentences.filter((x) => x.citation.status === "SOURCE_NEEDED")) expect(s.citation.locator!.length).toBeGreaterThan(20);
  });
  it("the five explicit checks are recorded", () => {
    expect(architecture.checks.map((c) => c.id).sort()).toEqual(["g8271-budget", "lls-mapping", "mplane-yang", "odu-timing-role", "wg11-threats"]);
    expect(architecture.checks.find((c) => c.id === "mplane-yang")!.result).toBe("SOURCE_NEEDED");
    expect(architecture.checks.find((c) => c.id === "lls-mapping")!.result).toContain("LLS-C3");
  });
  it("tier log records the demotion of C-plane and U-plane", () => {
    const d = architecture.tier_log.find((t) => t.element.includes("fh-cplane"))!;
    expect(d.requested).toBe(2);
    expect(d.final).toBe(3);
    expect(getElement("fh-cplane")!.tier).toBe(3);
    expect(getElement("fh-uplane")!.tier).toBe(3);
  });
  it("tiers: dimmed elements are not clickable; tier 1 to 3 are", () => {
    for (const id of ["near-rt-ric", "o-cu", "core-5g", "o-cloud"]) {
      expect(getElement(id)!.tier).toBe("dimmed");
      expect(isClickable(getElement(id)!)).toBe(false);
      expect(getElement(id)!.outside_project).toBe(true);
    }
    for (const id of ["gm-a", "gm-b", "bc", "bc-standby", "o-ru", "fh-splane", "injector"]) expect(getElement(id)!.tier).toBe(1);
    for (const id of ["o-du", "fh-mplane", "smo-nonrt", "gnss-time", "synce"]) expect(getElement(id)!.tier).toBe(2);
    for (const id of ["air-interface", "ue", "fh-cplane", "fh-uplane"]) expect(getElement(id)!.tier).toBe(3);
  });
  it("only LLS-C3 is marked as the testbed's configuration", () => {
    expect(LLS_IDS.filter((l) => getElement(`lls-${l}`)!.lls!.testbed)).toEqual(["c3"]);
  });
  it("lit elements keep at least one renderable sentence; SMO label says 'not implemented there'", () => {
    for (const e of architecture.elements.filter((x) => x.tier !== "dimmed")) expect(renderableSentences(e).length, e.id).toBeGreaterThan(0);
    expect(renderableSentences(getElement("smo-nonrt")!).some((s) => /not implemented there/.test(s.text))).toBe(true);
    expect(getElement("smo-nonrt")!.role).toMatch(/not implemented there/);
  });
  it("the word TDD is not paired with 1.5 µs anywhere in the content", () => {
    const text = JSON.stringify(architecture.elements.map((e) => e.sentences.map((s) => s.text)));
    expect(/TDD[^.]{0,60}1\.5/.test(text) || /1\.5[^.]{0,60}TDD/.test(text)).toBe(false);
  });
  it("evidence kinds: B6 and pilot figures are MEASURED, scope limits UNKNOWN, mappings ILLUSTRATIVE", () => {
    expect(getElement("osc-drift")!.sentences[0].kind).toBe("MEASURED");
    expect(getElement("smo-nonrt")!.sentences.some((s) => s.kind === "ILLUSTRATIVE")).toBe(true);
    expect(getElement("gm-a")!.sentences.some((s) => s.kind === "UNKNOWN")).toBe(true);
  });
  it("referenceUrl builds an openable link for repo paths and passes URLs through", () => {
    expect(referenceUrl(cite("UNVERIFIED", { url_or_repo_path: "00_LATEST/a b.pdf" }) as never)).toBe("https://github.com/platynom/oran-splane-self-healing-digital-twin/blob/full-project-2026-10-05/00_LATEST/a%20b.pdf");
    expect(referenceUrl(cite("UNVERIFIED", { url_or_repo_path: "https://x.org/y" }) as never)).toBe("https://x.org/y");
  });
  it("rejects a file that violates the rules", () => {
    const bad = JSON.parse(JSON.stringify(architecture)) as Architecture;
    bad.elements[0].sentences[0].citation.status = "VERIFIED";
    bad.elements[1].sentences[0].citation.source_id = "NOPE";
    delete (bad.elements[2].sentences[0].citation as Partial<typeof bad.elements[0]["sentences"][0]["citation"]>).clause;
    expect(validateArchitecture(bad).length).toBeGreaterThanOrEqual(3);
  });
  it("the content file contains no phone numbers", () => {
    const t = readFileSync(path.join(__dirname, "..", "..", "content", "architecture.json"), "utf8");
    expect(/\+\d{1,3}[\s-]?\(?\d{2,5}\)?[\s-]?\d{3,5}[\s-]?\d{3,5}\b/.test(t) || /(?<![\d.a-f])[6-9]\d{9}(?![\d.a-f])/.test(t)).toBe(false);
  });
});

describe("scene layout is consistent with the content", () => {
  it("every drawn part exists in the content and lists the level", () => {
    for (const level of [1, 2]) for (const lls of LLS_IDS)
      for (const id of drawnIds(level, lls)) {
        const el = getElement(id);
        expect(el, `${level}/${lls}/${id}`).toBeDefined();
        expect(el!.levels, `${id} at level ${level}`).toContain(level);
      }
  });
  it("level 1 draws every tier-1, tier-2 (except LLS cards), tier-3 and dimmed element that lists level 1", () => {
    const ids = new Set(drawnIds(1, "c3"));
    for (const e of architecture.elements.filter((x) => x.levels.includes(1))) expect(ids.has(e.id), e.id).toBe(true);
  });
  it("level 2 draws the testbed configuration (LLS-C3) with all tier-1 testbed parts", () => {
    const ids = new Set(drawnIds(2, "c3"));
    for (const id of ["gm-a", "gm-b", "bc", "bc-standby", "o-ru", "injector", "fh-splane"]) expect(ids.has(id), id).toBe(true);
    expect(level2("c3").testbed).toBe(true);
    for (const l of ["c1", "c2", "c4"] as const) expect(level2(l).testbed).toBe(false);
  });
  it("no link or time source is drawn from the GM to the O-DU in LLS-C1 (no openable source)", () => {
    const parts = partsAt(2, "c1").map((p) => p.id);
    expect(parts).toEqual(["o-du", "o-ru"]);
    expect(linksAt(2, "c1")).toHaveLength(1);
  });
  it("every pose lies inside the orbit limits (polar, azimuth, distance), so a camera flight always ends", () => {
    const check = (level: number, lls: (typeof LLS_IDS)[number], focus: string | null) => {
      const p = poseFor(level, lls, focus);
      const o = p.position.map((v, i) => v - p.target[i]);
      const r = Math.hypot(...o);
      const phi = Math.acos(o[1] / r);
      const theta = Math.atan2(o[0], o[2]);
      const tag = `${level}/${lls}/${focus}`;
      expect(phi, tag).toBeGreaterThan(POLAR_MIN);
      expect(phi, tag).toBeLessThan(POLAR_MAX);
      expect(Math.abs(theta), tag).toBeLessThan(AZIMUTH_LIMIT);
      expect(r, tag).toBeGreaterThanOrEqual(p.minDistance - 1e-6);
      expect(r, tag).toBeLessThanOrEqual(p.maxDistance + 1e-6);
    };
    for (const level of [1, 2]) for (const lls of LLS_IDS) {
      check(level, lls, null);
      for (const id of drawnIds(level, lls)) check(level, lls, id);
    }
  });
  it("no two drawn parts overlap on screen from the level-1 home camera (nothing is hidden behind another part)", () => {
    // simple pinhole projection of part centres; labels are about 90 px wide, so require 70 px separation at 820 px width
    const pose = poseFor(1, "c3", null);
    const f = new Float64Array(3);
    const fwd = pose.target.map((v, i) => v - pose.position[i]);
    const fl = Math.hypot(...fwd);
    const z = fwd.map((v) => v / fl);
    const x = [z[2], 0, -z[0]];
    const xl = Math.hypot(...x);
    const xn = x.map((v) => v / xl);
    const yv = [xn[1] * z[2] - xn[2] * z[1], xn[2] * z[0] - xn[0] * z[2], xn[0] * z[1] - xn[1] * z[0]];
    const focal = 820 / 2 / Math.tan((42 * Math.PI) / 360) / 1.27;
    const proj = partsAt(1, "c3").map((p) => {
      const d = p.pos.map((v, i) => v - pose.position[i]);
      f[2] = d[0] * z[0] + d[1] * z[1] + d[2] * z[2];
      f[0] = d[0] * xn[0] + d[1] * xn[1] + d[2] * xn[2];
      f[1] = d[0] * yv[0] + d[1] * yv[1] + d[2] * yv[2];
      return { id: p.id, sx: (f[0] / f[2]) * focal, sy: (-f[1] / f[2]) * focal };
    });
    const clashes: string[] = [];
    for (let i = 0; i < proj.length; i++) for (let j = i + 1; j < proj.length; j++) {
      if (Math.abs(proj[i].sx - proj[j].sx) < 70 && Math.abs(proj[i].sy - proj[j].sy) < 22) clashes.push(`${proj[i].id}/${proj[j].id}`);
    }
    expect(clashes).toEqual([]);
  });
  it("every part has a camera pose inside its distance limits", () => {
    for (const level of [1, 2]) for (const lls of LLS_IDS) {
      const base = poseFor(level, lls, null);
      expect(base.minDistance).toBeLessThan(base.maxDistance);
      for (const p of partsAt(level, lls)) {
        const pose = poseFor(level, lls, p.id);
        const d = Math.hypot(...pose.position.map((v, i) => v - pose.target[i]));
        expect(d, `${level}/${lls}/${p.id}`).toBeGreaterThanOrEqual(pose.minDistance);
        expect(d).toBeLessThanOrEqual(pose.maxDistance);
      }
    }
  });
});

describe("view state and deep links", () => {
  it("round-trips level, LLS and focus through the URL", () => {
    for (const v of [DEFAULT_VIEW, { level: 2, lls: "c3" as const, focus: "bc" }, { level: 2, lls: "c1" as const, focus: null }, { level: 1, lls: "c3" as const, focus: "smo-nonrt" }]) {
      expect(parseView(new URLSearchParams(serializeView(v)))).toEqual(v);
    }
    expect(serializeView(DEFAULT_VIEW)).toBe("");
    expect(serializeView({ level: 2, lls: "c4", focus: "o-ru" })).toBe("?level=2&lls=c4&focus=o-ru");
  });
  it("ignores unknown, dimmed or wrong-level focus values and bad levels", () => {
    expect(parseView(new URLSearchParams("focus=nope")).focus).toBeNull();
    expect(parseView(new URLSearchParams("focus=o-cu")).focus).toBeNull();
    expect(parseView(new URLSearchParams("level=1&focus=lls-c3")).focus).toBeNull();
    expect(parseView(new URLSearchParams("level=9")).level).toBe(1);
    expect(parseView(new URLSearchParams("level=2&lls=zz")).lls).toBe("c3");
  });
  it("selecting a tier-1 part at level 1 goes to level 2; tier 2/3 stay; dimmed does nothing", () => {
    expect(select(DEFAULT_VIEW, "gm-a")).toEqual({ level: 2, lls: "c3", focus: "gm-a" });
    expect(select(DEFAULT_VIEW, "o-du")).toEqual({ level: 2, lls: "c3", focus: "o-du" });
    expect(select(DEFAULT_VIEW, "smo-nonrt")).toEqual({ level: 1, lls: "c3", focus: "smo-nonrt" });
    expect(select(DEFAULT_VIEW, "ue").level).toBe(1);
    expect(select(DEFAULT_VIEW, "o-cu")).toEqual(DEFAULT_VIEW);
  });
  it("Esc / Back clears the focus first, then goes up a level, then stops", () => {
    let v: ViewState = { level: 2, lls: "c3", focus: "bc" };
    v = up(v);
    expect(v).toEqual({ level: 2, lls: "c3", focus: null });
    v = up(v);
    expect(v.level).toBe(1);
    expect(up(v)).toEqual(v);
  });
  it("breadcrumb names every step", () => {
    expect(breadcrumb({ level: 2, lls: "c3", focus: "bc" }).map((c) => c.label)).toEqual(["Whole O-RAN", "Open Fronthaul (LLS-C3)", "Boundary clock (T-BC)"]);
  });
});

describe("quality auto-reduction heuristics", () => {
  it("weak devices start lower", () => {
    expect(initialQuality({ cores: 8, memory: 8, width: 1920, reducedMotion: false })).toBe("high");
    expect(initialQuality({ cores: 4, memory: undefined, width: 1920, reducedMotion: false })).toBe("medium");
    expect(initialQuality({ cores: 8, memory: 8, width: 390, reducedMotion: false })).toBe("medium");
    expect(initialQuality({ cores: 2, memory: 8, width: 1920, reducedMotion: false })).toBe("low");
    expect(initialQuality({ cores: 16, memory: 16, width: 1920, reducedMotion: true })).toBe("low");
  });
});
