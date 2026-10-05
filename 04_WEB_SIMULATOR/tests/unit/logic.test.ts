/** Pure-logic tests: health definition, replay state, sandbox model, BMCA widget, XP rules and lesson content. */
import "dotenv/config";
import { afterAll, describe, expect, it } from "vitest";
import { PrismaClient } from "@prisma/client";
import { isHealthy, legitParentsFor, pyRound } from "@/lib/metrics";
import { deviceOfIdentity, markers, stateAt, type ReplayRun } from "@/lib/replay";
import { PREREGISTERED, runModel, integrateUnhealthy } from "@/lib/sandboxModel";
import { buildSandboxData } from "@/lib/sandboxData";
import { bmcaBest, type ClockDS } from "@/components/lesson/BmcaArena";
import { nextStreak, xpFor } from "@/lib/xp";
import { LESSONS } from "@/lib/lessons";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { gunzipSync } from "node:zlib";

/** International (+CC ...), 10-digit Indian mobile, and (NNN) NNN-NNNN patterns. */
const PHONE = [/\+\d{1,3}[\s-]?\(?\d{2,5}\)?[\s-]?\d{3,5}[\s-]?\d{3,5}\b/, /(?<![\d.])[6-9]\d{9}(?![\d.])/, /\(\d{3}\)\s?\d{3}-\d{4}/];
function scanForPhoneNumbers(root: string): string[] {
  const hits: string[] = [];
  const walk = (d: string) => {
    for (const f of readdirSync(d)) {
      if (["node_modules", ".next", "test-results", "playwright-report", ".git"].includes(f)) continue;
      const p = path.join(d, f);
      const st = statSync(p);
      if (st.isDirectory()) walk(p);
      else if (/\.(tsx?|mjs|js|json|md|py|css|yml|txt|example)$|\.json\.gz$/.test(f) && st.size < 50e6) {
        let text = f.endsWith(".gz") ? gunzipSync(readFileSync(p)).toString("utf8") : readFileSync(p, "utf8");
        if (f === "package-lock.json") continue;
        text = text.replace(/\b\d{4}-\d{2}-\d{2}\b/g, "");
        for (const re of PHONE) {
          const m = text.match(re);
          if (m) hits.push(`${path.relative(root, p)}: ${m[0]}`);
        }
      }
    }
  };
  walk(root);
  return hits;
}

const prisma = new PrismaClient();
afterAll(async () => prisma.$disconnect());

describe("health definition (PREREGISTRATION.md s4)", () => {
  const legit = legitParentsFor(null);
  it("SLAVE or UNCALIBRATED, provisioned parent, allow-listed GM", () => {
    expect(isHealthy({ portState: "UNCALIBRATED", parent: "020000fffe000001", gm: "020000fffe00000a" }, legit)).toBe(true);
    expect(isHealthy({ portState: "SLAVE", parent: "020000fffe0000c5", gm: "020000fffe00000b" }, legit)).toBe(true);
  });
  it("rejects a rogue parent, a foreign GM, LISTENING, and a replacement BC outside B_bc_replacement", () => {
    expect(isHealthy({ portState: "UNCALIBRATED", parent: "020000fffe000062", gm: "020000fffe000062" }, legit)).toBe(false);
    expect(isHealthy({ portState: "UNCALIBRATED", parent: "020000fffe000001", gm: "020000fffe000042" }, legit)).toBe(false);
    expect(isHealthy({ portState: "LISTENING", parent: "020000fffe000001", gm: "020000fffe00000a" }, legit)).toBe(false);
    expect(isHealthy({ portState: "SLAVE", parent: "020000fffe0000b1", gm: "020000fffe00000a" }, legit)).toBe(false);
    expect(isHealthy({ portState: "SLAVE", parent: "020000fffe0000b1", gm: "020000fffe00000a" }, legitParentsFor("020000fffe0000b1"))).toBe(true);
  });
  it("pyRound matches Python round(): half-even on exact binary ties, nearest otherwise", () => {
    expect(pyRound(2.125, 2)).toBe(2.12); // Python: round(2.125, 2) == 2.12
    expect(pyRound(2.375, 2)).toBe(2.38); // Python: 2.38
    expect(pyRound(3415.539 - 3413.414, 2)).toBe(2.12); // Python: 2.12 (the difference is exactly 2.125 in binary)
    expect(pyRound(2.1250000000000004, 2)).toBe(2.13); // just above the tie
    expect(pyRound(0.5, 0)).toBe(0);
    expect(pyRound(1.5, 0)).toBe(2);
    expect(pyRound(2.675, 2)).toBe(2.67); // binary value is just below 2.675
    expect(pyRound(-2.125, 2)).toBe(-2.12);
  });
});

