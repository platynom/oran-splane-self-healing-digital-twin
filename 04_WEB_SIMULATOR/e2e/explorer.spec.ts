import { expect, test, type Page } from "@playwright/test";

declare global {
  interface Window {
    __oranExplorer?: { ready: boolean; fps: () => number; frames: () => number; project: (id: string) => { x: number; y: number; inFront: boolean } | null };
    __oranFlying?: boolean;
  }
}

function collectErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error" || m.type() === "warning") errors.push(`[${m.type()}] ${m.text()}`);
  });
  page.on("pageerror", (e) => errors.push(`[pageerror] ${e.message}`));
  return errors;
}
async function open(page: Page, url = "/") {
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.__oranExplorer?.ready === true, null, { timeout: 60_000 });
  await settled(page);
}
async function settled(page: Page) {
  await page.waitForFunction(() => window.__oranFlying !== true, null, { timeout: 30_000 });
  await page.waitForTimeout(150);
}
async function clickPart(page: Page, id: string) {
  const pos = await page.evaluate((i) => window.__oranExplorer!.project(i), id);
  expect(pos, `${id} projects onto the screen`).not.toBeNull();
  await page.mouse.move(pos!.x, pos!.y);
  await page.mouse.click(pos!.x, pos!.y);
}

test("home loads with a rendering WebGL canvas and the expected structure", async ({ page }) => {
  const errors = collectErrors(page);
  await open(page, "/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("O-RAN S-plane explorer");
  await expect(page.getByTestId("explorer-canvas")).toBeVisible();
  const gl = await page.evaluate(() => {
    const c = document.querySelector("canvas")!;
    const ctx = (c.getContext("webgl2") || c.getContext("webgl")) as WebGL2RenderingContext | null;
    return { hasContext: !!ctx, w: c.width, h: c.height };
  });
  expect(gl.hasContext).toBe(true);
  expect(gl.w).toBeGreaterThan(300);
  const f0 = await page.evaluate(() => window.__oranExplorer!.frames());
  await page.waitForTimeout(800);
  expect(await page.evaluate(() => window.__oranExplorer!.frames())).toBeGreaterThan(f0); // frames are being rendered
  await expect(page.getByTestId("breadcrumb")).toContainText("Whole O-RAN");
  await expect(page.getByTestId("dataset-strip")).toContainText("140 runs");
  await expect(page.getByTestId("dataset-strip")).toContainText("168 runs");
  await expect(page.getByTestId("dataset-strip")).toContainText("S15 not established");
  await expect(page.getByTestId("dataset-strip")).toContainText("raw samples: not in repo");
  // tier lighting: dimmed parts say so in the list
  for (const id of ["near-rt-ric", "o-cu", "core-5g", "o-cloud"]) await expect(page.getByTestId(`part-item-${id}`)).toHaveAttribute("data-dimmed", "true");
  for (const id of ["gm-a", "gm-b", "bc", "o-ru", "injector", "o-du", "smo-nonrt", "ue"]) await expect(page.getByTestId(`part-item-${id}`)).toBeEnabled();
  expect(errors).toEqual([]);
});

test("clicking a Tier-1 part flies to level 2 and shows its cited card", async ({ page }) => {
  const errors = collectErrors(page);
  await open(page, "/");
  await clickPart(page, "gm-a");
  await expect(page).toHaveURL(/level=2&focus=gm-a/);
  await expect(page.getByTestId("breadcrumb")).toContainText("Open Fronthaul (LLS-C3)");
  await expect(page.getByTestId("card-gm-a")).toBeVisible();
  await settled(page);
  // the first sentence carries a CONFIGURED tag, an UNVERIFIED status and a citation chip that opens the reference
  const s1 = page.getByTestId("sentence-gm-a.s1");
  await expect(s1).toContainText("priority2 100");
  await expect(s1).toHaveAttribute("data-status", "UNVERIFIED");
  await page.getByTestId("cite-gm-a.s1").click();
  const ref = page.getByTestId("ref-gm-a.s1");
  await expect(ref).toContainText("Testbed Configuration Reference");
  await expect(ref).toContainText("§4 Topology and node roles");
  await expect(ref.getByRole("link")).toHaveAttribute("href", /github\.com\/platynom\/oran-splane-self-healing-digital-twin\/blob\/full-project-2026-10-05\/00_LATEST/);
  expect(errors).toEqual([]);
});

test("a dimmed part is not clickable but shows its tooltip", async ({ page }) => {
  const errors = collectErrors(page);
  await open(page, "/");
  const before = page.url();
  const pos = await page.evaluate(() => window.__oranExplorer!.project("o-cu"));
  expect(pos).not.toBeNull();
  await page.mouse.move(pos!.x, pos!.y);
  const tip = page.getByTestId("part-tooltip");
  await expect(tip).toBeVisible();
  await expect(tip).toHaveAttribute("data-part", "o-cu");
  await expect(tip).toContainText("O-CU");
  await expect(tip).toContainText("Outside this project");
  await page.mouse.click(pos!.x, pos!.y);
  await page.waitForTimeout(400);
  expect(page.url()).toBe(before);
  await expect(page.getByTestId("card-o-cu")).toHaveCount(0);
  // the list entry is not a button and also shows the tooltip on keyboard focus
  await page.mouse.move(4, 4); // leave the canvas: the tooltip disappears
  await expect(tip).toHaveCount(0);
  const item = page.getByTestId("part-item-core-5g");
  await expect(item).not.toHaveRole("button");
  await item.focus();
  await expect(tip).toHaveAttribute("data-part", "core-5g");
  expect(errors).toEqual([]);
});

test("Esc goes back: focus first, then up a level; Back button does the same", async ({ page }) => {
  await open(page, "/?level=2&focus=bc");
  await expect(page.getByTestId("card-bc")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/\?level=2$/);
  await expect(page.getByTestId("card-bc")).toHaveCount(0);
  await expect(page.getByTestId("card-lls-c3")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByTestId("breadcrumb")).toHaveText("Whole O-RAN");
  await expect(page.getByTestId("back-btn")).toBeDisabled();
  await page.getByTestId("part-item-gm-b").click();
  await expect(page).toHaveURL(/level=2&focus=gm-b/);
  await page.getByTestId("back-btn").click();
  await page.getByTestId("back-btn").click();
  await expect(page).toHaveURL(/\/$/);
  await page.goBack(); // browser history follows the same states
  await expect(page).toHaveURL(/level=2/);
});

test("deep links restore level, LLS configuration and focus; reload keeps them", async ({ page }) => {
  await open(page, "/?level=2&lls=c1&focus=o-du");
  await expect(page.getByTestId("lls-c1")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("card-o-du")).toBeVisible();
  await expect(page.getByTestId("breadcrumb")).toContainText("LLS-C1");
  await expect(page.getByText("This configuration is shown for comparison only")).toBeVisible();
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("card-o-du")).toBeVisible();
  await expect(page.getByTestId("lls-c1")).toHaveAttribute("aria-selected", "true");
  await open(page, "/?level=1&focus=smo-nonrt");
  await expect(page.getByTestId("card-smo-nonrt")).toContainText("not implemented there");
  // invalid or dimmed focus values are ignored instead of breaking the view
  await open(page, "/?focus=o-cu&level=2&lls=zz");
  await expect(page.getByTestId("card-o-cu")).toHaveCount(0);
  await expect(page.getByTestId("lls-c3")).toHaveAttribute("aria-selected", "true");
});

