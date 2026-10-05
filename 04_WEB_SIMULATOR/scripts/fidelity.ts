/**
 * Data-fidelity check: every number the simulator renders (server-rendered Results overlay and Datasets panel, and
 * the run API that drives the replay and loop stages) is compared with the project's source files and the database.
 *
 *   BASE=http://localhost:3000 npx tsx scripts/fidelity.ts      (exit 1 on any mismatch)
 *
 * Sources compared against, independently of the app code where possible:
 *   03_RECOVERY_LOOP_S-PLANE/results/EVALUATION_RL.json   (per-run and per-scenario results of the 140 runs)
 *   data/derived/extra.json.gz                            (campaign evidence counts from the corrected archive)
 *   outputs/empirical_software_network_pilot_v1/S11_*.json, S15_*.json, outputs/B6_two_machine_2026-10-02/*.json
 *   PostgreSQL rows (campaign verdicts; the Wilson interval is recomputed here with its own implementation)
 */
import { PrismaClient } from "@prisma/client";
import { readFileSync, writeFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import path from "node:path";
import { pyRound } from "../src/lib/metrics";

/* eslint-disable @typescript-eslint/no-explicit-any */
const BASE = process.env.BASE ?? "http://localhost:3000";
const ROOT = path.join(__dirname, "..", "..");
const json = (p: string) => JSON.parse(readFileSync(path.join(ROOT, p), "utf8"));
const prisma = new PrismaClient();
const results: { check: string; rendered: string; expected: string; ok: boolean }[] = [];
const cmp = (check: string, rendered: string | undefined, expected: string) =>
  results.push({ check, rendered: rendered ?? "(not rendered)", expected, ok: rendered === expected });

async function page(url: string): Promise<Map<string, string>> {
  const r = await fetch(BASE + url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  const html = (await r.text()).replace(/<!-- -->/g, "");
  const m = new Map<string, string>();
  // text content of each element carrying a data-testid (balanced scan, so nested testids are read too)
  const open = /<(\w+)[^>]*data-testid="([^"]+)"[^>]*>/g;
  for (let x = open.exec(html); x; x = open.exec(html)) {
    const tag = x[1], id = x[2];
    if (m.has(id)) continue;
    const re = new RegExp(`<${tag}[\\s>]|</${tag}>`, "g");
    re.lastIndex = x.index + x[0].length;
    let depth = 1, end = html.length;
    for (let y = re.exec(html); y; y = re.exec(html)) {
      depth += y[0].startsWith("</") ? -1 : 1;
      if (depth === 0) {
        end = y.index;
        break;
      }
    }
    m.set(id, html.slice(x.index + x[0].length, end).replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").replace(/&#x27;/g, "'").trim());
  }
  return m;
}

function wilson(k: number, n: number) {
  const z = 1.96, p = k / n, d = 1 + (z * z) / n;
  const c = (p + (z * z) / (2 * n)) / d, h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [Math.max(0, c - h), Math.min(1, c + h)].map((x) => (Math.round(x * 1e4) / 1e4).toFixed(3));
}

async function main() {
  const ev = json("03_RECOVERY_LOOP_S-PLANE/results/EVALUATION_RL.json");

  // ---- Results overlay vs EVALUATION_RL.json summary
  const R = await page("/?results=1");
  for (const [sc, arms] of Object.entries<any>(ev.summary)) {
    for (const arm of ["control", "loop"]) cmp(`${sc} ${arm} median unhealthy s`, R.get(`agg-${sc}-${arm}-median`), `${arms[arm].unhealthy_s_median.toFixed(2)} s`);
    cmp(`${sc} restored at end`, R.get(`agg-${sc}-restored`), `control ${arms.control.restored_at_end}/${arms.control.n} · loop ${arms.loop.restored_at_end}/${arms.loop.n}`);
    cmp(`${sc} loop executed disruptive actions`, R.get(`agg-${sc}-loop-actions`)?.split(" · ")[0], String(arms.loop.disruptive_actions));
    cmp(`${sc} loop verified`, R.get(`agg-${sc}-verified`), arms.loop.verify_total ? `${arms.loop.verify_ok}/${arms.loop.verify_total}` : "–");
  }

  // ---- campaign numbers vs DB rows, recomputed here
  const rows = await prisma.campaignRun.findMany();
  const A = rows.filter((r) => r.expected === "ATTACK"), B = rows.filter((r) => r.expected === "BENIGN");
  const ALIAS: Record<string, string> = { A_intercept: "C1", A_malformed: "C2", A_wholesecond: "C3" };
  const tp = A.filter((r) => r.v3Verdict === "ATTACK").length, tn = B.filter((r) => r.v3Verdict === "BENIGN").length;
  const attr = A.filter((r) => (ALIAS[r.v3Hint ?? ""] ?? r.v3Hint) === r.truthFault).length;
  cmp("campaign v3 sensitivity", R.get("camp-v3-sens"), `${tp}/${A.length} = ${(tp / A.length).toFixed(3)}`);
  cmp("campaign v3 attribution", R.get("camp-v3-attr"), `${attr}/${A.length} = ${(attr / A.length).toFixed(3)}`);
  cmp("campaign v3 attribution equals the brief's 84/96", `${attr}/${A.length}`, "84/96");
  for (const [l, k, n] of [["sensitivity", tp, A.length], ["specificity", tn, B.length], ["attribution", attr, A.length]] as const) {
    const [lo, hi] = wilson(k, n);
    cmp(`Wilson 95% ${l}`, R.get(`camp-wilson-${l}`)?.replace(/^;\s*/, ""), `${l} ${k}/${n} [${lo}, ${hi}]`);
  }

  // ---- Datasets panel vs source files
  const D = await page("/?panel=datasets");
  const extra = JSON.parse(gunzipSync(readFileSync(path.join(__dirname, "..", "data", "derived", "extra.json.gz"))).toString("utf8"));
  const s11 = json("outputs/empirical_software_network_pilot_v1/S11_CLOSED_LOOP_EVALUATION.json");
  const s15 = json("outputs/empirical_software_network_pilot_v1/S15_INDEPENDENT_VALIDATION_EVALUATION.json");
  cmp("recovery runs", D.get("ds-recovery-rows"), String(ev.runs.length));
  cmp("campaign runs", D.get("ds-campaign-rows"), String(extra.counts.campaign));
  cmp("campaign runs with evidence", D.get("ds-campaign-evidence"), String(extra.counts.campaign));
  cmp("campaign PTP frames", D.get("ds-campaign-frames"), extra.counts.campaignCsvRows.toLocaleString("en-US"));
  cmp("S11 trials", D.get("ds-pilot-s11"), String(Object.values<any>(s11.runs).reduce((a, d) => a + Object.keys(d).length, 0)));
  cmp("S15 trials", D.get("ds-pilot-s15"), String(s15.runs.length));
  cmp("S15 label", D.get("ds-pilot-s15-status"), "independent validation S15 not established");
  for (const [id, rel] of [["run1", "drift_pair.json"], ["run2", "run2/drift_pair_run2.json"]]) {
    const d = json(`outputs/B6_two_machine_2026-10-02/${rel}`);
    // rendered at 3 decimals, the precision DRIFT_REPORT.md quotes
    cmp(`B6 ${id} relative ppm`, D.get(`ds-b6-${id}-ppm`), d.relative_frequency_offset_ppm.ppm.toFixed(3));
    cmp(`B6 ${id} 95% CI`, D.get(`ds-b6-${id}-ci`), d.relative_frequency_offset_ppm.ci95.map((x: number) => x.toFixed(3)).join(" to "));
  }

  // ---- run API (drives the replay, packet inspector and loop stages) vs EVALUATION_RL.json per run
  // EVALUATION_RL.json was written by Python: round() is half-even on exact ties, so compare with the same rounding
  const r2 = (x: number | null) => (x === null || x === undefined ? "null" : pyRound(x, 2).toFixed(2));
  for (const er of ev.runs) {
    const api = await (await fetch(`${BASE}/api/runs/${er.run}`)).json();
    cmp(`${er.run} unhealthy_s`, r2(api.unhealthyS), r2(er.unhealthy_s));
    cmp(`${er.run} restored_at_end`, String(api.restoredAtEnd), String(er.restored_at_end));
    const acts = api.events.filter((e: any) => e.source === "loop" && (e.kind === "act" || e.kind === "would_act"));
    cmp(`${er.run} logged actions`, acts.map((a: any) => `${a.kind}:${a.action}:${a.target}@${r2(a.t)}`).join(" "), er.actions.map((a: any) => `${a.kind}:${a.action}:${a.target}@${r2(a.t)}`).join(" "));
    cmp(`${er.run} verify count`, String(api.events.filter((e: any) => e.kind === "verify").length), String(er.verifies.length));
    cmp(`${er.run} rollbacks`, String(api.events.filter((e: any) => e.kind === "rollback").length), "0");
  }

  const bad = results.filter((r) => !r.ok);
  const out = path.join(__dirname, "..", "docs", "SIM_FIDELITY.json");
  writeFileSync(out, JSON.stringify({ base: BASE, checked: results.length, mismatches: bad.length, failures: bad, generatedAt: new Date().toISOString() }, null, 1) + "\n");
  console.log(`fidelity: ${results.length} values checked, ${bad.length} mismatches`);
  for (const b of bad.slice(0, 30)) console.log(`MISMATCH ${b.check}: rendered "${b.rendered}" expected "${b.expected}"`);
  process.exitCode = bad.length ? 1 : 0;
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());
