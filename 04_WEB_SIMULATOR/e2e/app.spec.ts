import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { LESSONS } from "../src/lib/lessons";

function collectErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

// Phase 1: "/" is now the 3D explorer (see e2e/explorer.spec.ts); the previous 2D home page lives at /overview.
test("2D overview (previous home) loads with live hypothesis verdicts and headline numbers", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("/overview", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Timing security");
  await expect(page.getByText("H3 FAIL")).toBeVisible();
  for (const t of ["A1 · Rogue grandmaster", "C1 · Interception", "C3 · Whole-second"]) await expect(page.getByText(t)).toBeVisible();
  await expect(page.getByLabel(/Rogue grandmaster: control 38.5 s, loop 2.0 s/)).toBeVisible();
  expect(errors).toEqual([]);
});

test("a lesson can be completed and progress is stored in the database", async ({ page }) => {
  const errors = collectErrors(page);
  const lesson = LESSONS.find((l) => l.id === "oran-splane")!;
  await page.goto("/learn/oran-splane", { waitUntil: "networkidle" });
  // step 1: four planes
  for (const k of ["C", "U", "S", "M"]) await page.getByTestId(`reveal-${k}`).click();
  await page.getByTestId("step-continue").click();
  // step 2: timing budget
  await page.getByLabel(/Time error/).fill("200");
  await page.getByTestId("step-continue").click();
  // step 3: topology tour
  for (const d of ["gma", "gmb", "bc", "bcs", "ru1", "ru2", "ru3"]) await page.getByTestId(`tour-${d}`).click();
  await page.getByTestId("step-continue").click();
  // 3-question check with instant feedback
  for (const q of lesson.quiz) {
    await page.getByTestId(`quiz-option-${q.answer}`).click();
    await expect(page.getByText("Correct.")).toBeVisible();
    await expect(page.getByText(q.citation, { exact: false })).toBeVisible();
    await page.getByTestId("quiz-next").click();
  }
  await expect(page.getByTestId("quiz-score")).toHaveText("3/3 correct");
  await expect(page.getByTestId("lesson-complete")).toContainText("Lesson 1 complete");
  const prog = await (await page.request.get("/api/progress")).json();
  const p = prog.progress.find((x: { lessonId: string }) => x.lessonId === "oran-splane");
  expect(p.completed).toBe(true);
  expect(p.quizBest).toBe(3);
  expect(prog.stats.isGuest).toBe(true);
  expect(prog.stats.xp).toBe(3 * 10 + 3 * 5 + 20);
  await page.goto("/learn", { waitUntil: "networkidle" });
  await expect(page.getByTestId("path-completed")).toHaveText("1/7");
  expect(errors).toEqual([]);
});

test("replay of A1 control vs loop plays to the end and shows the isolation at the recorded time", async ({ page, request }) => {
  const errors = collectErrors(page);
  const loop = await (await request.get("/api/runs/A1_rogue_master__r13__loop")).json();
  const act = loop.events.find((e: { kind: string }) => e.kind === "act");
  expect(act.action).toBe("ISOLATE_PTP_AT_PORT");
  expect(act.target).toBe("p-rogue");
  await page.goto("/replay?scenario=A1_rogue_master&rep=13", { waitUntil: "networkidle" });
  await expect(page.getByTestId("rp-arm-loop").locator("svg").first()).toBeVisible();
  await page.getByTestId("rp-speed-4").click();
  await page.getByTestId("rp-play").click();
  await expect(page.getByTestId("rp-ended")).toBeVisible({ timeout: 60_000 });
  await expect(page.getByTestId("rp-time")).toHaveText("T0 + 41.0 s");
  // loop arm: the executed isolation is logged at exactly the recorded time
  const actItem = page.getByTestId("rp-log-loop").locator('li[data-kind="act"]');
  await expect(actItem).toHaveCount(1);
  await expect(actItem).toHaveAttribute("data-t", act.t.toFixed(3));
  await expect(actItem).toContainText("Isolate PTP at port p-rogue");
  await expect(page.getByTestId("rp-log-loop").locator('li[data-kind="verify"]')).toContainText("VERIFY passed");
  // control arm: same decision only logged as would_act, never executed
  await expect(page.getByTestId("rp-log-control").locator('li[data-kind="act"]')).toHaveCount(0);
  await expect(page.getByTestId("rp-log-control").locator('li[data-kind="would_act"]')).toContainText("p-rogue");
  // recorded totals
  await expect(page.getByTestId("rp-arm-control")).toContainText("38.51 s · not restored");
  await expect(page.getByTestId("rp-arm-loop")).toContainText("2.00 s · restored");
  // the port turns isolated exactly at the act time
  const caption = page.getByTestId("rp-arm-loop").locator("figcaption");
  await page.getByTestId("rp-scrubber").fill(String(Math.floor((act.t - 0.15) * 10) / 10));
  await expect(caption).not.toContainText("Isolated: p-rogue");
  await page.getByTestId("rp-scrubber").fill(String(Math.ceil((act.t + 0.05) * 10) / 10));
  await expect(caption).toContainText("Isolated: p-rogue");
  expect(errors).toEqual([]);
});