async function loadRun(id: string): Promise<ReplayRun> {
  const r = await prisma.run.findUniqueOrThrow({
    where: { id },
    include: { samples: { orderBy: [{ round: "asc" }, { id: "asc" }] }, events: { orderBy: [{ t: "asc" }, { id: "asc" }] }, packets: true },
  });
  return { ...r, arm: r.arm as "control" | "loop", params: r.params as Record<string, unknown>, events: r.events.map((e) => ({ ...e, detail: e.detail as Record<string, unknown> | null })), packets: (r.packets?.bins ?? []) as ReplayRun["packets"] };
}

describe("replay state is a lookup into the recorded run", () => {
  it("A1 r13 loop: p-rogue isolated exactly from the logged act time, RUs back on the BC afterwards", async () => {
    const run = await loadRun("A1_rogue_master__r13__loop");
    const act = run.events.find((e) => e.kind === "act")!;
    expect(act.target).toBe("p-rogue");
    expect(stateAt(run, act.t - 0.01).isolatedPorts).toEqual([]);
    expect(stateAt(run, act.t).isolatedPorts).toEqual(["p-rogue"]);
    const late = stateAt(run, 30);
    expect(late.nodes.ru1.parentDevice).toBe("bc");
    expect(late.nodes.ru1.healthy).toBe(true);
    expect(markers(run).some((m) => m.kind === "act" && m.t === act.t)).toBe(true);
  });
  it("A1 r13 control: RUs follow the rogue, isolation only logged as would_act", async () => {
    const run = await loadRun("A1_rogue_master__r13__control");
    const s = stateAt(run, 20);
    expect(s.nodes.ru1.parentDevice).toBe("rogue");
    expect(s.isolatedPorts).toEqual([]);
    expect(s.wouldIsolate).toEqual(["p-rogue"]);
    expect(s.unhealthySoFar).toBeGreaterThan(15);
  });
  it("C3 forger maps to the injector; GM-A elsewhere maps to GM-A", () => {
    expect(deviceOfIdentity("020000fffe00000a", "ru1", "C3_wholesecond", {})).toBe("injector");
    expect(deviceOfIdentity("020000fffe00000a", "ru1", "B2_gm_failover", {})).toBe("gma");
    expect(deviceOfIdentity("020000fffe00000c", "ru1", "B7_topology_change", {})).toBe("self");
  });
});

describe("sandbox model (labelled MODEL in the UI)", () => {
  it("reproduces the loop's logged decisions in all 70 control runs at the pre-registered parameters", async () => {
    const d = await buildSandboxData();
    expect(d.cases).toHaveLength(70);
    let match = 0;
    for (const c of d.cases) {
      const r = runModel(c, PREREGISTERED, d.latency);
      const rec = c.controlWouldAct;
      if (r.actions.length === rec.length && r.actions.every((a, i) => a.action === rec[i].action && Math.abs(a.t - rec[i].t) < 0.05)) match++;
    }
    expect(match).toBe(70);
  });
  it("benign harm count at pre-registered parameters equals the measured H3 count (1/25), and grows when the threshold drops", async () => {
    const d = await buildSandboxData();
    const benign = d.cases.filter((c) => c.cls === "benign" || c.cls === "healthy");
    expect(benign).toHaveLength(25);
    const harm = (p: typeof PREREGISTERED) => benign.filter((c) => runModel(c, p, d.latency).disruptive > 0).length;
    expect(harm(PREREGISTERED)).toBe(1);
    expect(harm({ ...PREREGISTERED, serviceLossS: 0.5, serviceLossMaintS: 0.5 })).toBeGreaterThanOrEqual(1);
    expect(harm({ ...PREREGISTERED, serviceLossS: 20 })).toBe(0);
  });
  it("with a 20 s service-loss threshold the model leaves C1 almost as bad as no action", async () => {
    const d = await buildSandboxData();
    const c1 = d.cases.filter((c) => c.scenarioId === "C1_removal");
    for (const c of c1) {
      const r = runModel(c, { ...PREREGISTERED, serviceLossS: 20 }, d.latency);
      expect(r.predictedUnhealthyS).toBeGreaterThan(19);
    }
  });
  it("integrateUnhealthy", () => {
    expect(integrateUnhealthy([[0, false], [1, false], [2, true], [3, true]], 10)).toBe(2);
    expect(integrateUnhealthy([[0, false], [1, false], [2, true]], 0.5)).toBe(0.5);
  });
});

