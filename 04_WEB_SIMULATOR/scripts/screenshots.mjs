// Capture the documentation screenshots in docs/screenshots/ from a running server.
//   node scripts/screenshots.mjs [baseUrl]      (default http://localhost:3000)
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const base = process.argv[2] ?? "http://localhost:3000";
const out = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "docs", "screenshots");
mkdirSync(out, { recursive: true });
const b = await chromium.launch();
const shot = async (page, name, opts = {}) => page.screenshot({ path: path.join(out, `${name}.png`), ...opts });

const desk = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
let p = await desk.newPage();
await p.goto(`${base}/`, { waitUntil: "networkidle" });
await shot(p, "01-home", { fullPage: true });

await p.goto(`${base}/learn`, { waitUntil: "networkidle" });
await shot(p, "02-learning-path");

await p.goto(`${base}/learn/bmca`, { waitUntil: "networkidle" });
await p.getByTestId("bmca-add-rogue").click();
await p.getByTestId("bmca-rogue-clockClass").selectOption("6");
await shot(p, "03-lesson-bmca-arena", { fullPage: true });

await p.goto(`${base}/learn/attack-vs-benign`, { waitUntil: "networkidle" });
for (const k of ["la1", "la2", "la3"]) await p.getByTestId(`reveal-${k}`).click();
await p.getByTestId("step-continue").click();
for (const [sc, v] of [["A1_rogue_master", "ATTACK"], ["B2_gm_failover", "BENIGN"], ["B_unplanned_failover", "UNKNOWN"], ["B_bc_replacement", "BENIGN"]]) await p.getByTestId(`game-${sc}-${v}`).click();
await shot(p, "04-lesson-you-are-the-rule", { fullPage: true });

await p.goto(`${base}/learn/ptp`, { waitUntil: "networkidle" });
await p.getByTestId("step-continue").isDisabled();
for (let i = 0; i < 4; i++) await p.getByTestId("seq-next").click();
await p.getByTestId("step-continue").click();
await p.getByTestId("offset-input").fill("300");
await p.getByTestId("offset-check").click();
await p.getByLabel(/Extra one-way delay/).fill("800");
await shot(p, "05-lesson-offset-calculator", { fullPage: true });

for (const [name, sc, t] of [["06-replay-A1-side-by-side", "A1_rogue_master", "12"], ["07-replay-C1-failover", "C1_removal", "3.5"], ["08-replay-B3-r17-H3-failure", "B3_pdv_congestion", "10"]]) {
  const rep = sc === "B3_pdv_congestion" ? 17 : 13;
  await p.goto(`${base}/replay?scenario=${sc}&rep=${rep}`, { waitUntil: "networkidle" });
  await p.getByTestId("rp-scrubber").fill(t);
  await p.getByTestId("rp-speed-0.5").click();
  await p.getByTestId("rp-play").click();
  await p.waitForTimeout(450);
  await p.getByTestId("rp-play").click();
  await shot(p, name, { fullPage: true });
}

await p.goto(`${base}/dashboard`, { waitUntil: "networkidle" });
await shot(p, "09-dashboard-hypotheses");
await p.locator("#per").scrollIntoViewIfNeeded();
await shot(p, "10-dashboard-per-scenario", { fullPage: true });

await p.goto(`${base}/sandbox`, { waitUntil: "networkidle" });
await p.waitForSelector("[data-testid=sb-model-card]");
await p.getByTestId("sb-scenario").selectOption("B3_pdv_congestion");
await shot(p, "11-sandbox-model", { fullPage: true });

await p.goto(`${base}/catalogue`, { waitUntil: "networkidle" });
await p.getByTestId("cat-search").fill("boundary clock");
await p.getByRole("button", { name: /^A8/ }).first().click();
await shot(p, "12-fault-catalogue");

await p.goto(`${base}/about`, { waitUntil: "networkidle" });
await shot(p, "13-about-limits-provenance", { fullPage: true });
await p.goto(`${base}/live`, { waitUntil: "networkidle" });
await shot(p, "14-live-mode-disabled");

const dark = await b.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "dark" });
p = await dark.newPage();
await p.goto(`${base}/replay?scenario=C3_wholesecond&rep=13`, { waitUntil: "networkidle" });
await p.getByTestId("rp-scrubber").fill("15");
await shot(p, "15-dark-mode-replay-C3");

const mob = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
p = await mob.newPage();
await p.goto(`${base}/`, { waitUntil: "networkidle" });
await shot(p, "16-mobile-home");
await p.goto(`${base}/replay?scenario=A1_rogue_master&rep=13`, { waitUntil: "networkidle" });
await p.getByTestId("rp-scrubber").fill("12");
await shot(p, "17-mobile-replay", { fullPage: true });

await b.close();
console.log(`screenshots written to ${out}`);
