import { expect, test, type Page } from "@playwright/test";

function collectErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}
const sim = (p: Page) => p.getByTestId("simulator");

test("home renders the O-RAN diagram with tiered elements", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(sim(page)).toHaveAttribute("data-level", "1");
  for (const id of ["gm-a", "gm-b", "bc", "o-ru", "fh-splane", "injector"]) await expect(page.getByTestId(`node-${id}`)).toHaveAttribute("data-tier", "1");
  for (const id of ["o-du", "fh-mplane", "smo-nonrt", "gnss-time", "synce"]) await expect(page.getByTestId(`node-${id}`)).toHaveAttribute("data-tier", "2");
  await expect(page.getByTestId("node-smo-nonrt")).toContainText("not implemented there");
  await expect(page.getByTestId("node-o-ru")).toContainText("RU3");
  await expect(page.getByTestId("node-gm-a")).not.toContainText("PRTC");
  await expect(page.getByTestId("node-fh-splane")).not.toContainText("SyncE");
  await expect(page.getByTestId("content-counts")).toContainText("VERIFIED by an independent audit");
  expect(errors).toEqual([]);
});

test("dimmed elements are not clickable but show a tooltip", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  for (const id of ["near-rt-ric", "o-cu", "core-5g", "o-cloud"]) await expect(page.getByTestId(`node-${id}`)).toHaveAttribute("data-clickable", "false");
  await page.getByTestId("node-o-cu").hover();
  await expect(page.getByTestId("sim-tooltip")).toContainText("Outside this project");
  await expect(page.getByTestId("sim-tooltip")).toContainText("O-CU");
  await page.getByTestId("node-o-cu").click({ force: true });
  await expect(sim(page)).toHaveAttribute("data-level", "1");
  await expect(page.getByTestId("side-intro")).toBeVisible();
  await expect(page).toHaveURL(/\/$/);
});

test("clicking a tier-1 element zooms in; Esc returns", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("/", { waitUntil: "networkidle" });
  await page.getByTestId("node-fh-splane").click();
  await expect(sim(page)).toHaveAttribute("data-level", "2");
  await expect(page.getByTestId("sim-diagram")).toHaveAttribute("data-zoom", "l2");
  await expect(page.getByTestId("crumb-2")).toHaveAttribute("aria-current", "location");
  await expect(page.getByTestId("side-title")).toHaveText("Open Fronthaul S-plane (PTP in the testbed)");
  await expect(page).toHaveURL(/level=2/);
  await expect(page.getByTestId("lls-overlay")).toHaveAttribute("data-testbed", "true");
  await expect(page.getByTestId("lls-c3")).toHaveText("LLS-C3 · closest match (reference doc says C2/C3)");
  await expect(page.getByTestId("lls-overlay")).toContainText("closest match to the testbed");
  await page.getByTestId("lls-c1").click();
  await expect(page.getByTestId("lls-overlay")).toHaveAttribute("data-testbed", "false");
  await expect(page.getByTestId("side-title")).toHaveText("LLS-C1");
  await page.keyboard.press("Escape"); // up a level
  await expect(sim(page)).toHaveAttribute("data-level", "1");
  await expect(page.getByTestId("side-intro")).toBeVisible();
  await expect(page.getByTestId("sim-diagram")).toHaveAttribute("data-zoom", "l1");
  expect(errors).toEqual([]);
});

test("zoom from the T-BC into the recorded testbed, then back with the Back button", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await page.getByTestId("node-bc").click();
  await expect(sim(page)).toHaveAttribute("data-level", "3");
  await expect(page.getByTestId("rp-arm-loop").locator("svg").first()).toBeVisible();
  await expect(page.getByTestId("pkt-inspector")).toBeVisible();
  await expect(page.getByTestId("hw-A6")).toContainText("requires hardware, not measured");
  await page.getByTestId("sim-back").click();
  await expect(sim(page)).toHaveAttribute("data-level", "2");
});