test("LLS-C1..C4 are switchable; only C3 is the testbed's configuration", async ({ page }) => {
  const errors = collectErrors(page);
  await open(page, "/?level=2");
  await expect(page.getByTestId("lls-c3")).toContainText("testbed");
  for (const l of ["c1", "c2", "c4", "c3"]) {
    await page.getByTestId(`lls-${l}`).click();
    await expect(page).toHaveURL(l === "c3" ? /\/\?level=2$/ : new RegExp(`lls=${l}`));
    await expect(page.getByTestId(`card-lls-${l}`)).toBeVisible();
    await settled(page);
  }
  await page.getByTestId("lls-c2").click();
  await expect(page.getByTestId("card-lls-c2")).toContainText("models O-RAN LLS-C2/C3");
  await expect(page.getByTestId("parts-list")).not.toContainText("GM-A"); // not the testbed's chain
  await page.getByTestId("lls-c3").click();
  await expect(page.getByTestId("parts-list")).toContainText("GM-A");
  await expect(page.getByTestId("parts-list")).toContainText("Standby boundary clock");
  expect(errors).toEqual([]);
});

test("SOURCE_NEEDED statements are never rendered; a hidden-count note is", async ({ page, request }) => {
  const api = await (await request.get("/api/scene/architecture")).json();
  const all = JSON.stringify(api.elements);
  expect(all).not.toContain("o-ran-sync");
  expect(all).not.toContain("implements a specific PTP clock type");
  expect(api.stats).toMatchObject({ elements: 25, sentences: 69, sourceNeeded: 4, unverified: 65 });
  await open(page, "/?level=2&focus=o-du");
  await expect(page.getByTestId("card-o-du")).not.toContainText("PTP clock type");
  await expect(page.getByTestId("hidden-o-du")).toContainText("1 statement is hidden");
  await expect(page.getByTestId("card-o-du").locator("li[data-status]")).toHaveCount(4);
  await open(page, "/?level=1&focus=fh-cplane");
  await expect(page.getByTestId("card-fh-cplane")).toContainText("Consequence card");
  await expect(page.getByTestId("card-fh-cplane")).toContainText("UNKNOWN");
  await expect(page.getByTestId("card-fh-cplane")).not.toContainText("stops or is misaligned");
});

