import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import path from "node:path";
import { DEFAULT_STATE, parseState, select, serializeState, up, type SimState } from "@/lib/sim/state";
import { keyEvents, nextEventTime, prevEventTime, stagesAt, stagesInRun } from "@/lib/sim/events";
import {
  APP_BLOB, REPO_BLOB, referenceUrl, architecture, contentStats, getElement, hiddenSentenceCount, isClickable, isRenderable, renderableSentences, validateArchitecture,
  type Sentence,
} from "@/lib/architecture";
import type { ReplayRun } from "@/lib/replay";

/* eslint-disable @typescript-eslint/no-explicit-any */
const runs: any[] = JSON.parse(gunzipSync(readFileSync(path.join(__dirname, "../../data/derived/recovery_runs.json.gz"))).toString("utf8"));
const run = (id: string) => {
  const r = runs.find((x) => x.id === id);
  return { ...r, scenarioId: r.scenario, events: r.events.map((e: any) => ({ source: "loop", node: null, verdict: null, hint: null, action: null, target: null, ok: null, detail: null, ...e })) } as ReplayRun;
};

describe("simulator URL state", () => {
  it("default state serialises to the bare home URL", () => {
    expect(serializeState(DEFAULT_STATE)).toBe("/");
  });
  it("every field round-trips through the URL", () => {
    const s = { ...DEFAULT_STATE, level: 3 as const, lls: "c2" as const, focus: "bc", scenario: "A8_rogue_bc", rep: 16, arm: "control" as const, t: 2.1, results: true, pkt: "bmca" as const, panel: "lesson:ptp" };
    const url = serializeState(s);
    expect(parseState(new URLSearchParams(url.slice(2)))).toEqual(s);
  });
  it("rejects malformed values and clamps time", () => {
    const s = parseState(new URLSearchParams("level=9&rep=3&arm=x&t=999&focus=<script>&lls=c9&panel=evil"));
    expect(s.panel).toBeNull();
    expect(s.level).toBe(1);
    expect(s.rep).toBe(13);
    expect(s.arm).toBe("side");
    expect(s.t).toBe(41);
    expect(s.focus).toBeNull();
    expect(s.lls).toBe("c3");
  });
  it("Esc closes results, then the panel, then goes up a level clearing the selection, and stops at level 1", () => {
    let s: SimState = { ...DEFAULT_STATE, level: 4, focus: "loop-act", results: true, panel: "sandbox" };
    s = up(s); expect(s.results).toBe(false); expect(s.level).toBe(4);
    s = up(s); expect(s.panel).toBeNull();
    s = up(s); expect(s.level).toBe(3); expect(s.focus).toBeNull();
    s = up(up(s)); expect(s.level).toBe(1);
    expect(up(s)).toEqual(s);
    expect(up({ ...s, focus: "bc" }).focus).toBeNull();
  });
  it("selecting the S-plane zooms to level 2, the BC to level 3, the SMO to level 4", () => {
    expect(select(DEFAULT_STATE, "fh-splane").level).toBe(2);
    expect(select(DEFAULT_STATE, "bc").level).toBe(3);
    expect(select(DEFAULT_STATE, "smo-nonrt").level).toBe(4);
    expect(select(DEFAULT_STATE, "lls-c1").lls).toBe("c1");
    expect(select({ ...DEFAULT_STATE, level: 3 }, "fh-splane").level).toBe(3); // never zooms out on select
  });
});