test("deep link restores the exact state", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("/?level=3&focus=bmca-contest&scenario=A8_rogue_bc&rep=15&arm=loop&t=2.1&pkt=bmca", { waitUntil: "networkidle" });
  await expect(sim(page)).toHaveAttribute("data-level", "3");
  await expect(page.getByTestId("rp-scenario")).toHaveValue("A8_rogue_bc");
  await expect(page.getByTestId("rp-rep")).toHaveValue("15");
  await expect(page.getByRole("button", { name: "Recovery loop", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("rp-arm-control")).toHaveCount(0);
  await expect(page.getByTestId("rp-time")).toHaveText("T0 + 2.1 s");
  await expect(page.getByTestId("side-title")).toHaveText("Announce and the BMCA contest");
  await expect(page.getByTestId("pkt-inspector")).toHaveAttribute("data-tab", "bmca");
  await expect(page.getByTestId("rp-arm-loop").locator("span.font-mono").first()).toHaveText("A8_rogue_bc__r15__loop");
  // the URL written back by the app is the same state
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("rp-time")).toHaveText("T0 + 2.1 s");
  await expect(page.getByTestId("pkt-inspector")).toHaveAttribute("data-tab", "bmca");
  expect(errors).toEqual([]);
});

test("replay steps event by event and lights the loop stages at the recorded times", async ({ page, request }) => {
  const errors = collectErrors(page);
  const run = await (await request.get("/api/runs/A1_rogue_master__r13__loop")).json();
  const act = run.events.find((e: { kind: string }) => e.kind === "act");
  const verify = run.events.find((e: { kind: string }) => e.kind === "verify");
  const detect = run.events.find((e: { kind: string; verdict: string; t: number }) => e.kind === "eval" && e.verdict === "ATTACK" && e.t >= 0);
  await page.goto("/?level=4&scenario=A1_rogue_master&rep=13&arm=loop", { waitUntil: "networkidle" });
  await expect(page.getByTestId("loop-stages")).toBeVisible();
  await expect(page.getByTestId("stage-detect")).toHaveAttribute("data-lit", "false");
  await expect(page.getByTestId("stage-rollback")).toHaveAttribute("data-never", "true");
  await page.locator("body").click({ position: { x: 5, y: 5 } });
  await page.keyboard.press("ArrowRight"); // onset
  await expect(page.getByTestId("rp-time")).toHaveText("T0 + 0.0 s");
  await page.keyboard.press("ArrowRight"); // first ATTACK verdict
  await expect(page.getByTestId("stage-detect")).toHaveAttribute("data-lit", "true");
  await expect(page.getByTestId("stage-detect")).toContainText(`T0 + ${detect.t.toFixed(3)} s`);
  await expect(page.getByTestId("stage-act")).toHaveAttribute("data-lit", "false");
  while ((await page.getByTestId("stage-act").getAttribute("data-lit")) !== "true") await page.getByTestId("rp-next-event").click();
  await expect(page.getByTestId("stage-act")).toContainText(`T0 + ${act.t.toFixed(3)} s`);
  await expect(page.getByTestId("stage-decide")).toContainText(`T0 + ${act.t.toFixed(3)} s`);
  await expect(page.getByTestId("stage-verify")).toHaveAttribute("data-lit", "false");
  // RU port-state changes recorded by ptp4l sit between act and verify; step through them
  while ((await page.getByTestId("stage-verify").getAttribute("data-lit")) !== "true") await page.getByTestId("rp-next-event").click();
  await expect(page.getByTestId("stage-verify")).toContainText(`T0 + ${verify.t.toFixed(3)} s`);
  await page.keyboard.press("ArrowLeft");
  await expect(page.getByTestId("stage-verify")).toHaveAttribute("data-lit", "false");
  await expect(page).toHaveURL(/level=4.*t=\d/);
  // control arm: the decision is logged but never executed
  await page.goto("/?level=4&scenario=A1_rogue_master&rep=13&arm=control&t=41", { waitUntil: "networkidle" });
  await expect(page.getByTestId("stage-decide")).toHaveAttribute("data-lit", "true");
  await expect(page.getByTestId("stage-act")).toHaveAttribute("data-never", "true");
  // 0.25x speed exists
  await expect(page.getByTestId("rp-speed-0.25")).toBeVisible();
  expect(errors).toEqual([]);
});

test("results overlay opens from anywhere with R and closes with Esc", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("/?level=2&focus=o-du", { waitUntil: "networkidle" });
  await page.keyboard.press("r");
  await expect(page.getByTestId("results-overlay")).toBeVisible();
  await expect(page.getByTestId("hyp-H3-verdict")).toHaveText("FAILED");
  await expect(page.getByTestId("camp-v3-attr")).toHaveText("84/96 = 0.875");
  await expect(page.getByTestId("camp-wilson")).toContainText("attribution 84/96");
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("results-overlay")).toHaveCount(0);
  await expect(sim(page)).toHaveAttribute("data-level", "2");
  await expect(page.getByTestId("side-title")).toHaveText("O-DU (distributed unit)");
  expect(errors).toEqual([]);
});