test("B6 figures on the oscillator card come from the database, with the raw-data caveat", async ({ page }) => {
  await open(page, "/?level=1&focus=osc-drift");
  const card = page.getByTestId("b6-card");
  await expect(card).toContainText("+21.013 ppm");
  await expect(card).toContainText("+20.161 ppm");
  await expect(card).toContainText("not established");
  await expect(card).toContainText("Raw per-sample files are not in the repository");
});

test("projector mode and large text apply to the page, persist, and reset when leaving", async ({ page }) => {
  const errors = collectErrors(page);
  await open(page, "/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  const bgDark = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  await page.getByTestId("theme-projector").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "projector");
  expect(await page.evaluate(() => getComputedStyle(document.body).backgroundColor)).toBe("rgb(255, 255, 255)");
  expect(bgDark).not.toBe("rgb(255, 255, 255)");
  const fs0 = await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).fontSize));
  await page.getByTestId("text-toggle").click();
  expect(await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).fontSize))).toBeCloseTo(fs0 * 1.25, 1);
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "projector");
  await expect(page.locator("html")).toHaveAttribute("data-text", "large");
  await page.waitForFunction(() => window.__oranExplorer?.ready === true);
  await page.goto("/learn", { waitUntil: "networkidle" });
  await expect(page.locator("html")).not.toHaveAttribute("data-theme", /.+/);
  await page.goto("/", { waitUntil: "networkidle" });
  await page.getByTestId("theme-dark").click();
  await page.getByTestId("text-toggle").click();
  expect(errors).toEqual([]);
});