describe("BMCA widget comparison", () => {
  const base: ClockDS = { key: "a", name: "A", priority1: 128, clockClass: 248, clockAccuracy: 254, variance: 65535, priority2: 128, identity: "020000fffe00000a" };
  it("clockClass 6 beats 248 before priority2 is consulted", () => {
    const rogue = { ...base, key: "r", clockClass: 6, priority2: 200, identity: "020000fffe000042" };
    expect(bmcaBest([base, rogue])).toMatchObject({ winner: { key: "r" }, field: "clockClass" });
  });
  it("identity is the final tie-breaker", () => {
    const b = { ...base, key: "b", identity: "020000fffe00000b" };
    expect(bmcaBest([b, base])).toMatchObject({ winner: { key: "a" }, field: "clockIdentity" });
  });
});

describe("XP and streak", () => {
  it("streak continues on consecutive UTC days and resets after a gap", () => {
    const now = new Date("2026-10-05T10:00:00Z");
    expect(nextStreak("2026-10-04", 3, now)).toBe(4);
    expect(nextStreak("2026-10-05", 3, now)).toBe(3);
    expect(nextStreak("2026-10-01", 9, now)).toBe(1);
    expect(nextStreak(null, 0, now)).toBe(1);
  });
  it("xp", () => {
    expect(xpFor({ newSteps: 1, quizImprovement: 0, lessonCompletedNow: false })).toBe(10);
    expect(xpFor({ newSteps: 0, quizImprovement: 3, lessonCompletedNow: true })).toBe(35);
    expect(xpFor({ newSteps: 0, quizImprovement: -1, lessonCompletedNow: false })).toBe(0);
  });
});

describe("lesson content", () => {
  it("7 lessons, each with 2-4 steps and a 3-question check with valid answers", () => {
    expect(LESSONS).toHaveLength(7);
    for (const l of LESSONS) {
      expect(l.steps.length).toBeGreaterThanOrEqual(2);
      expect(l.steps.length).toBeLessThanOrEqual(4);
      expect(l.quiz).toHaveLength(3);
      for (const q of l.quiz) {
        expect(q.answer).toBeGreaterThanOrEqual(0);
        expect(q.answer).toBeLessThan(q.options.length);
        expect(q.citation.length).toBeGreaterThan(5);
      }
      expect(new Set(l.steps.map((s) => s.id)).size).toBe(l.steps.length);
    }
  });
  it("lesson 5 covers all eight attacks with replays", () => {
    const sc = LESSONS.find((l) => l.id === "attacks")!.steps.flatMap((s) => (s.widget.type === "replay" ? s.widget.scenarios : []));
    expect(sc.sort()).toEqual(["A1_rogue_master", "A2_sync_spoof", "A3_replay", "A5_dos_flood", "A8_rogue_bc", "C1_removal", "C2_malformed", "C3_wholesecond"]);
  });
  it("no phone numbers anywhere in 04_WEB_SIMULATOR sources, docs or data", () => {
    const hits = scanForPhoneNumbers(path.resolve(__dirname, "..", ".."));
    expect(hits).toEqual([]);
  });
});