describe("event sequencing from recorded loop.jsonl", () => {
  const a1 = run("A1_rogue_master__r13__loop");
  const ev = keyEvents(a1);
  it("A1 r13 loop: detect 1.068, localise 1.068, decide/act 2.081, verify 3.210 (recorded values)", () => {
    const st = stagesAt(ev, 41);
    expect(st.detect?.t).toBe(1.068);
    expect(st.localise?.t).toBe(1.068);
    expect(st.localise?.label).toContain("p-rogue");
    expect(st.decide?.t).toBe(2.081);
    expect(st.act?.t).toBe(2.081);
    expect(st.verify?.t).toBe(3.21);
    expect(st.rollback).toBeNull();
  });
  it("events are sorted and decide precedes act at the same timestamp", () => {
    for (let i = 1; i < ev.length; i++) expect(ev[i].t).toBeGreaterThanOrEqual(ev[i - 1].t);
    const iDecide = ev.findIndex((e) => e.kind === "decide");
    expect(ev[iDecide + 1].kind).toBe("act");
  });
  it("stages light only once their recorded time has passed", () => {
    expect(stagesAt(ev, 1.0).detect).toBeNull();
    expect(stagesAt(ev, 1.068).detect).not.toBeNull();
    expect(stagesAt(ev, 2.0).act).toBeNull();
  });
  it("next/prev step event to event and stop at the ends", () => {
    expect(nextEventTime(ev, -3)).toBe(0);
    expect(nextEventTime(ev, 0)).toBe(1.068);
    expect(prevEventTime(ev, 1.068)).toBe(0);
    expect(prevEventTime(ev, -3)).toBeNull();
    expect(nextEventTime(ev, 41)).toBeNull();
    // stepping visits every distinct time exactly once
    const seen: number[] = [];
    for (let t: number | null = nextEventTime(ev, -20); t !== null; t = nextEventTime(ev, t)) seen.push(t);
    expect(seen).toEqual([...new Set(ev.map((e) => e.t))]);
  });
  it("control arm never reaches act: would_act counts as decide only", () => {
    const c = keyEvents(run("A1_rogue_master__r13__control"));
    const inRun = stagesInRun(c);
    expect(inRun.has("decide")).toBe(true);
    expect(inRun.has("act")).toBe(false);
    expect(inRun.has("verify")).toBe(false);
  });
  it("no recorded run reaches rollback (EVALUATION_RL.json: 0 rollbacks)", () => {
    const n = runs.filter((r) => stagesInRun(keyEvents(run(r.id))).has("rollback")).length;
    expect(n).toBe(0);
  });
  it("act count across all 140 runs equals the 41 recorded act records", () => {
    expect(runs.length).toBe(140);
    const acts = runs.reduce((a, r) => a + keyEvents(run(r.id)).filter((e) => e.kind === "act").length, 0);
    expect(acts).toBe(41);
  });
});

describe("architecture content: citation hiding", () => {
  it("content file is structurally valid", () => {
    expect(validateArchitecture()).toEqual([]);
  });
  it("SOURCE_NEEDED and incomplete citations are hidden", () => {
    const base: Sentence = { id: "x", kind: "REFERENCE", text: "t", citation: { source: "s", source_id: "S", clause: "c", locator: "l", url_or_repo_path: "p", status: "UNVERIFIED" } };
    expect(isRenderable(base)).toBe(true);
    expect(isRenderable({ ...base, citation: { ...base.citation, status: "SOURCE_NEEDED" } })).toBe(false);
    expect(isRenderable({ ...base, citation: { ...base.citation, clause: null } })).toBe(false);
    expect(isRenderable({ ...base, citation: { ...base.citation, url_or_repo_path: null } })).toBe(false);
    expect(isRenderable({ ...base, text: "  " })).toBe(false);
  });
  it("counts: rendered + hidden = all, and every SOURCE_NEEDED sentence is hidden", () => {
    const s = contentStats();
    expect(s.rendered + s.hidden).toBe(s.sentences);
    expect(s.hidden).toBeGreaterThanOrEqual(s.sourceNeeded);
    // VERIFIED only with an independent auditor's verbatim quote and location
    for (const el of architecture.elements) for (const x of el.sentences) if (x.citation.status === "VERIFIED") {
      expect(x.verification?.quote?.length, x.id).toBeGreaterThan(0);
      expect(x.verification?.where?.length, x.id).toBeGreaterThan(0);
    }
    for (const el of architecture.elements) {
      expect(renderableSentences(el).every((x) => x.citation.status !== "SOURCE_NEEDED")).toBe(true);
      expect(hiddenSentenceCount(el)).toBe(el.sentences.filter((x) => x.citation.status === "SOURCE_NEEDED").length);
    }
  });
  it("records valid primary-source outcomes and resolves the four formerly hidden claims", () => {
    const all = architecture.elements.flatMap((e) => e.sentences);
    const primary = all.filter((x) => x.citation.primary);
    expect(primary.filter((x) => x.citation.primary?.result === "CONFIRMED")).toHaveLength(31);
    expect(primary.filter((x) => x.citation.primary?.result === "NOT_ACCESSIBLE")).toHaveLength(4);
    expect(primary.filter((x) => x.citation.primary?.result === "CONFLICTS")).toHaveLength(0);
    for (const x of primary.filter((s) => s.citation.primary?.result === "CONFIRMED")) {
      expect(x.citation.primary?.checked, x.id).toBe(true);
      expect(x.citation.primary?.quote?.length, x.id).toBeGreaterThan(0);
    }
    for (const id of ["o-du.s5", "fh-mplane.s4", "fh-cplane.s3", "fh-uplane.s3"]) {
      const sentence = all.find((x) => x.id === id)!;
      expect(sentence.citation.status).toBe("VERIFIED");
      expect(sentence.citation.primary?.result).toBe("CONFIRMED");
      expect(isRenderable(sentence)).toBe(true);
    }
    expect(contentStats().sourceNeeded).toBe(0);
    expect(contentStats().hidden).toBe(0);
    expect(contentStats().primaryConfirmed).toBe(31);
    expect(contentStats().primaryConflicts).toBe(0);
    expect(contentStats().primaryNotAccessible).toBe(4);
  });
  it("dimmed elements are not clickable and are marked outside the project", () => {
    const dimmed = architecture.elements.filter((e) => e.tier === "dimmed");
    expect(dimmed.map((e) => e.id).sort()).toEqual(["core-5g", "near-rt-ric", "o-cloud", "o-cu"]);
    for (const e of dimmed) {
      expect(isClickable(e)).toBe(false);
      expect(e.outside_project).toBe(true);
    }
    expect(isClickable(getElement("bc")!)).toBe(true);
  });
  it("only LLS-C3 is marked as the testbed configuration", () => {
    expect(architecture.elements.filter((e) => e.lls?.testbed).map((e) => e.id)).toEqual(["lls-c3"]);
  });
});