test("quality can be set from the URL and the selector; reduced motion jumps the camera without flying", async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: "reduce" });
  const page = await ctx.newPage();
  const errors = collectErrors(page);
  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.__oranExplorer?.ready === true);
  await expect(page.getByTestId("quality-select")).toHaveValue("low"); // reduced motion starts at low quality
  await page.getByTestId("quality-select").selectOption("high");
  await expect(page.getByTestId("explorer-canvas")).toBeVisible();
  await page.goto("/?q=medium", { waitUntil: "networkidle" });
  await expect(page.getByTestId("quality-select")).toHaveValue("medium");
  await expect(page.getByTestId("quality-badge")).toHaveText("fixed");
  await page.goto("/?level=2&focus=bc", { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.__oranExplorer?.ready === true);
  expect(await page.evaluate(() => window.__oranFlying)).toBe(false);
  expect(errors).toEqual([]);
  await ctx.close();
});

test("without WebGL the page still explains itself and keeps all content readable", async ({ page }) => {
  const errors = collectErrors(page);
  await page.addInitScript(() => {
    const orig = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...rest: unknown[]) {
      if (type === "webgl" || type === "webgl2" || type === "experimental-webgl") return null;
      return (orig as (...a: unknown[]) => unknown).call(this, type, ...rest) as never;
    } as typeof orig;
  });
  await page.goto("/?level=2&focus=gm-a", { waitUntil: "networkidle" });
  await expect(page.getByTestId("no-webgl")).toContainText("WebGL is not available");
  await expect(page.getByTestId("card-gm-a")).toBeVisible();
  await page.getByTestId("part-item-bc").click();
  await expect(page.getByTestId("card-bc")).toBeVisible();
  expect(errors).toEqual([]);
});

test("scene APIs are read-only and return the loaded datasets", async ({ request }) => {
  const ds = await (await request.get("/api/scene/datasets")).json();
  const byId = Object.fromEntries(ds.datasets.map((d: { id: string }) => [d.id, d]));
  expect(byId["recovery-140"].rows).toBe(140);
  expect(byId["campaign-168"]).toMatchObject({ rows: 168, evidenceRows: 168, frames: 1451909 });
  expect(byId["pilot-13sep"].rows).toBe(40);
  expect(byId["b6"]).toMatchObject({ rows: 2, rawCsvPresent: false });
  const camp = await (await request.get("/api/scene/campaign")).json();
  expect(camp.runs).toBe(168);
  expect(camp.scenarios).toHaveLength(14);
  const one = await (await request.get("/api/scene/campaign?scenario=A1_rogue_master&rep=1")).json();
  expect(one.evidence.csvRows).toBe(one.evidence.nPacketsClaimed);
  expect((await request.get("/api/scene/campaign?scenario=nope&rep=1")).status()).toBe(404);
  const pilot = await (await request.get("/api/scene/pilot")).json();
  expect(pilot.summaries.map((s: { id: string; status: string }) => `${s.id}:${s.status}`)).toEqual(["S11:PRESPECIFIED_BRANCH_MET", "S15:NOT_ESTABLISHED"]);
  const b6 = await (await request.get("/api/scene/b6")).json();
  expect(b6.rawSamplesAvailable).toBe(false);
  for (const u of ["/api/scene/datasets", "/api/scene/campaign", "/api/scene/pilot", "/api/scene/b6"]) expect((await request.post(u, { data: {} })).status()).toBe(405);
});

test("level 3-5 deep links are accepted and explain that they come later", async ({ page }) => {
  await open(page, "/?level=4");
  await expect(page.getByTestId("level-pending")).toContainText("planned for a later phase");
  await expect(page.getByTestId("lls-c3")).toBeVisible();
});

test("no console errors on every explorer view (levels, LLS configurations, themes)", async ({ page }) => {
  const errors = collectErrors(page);
  for (const u of ["/", "/?level=2", "/?level=2&lls=c1", "/?level=2&lls=c2", "/?level=2&lls=c4", "/?level=2&focus=injector", "/?focus=gnss-time", "/?focus=air-interface"]) {
    await open(page, u);
    await page.getByTestId("theme-projector").click();
    await page.waitForTimeout(250);
    await page.getByTestId("theme-dark").click();
  }
  expect(errors).toEqual([]);
});
