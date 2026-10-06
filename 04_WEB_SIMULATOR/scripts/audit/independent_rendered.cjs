/* eslint-disable @typescript-eslint/no-require-imports -- plain Node script, run with `node` */
// Reads the RENDERED simulator DOM for each expected state. Uses only Playwright; no app code.
//   BASE=http://localhost:3000 node scripts/audit/independent_rendered.cjs   (run from 04_WEB_SIMULATOR)
const AUDIT = process.env.AUDIT_DIR || "/tmp/sim-audit";
const BASE = process.env.BASE || "http://localhost:3000";
const { chromium } = require("@playwright/test");
const fs = require("fs");
const exp = JSON.parse(fs.readFileSync(`${AUDIT}/expected.json`, "utf8"));
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const out = [];
  for (const s of exp.states) {
    const q = `scenario=${s.scenario}&rep=${s.rep}&arm=${s.arm}&t=${s.t}`;
    await page.goto(`${BASE}/?level=3&${q}`, { waitUntil: "networkidle" });
    const arm = page.getByTestId(`rp-arm-${s.arm}`);
    await arm.locator("table tbody tr").first().waitFor();
    const rows = {};
    for (const n of ["ru1", "ru2", "ru3"]) {
      const tr = arm.locator("table tbody tr").nth(Number(n[2]) - 1);
      const tds = tr.locator("td");
      rows[n] = { label: (await tds.nth(0).textContent()).trim(), portState: (await tds.nth(1).textContent()).trim(), parentTitle: await tds.nth(2).getAttribute("title") };
    }
    const badge = await arm.locator("header").textContent();
    const log = arm.getByTestId(`rp-log-${s.arm}`);
    const items = await log.locator("li[data-kind]").evaluateAll((els) => els.map((e) => [e.getAttribute("data-kind"), e.getAttribute("data-t")]));
    const time = await page.getByTestId("rp-time").textContent();
    await page.goto(`${BASE}/?level=4&${q}`, { waitUntil: "networkidle" });
    await page.getByTestId("loop-stages").waitFor();
    await page.getByTestId("stage-detect").waitFor();
    // wait for run data (stage tiles carry data-never only once the run is loaded)
    await page.waitForFunction(() => document.querySelector('[data-testid="stage-rollback"]')?.getAttribute("data-never") === "true" || document.querySelector('[data-testid="stage-rollback"]')?.getAttribute("data-never") === "false");
    await page.waitForTimeout(300);
    const stages = {};
    for (const st of ["detect", "localise", "decide", "act", "verify", "rollback"]) {
      const el = page.getByTestId(`stage-${st}`);
      stages[st] = { lit: await el.getAttribute("data-lit"), never: await el.getAttribute("data-never"), text: (await el.textContent()).trim() };
    }
    out.push({ run: s.run, t: s.t, time: time.trim(), rows, badge: badge.trim(), logCount: items.length, items, stages });
  }
  fs.writeFileSync(`${AUDIT}/rendered.json`, JSON.stringify({ errors, states: out }, null, 1));
  await browser.close();
  console.log(`read ${out.length} states, page errors: ${errors.length}`);
})();