test("projector and large-text toggles", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  const html = page.locator("html");
  await expect(html).toHaveAttribute("data-theme", "dark");
  await page.keyboard.press("p");
  await expect(html).toHaveAttribute("data-theme", "projector");
  await page.keyboard.press("l");
  await expect(html).toHaveAttribute("data-text", "large");
  await page.reload({ waitUntil: "networkidle" });
  await expect(html).toHaveAttribute("data-theme", "projector");
  await page.getByTestId("toggle-projector").click();
  await page.getByTestId("toggle-large").click();
  await expect(html).toHaveAttribute("data-theme", "dark");
  await expect(html).toHaveAttribute("data-text", "normal");
});

test("datasets panel: counts, S15 label and absent raw files", async ({ page }) => {
  await page.goto("/?focus=ds-pilot&panel=datasets", { waitUntil: "networkidle" });
  await expect(page.getByTestId("ds-recovery-rows")).toHaveText("140");
  await expect(page.getByTestId("ds-campaign-rows")).toHaveText("168");
  await expect(page.getByTestId("ds-pilot-s15-status")).toHaveText("independent validation S15 not established");
  await expect(page.getByTestId("ds-row-b6-run1")).toContainText("data not in repo");
  await expect(page.getByTestId("ds-absent")).toContainText("laptopA_20261002-175858");
});

test("no console errors across simulator states", async ({ page }) => {
  const errors = collectErrors(page);
  for (const u of ["/", "/?level=2", "/?level=3", "/?level=3&pkt=counts&t=5", "/?level=3&pkt=attack&t=5", "/?level=3&pkt=exchange", "/?level=4", "/?results=1", "/?panel=lessons", "/?panel=sandbox", "/?panel=catalogue", "/?panel=datasets", "/?panel=lesson:bmca"]) {
    await page.goto(u, { waitUntil: "networkidle" });
    await page.waitForTimeout(200);
  }
  expect(errors).toEqual([]);
});

test("accessibility in the dark and projector themes (WCAG 2.1 AA, serious/critical)", async ({ page }) => {
  const { default: AxeBuilder } = await import("@axe-core/playwright");
  for (const theme of ["dark", "projector"]) {
    await page.goto("/", { waitUntil: "networkidle" });
    if (theme === "projector") await page.keyboard.press("p");
    for (const u of ["/", "/?level=2", "/?level=3&pkt=counts&t=5", "/?level=4&t=41", "/?results=1"]) {
      await page.goto(u, { waitUntil: "networkidle" });
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
      const bad = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(bad.map((v) => `${theme} ${u}: ${v.id} (${v.nodes.length}) ${v.nodes[0]?.target}`)).toEqual([]);
    }
  }
});

test("B6 is shown as measured on two laptops, not in the hardware-only list", async ({ page, request }) => {
  const b6 = (await (await request.get("/api/scene/b6")).json()).measurements as { id: string; verdict: string }[];
  expect(b6.map((m) => `${m.id}:${m.verdict}`)).toEqual(["run1:NOT_ESTABLISHED", "run2:ESTABLISHED"]);
  await page.goto("/?level=3", { waitUntil: "networkidle" });
  const strip = page.getByTestId("hw-faults");
  for (const id of ["A6", "A7", "B1", "B4"]) await expect(page.getByTestId(`hw-${id}`)).toContainText("requires hardware, not measured");
  await expect(page.getByTestId("hw-B6")).toHaveCount(0);
  await expect(strip.locator("li", { hasText: "Oscillator" })).toHaveCount(0);
  const b = page.getByTestId("hw-B6-measured");
  await expect(b).toContainText("measured on two laptops (software timestamping)");
  await expect(b).not.toContainText("not measured");
  await expect(page.getByTestId("hw-B6-run1")).toHaveText("run1 not established");
  await expect(page.getByTestId("hw-B6-run2")).toContainText("run2 established");
  await expect(b).toContainText("not an end-to-end detection test");
  await page.getByTestId("hw-B6-open").click();
  await expect(page.getByTestId("side-title")).toHaveText("Oscillator drift (B6, two-laptop measurement)");
});