describe("architecture content: audit fixes (2026-10-06)", () => {
  const root = path.join(__dirname, "../../..");
  it("every cited repository path exists in this checkout", () => {
    const missing = architecture.elements.flatMap((e) => e.sentences)
      .map((x) => x.citation.url_or_repo_path)
      .filter((p): p is string => !!p && !/^https?:/.test(p))
      .filter((p) => !existsSync(path.join(root, p)));
    expect(missing).toEqual([]);
  });
  it("app-code citations link to the webapp-sim branch, project files to the snapshot branch", () => {
    const c = { source: "s", source_id: "S", clause: "c", locator: "l", status: "UNVERIFIED" as const };
    expect(referenceUrl({ ...c, url_or_repo_path: "04_WEB_SIMULATOR/ingest/extract.py" })).toBe(APP_BLOB + "04_WEB_SIMULATOR/ingest/extract.py");
    expect(referenceUrl({ ...c, url_or_repo_path: "03_RECOVERY_LOOP_S-PLANE/PREREGISTRATION.md" })).toBe(REPO_BLOB + "03_RECOVERY_LOOP_S-PLANE/PREREGISTRATION.md");
  });
  it("labels do not overclaim: no PRTC on GM-A, PTP-only S-plane, O-RU proxies, LLS-C3 as closest match", () => {
    expect(getElement("gm-a")!.name).not.toMatch(/PRTC/);
    expect(getElement("fh-splane")!.name).not.toMatch(/SyncE/);
    expect(getElement("o-ru")!.name).toMatch(/proxies/);
    expect(getElement("lls-c3")!.name).toMatch(/closest match/);
  });
  it("the A1 rogue is not placed in RU3's namespace by any rendered sentence", () => {
    const bad = architecture.elements.flatMap((e) => renderableSentences(e)).filter((x) => /A1[^.;]*RU3's namespace|RU3's namespace[^.;]*A1\b/.test(x.text));
    expect(bad.map((x) => x.id)).toEqual([]);
  });
  it("tier 1 elements on the level-1 diagram are only those the testbed built", () => {
    const t1 = architecture.elements.filter((e) => e.tier === 1 && e.levels.includes(1) && !e.id.startsWith("ds-")).map((e) => e.id).sort();
    expect(t1).toEqual(["bc", "fh-splane", "gm-a", "gm-b", "injector", "o-ru"]);
  });
});