test("dashboard numbers match the database and RESULTS_2026-10-05.md", async ({ page, request }) => {
  const errors = collectErrors(page);
  const api = await (await request.get("/api/aggregates")).json();
  await page.goto("/dashboard", { waitUntil: "networkidle" });
  for (const a of api.aggregates as { scenarioId: string; arm: string; unhealthyMedian: number; disruptiveExecuted: number }[]) {
    await expect(page.getByTestId(`agg-${a.scenarioId}-${a.arm}-median`)).toHaveText(`${a.unhealthyMedian.toFixed(2)} s`);
    if (a.arm === "loop") await expect(page.getByTestId(`agg-${a.scenarioId}-loop-actions`)).toContainText(String(a.disruptiveExecuted));
  }
  // the headline as written in RESULTS_2026-10-05.md (one decimal)
  const one = async (id: string) => Number((await page.getByTestId(id).textContent())!.replace(" s", "")).toFixed(1);
  expect(await one("agg-A1_rogue_master-control-median")).toBe("38.5");
  expect(await one("agg-A1_rogue_master-loop-median")).toBe("2.0");
  expect(await one("agg-C1_removal-control-median")).toBe("39.0");
  expect(await one("agg-C1_removal-loop-median")).toBe("2.5");
  expect(await one("agg-C3_wholesecond-control-median")).toBe("38.5");
  expect(await one("agg-C3_wholesecond-loop-median")).toBe("2.0");
  await expect(page.getByTestId("hyp-H3-verdict")).toHaveText("FAILED");
  await expect(page.getByTestId("hyp-H3-summary")).toContainText("1 disruptive action in 25 benign loop runs");
  for (const h of ["H1", "H2", "H4", "CI"]) await expect(page.getByTestId(`hyp-${h}-verdict`)).toHaveText("PASS");
  await expect(page.getByTestId("camp-v3-sens")).toHaveText("95/96 = 0.990");
  await expect(page.getByTestId("limits-panel")).toContainText("free_running 1");
  expect(errors).toEqual([]);
});

test("sandbox is labelled as a model and reproduces the logged decisions", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("/sandbox", { waitUntil: "networkidle" });
  await expect(page.getByTestId("sandbox-model-banner")).toContainText("MODEL — not measured data");
  await expect(page.getByTestId("sb-calibration")).toContainText("70/70");
  await expect(page.getByTestId("sb-model-unhealthy")).toHaveText("2.5 s"); // C1 r13 at the pre-registered parameters
  await page.getByTestId("sb-loss").fill("20");
  await expect(page.getByTestId("sb-model-unhealthy")).not.toHaveText("2.5 s");
  expect(errors).toEqual([]);
});

test("fault catalogue filters by text and class", async ({ page }) => {
  await page.goto("/catalogue", { waitUntil: "networkidle" });
  await expect(page.getByTestId("cat-count")).toHaveText("22 of 22 faults");
  await page.getByTestId("cat-search").fill("GNSS");
  await expect(page.getByText("GNSS spoofing (coherent)")).toBeVisible();
  await page.getByRole("button", { name: "BENIGN", exact: true }).click();
  await expect(page.getByText("GNSS spoofing (coherent)")).toHaveCount(0);
  await expect(page.getByText("GNSS holdover (honest outage)")).toBeVisible();
});

test("live mode explains why it is disabled when no service is configured", async ({ page }) => {
  await page.goto("/live", { waitUntil: "networkidle" });
  await expect(page.getByTestId("live-disabled")).toBeVisible();
});

const PAGES = ["/", "/overview", "/learn", "/learn/oran-splane", "/learn/ptp", "/learn/bmca", "/learn/attack-vs-benign", "/learn/attacks", "/learn/benign", "/learn/loop-limits", "/replay", "/sandbox", "/dashboard", "/catalogue", "/live", "/about", "/signin"];

test("no console errors on any page", async ({ page }) => {
  const errors = collectErrors(page);
  for (const p of PAGES) {
    await page.goto(p, { waitUntil: "networkidle" });
    await page.waitForTimeout(300);
  }
  expect(errors).toEqual([]);
});

test("responsive down to 390 px: no horizontal scrolling", async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  for (const p of ["/", "/overview", "/learn", "/learn/bmca", "/replay", "/sandbox", "/dashboard", "/catalogue", "/about"]) {
    await page.goto(p, { waitUntil: "networkidle" });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, p).toBeLessThanOrEqual(1);
  }
  await ctx.close();
});

test("reduced motion: packets are not animated, state still updates", async ({ browser }) => {
  for (const reducedMotion of ["no-preference", "reduce"] as const) {
    const ctx = await browser.newContext({ reducedMotion });
    const page = await ctx.newPage();
    await page.goto("/replay?scenario=A1_rogue_master&rep=13", { waitUntil: "networkidle" });
    await page.getByTestId("rp-scrubber").fill("5");
    await page.getByTestId("rp-play").click();
    await page.waitForTimeout(700);
    const dots = await page.getByTestId("rp-arm-loop").locator("svg circle").count();
    if (reducedMotion === "reduce") expect(dots).toBe(0);
    else expect(dots).toBeGreaterThan(0);
    await page.getByTestId("rp-play").click();
    await expect(page.getByTestId("rp-arm-loop").locator("figcaption")).toContainText("Isolated: p-rogue");
    await ctx.close();
  }
});

test("keyboard: skip link and replay controls are reachable", async ({ page }) => {
  await page.goto("/replay", { waitUntil: "networkidle" });
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.getByTestId("rp-play").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("rp-play")).toHaveText("Pause");
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("rp-play")).toHaveText("Play");
});

test("accessibility: no serious or critical axe violations (WCAG 2.1 AA, incl. contrast)", async ({ page }) => {
  for (const p of ["/", "/overview", "/learn", "/learn/oran-splane", "/replay", "/sandbox", "/dashboard", "/catalogue", "/about"]) {
    await page.goto(p, { waitUntil: "networkidle" });
    const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const bad = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(bad.map((v) => `${p}: ${v.id} (${v.nodes.length}) ${v.nodes[0]?.target}`), p).toEqual([]);
  }
});
