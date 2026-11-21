// Spec 035: the demonstrator's code in Node (node --test demo_node.mjs). Track editing, bearing
// determinism, the JavaScript least squares against Python's golden vectors, the dashboard's
// acceptance criteria 2-5, the LinkML validation, and the ONNX physics layer (one leg against the
// JavaScript solve; the oracle on a target turn) in onnxruntime-web's Node build of the same
// WASM. The learned model runs only with DEMO_E=1 (about three minutes).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import * as T from "../../site/static/demo-data/js/track.js";
import { bearings, windowRows, problemOf, targetManoeuvresIn } from "../../site/static/demo-data/js/scenario.js";
import { evaluate, observability } from "../../site/static/demo-data/js/metrics.js";
import { PRESETS, clone } from "../../site/static/demo-data/js/presets.js";
import { SOLVERS } from "../../site/static/demo-data/js/solvers.js";
import { encodeFragment, decodeFragment, checkScenario } from "../../site/static/demo-data/js/codec.js";
import { goldenCases } from "./demo_problems.mjs";

const here = new URL(".", import.meta.url).pathname;
const site = new URL("../../site/static/", import.meta.url).pathname;
const schema = JSON.parse(readFileSync(site + "demo-data/demo-scenario.schema.json", "utf8"));
const preset = (id) => clone(PRESETS.find((p) => p.id === id).scenario);
const solver = (name) => SOLVERS.find((s) => s.info.name === name);

let ort = null;
const sessions = {};
const GRAPHS = { "tl-layer": "demo-data/tl-layer.onnx", es: "viewer-data/es.onnx", ew: "viewer-data/model.onnx", layer: "viewer-data/layer.onnx" };
async function run(name, feeds) {
  if (!ort) {
    ort = await import("onnxruntime-web/dist/ort.node.min.mjs").catch(() => import("onnxruntime-web"));
    ort.env.wasm.numThreads = 1;
  }
  sessions[name] ??= await ort.InferenceSession.create(site + GRAPHS[name]);
  const f = {};
  for (const [k, v] of Object.entries(feeds)) f[k] = v.dtype === "int64" ? new ort.Tensor("int64", BigInt64Array.from(v.data, (x) => BigInt(Math.round(x))), v.shape) : new ort.Tensor("float64", Float64Array.from(v.data), v.shape);
  const out = await sessions[name].run(f);
  const o = {};
  for (const [k, t] of Object.entries(out)) o[k] = Float64Array.from(t.data, Number);
  return o;
}

async function solveScenario(sc, name = sc.solver) {
  const b = bearings(sc);
  const rows = windowRows(sc, b);
  const { problem, origin, t0 } = problemOf(sc, b, rows);
  const kn = targetManoeuvresIn(sc, b);
  const sol = await solver(name).solve(problem, { run });
  return { b, rows, sol, kn, ev: evaluate(sc, b, rows, origin, t0, sol, kn), obs: observability(sc, b, rows, kn) };
}

// ---------- tracks ----------
test("waypoint drag moves only the adjacent legs (FR-002)", () => {
  const tr = preset("good-geometry").ownship;
  const W0 = T.waypoints(tr);
  const moved = T.moveWaypoint(tr, 2, W0[2][0] + 1, W0[2][1] - 0.5);
  const W1 = T.waypoints(moved);
  for (const j of [0, 1, 3, 4]) {
    assert.ok(Math.hypot(W1[j][0] - W0[j][0], W1[j][1] - W0[j][1]) < 1e-9, `waypoint ${j} stayed`);
  }
  assert.ok(Math.abs(W1[2][0] - W0[2][0] - 1) < 1e-9);
  assert.deepEqual(moved.legs.map((l) => l.duration_s), tr.legs.map((l) => l.duration_s));
});

test("velocity handle turns the downstream track rigidly (FR-003, decision 10)", () => {
  const tr = preset("good-geometry").ownship;
  const out = T.setLegVelocity(tr, 1, tr.legs[1].course_deg + 30, 12);
  const a = T.waypoints(tr), b = T.waypoints(out);
  // distances between downstream waypoints are kept; the angle between downstream legs too
  for (let j = 2; j < a.length - 1; j++) {
    const da = Math.hypot(a[j + 1][0] - a[j][0], a[j + 1][1] - a[j][1]);
    const db = Math.hypot(b[j + 1][0] - b[j][0], b[j + 1][1] - b[j][1]);
    assert.ok(Math.abs(da - db) < 1e-9);
  }
  for (let i = 2; i < tr.legs.length; i++) assert.ok(Math.abs(((out.legs[i].course_deg - tr.legs[i].course_deg - 30 + 540) % 360) - 180) < 1e-9);
  assert.equal(out.legs[1].speed_kt, 12);
  const h = T.handleOf(out, 1);
  const v = T.velocityFromHandle(out, 1, h[0], h[1]);
  assert.ok(Math.abs(v.speed_kt - 12) < 1e-9 && Math.abs(v.course_deg - out.legs[1].course_deg) < 1e-9);
});

test("insert then delete a waypoint restores the track (FR-004)", () => {
  const tr = preset("good-geometry").target;
  const ins = T.insertWaypoint(tr, 0, 0.5);
  assert.equal(ins.legs.length, 2);
  const del = T.deleteWaypoint(ins, 1);
  assert.equal(del.legs.length, 1);
  assert.ok(Math.abs(del.legs[0].course_deg - tr.legs[0].course_deg) < 1e-9);
  assert.ok(Math.abs(del.legs[0].speed_kt - tr.legs[0].speed_kt) < 1e-9);
});

test("turns are arcs at the waypoint's rate; a turn that does not fit is clamped (FR-005)", () => {
  const tr = preset("good-geometry").ownship;
  const p = T.buildPath(tr);
  const J = p.joins[0];
  assert.ok(!J.clamped && Math.abs(J.rate_dps - 1) < 1e-9);
  // the path is continuous in position and its speed is the leg's
  for (let t = 1; t < p.end; t += 7) {
    const a = T.stateAt(p, t), b = T.stateAt(p, t + 0.01);
    assert.ok(Math.hypot(b.x - a.x, b.y - a.y) < 0.2, `continuous at ${t}`);
    assert.ok(Math.abs(Math.hypot(a.vx, a.vy) - 8 * T.KT) < 1e-9);
  }
  const short = { ...tr, legs: tr.legs.map((l) => ({ ...l, duration_s: 60, turn_rate_dps: 0.25 })) };
  assert.ok(T.buildPath(short).joins.every((j) => j.clamped));
});

// ---------- bearings ----------
test("same seed and scenario give identical bearings; the window does not change them (FR-011, NFR-2)", () => {
  const sc = preset("good-geometry");
  const a = bearings(sc), b = bearings(clone(sc));
  assert.deepEqual(Array.from(a.z), Array.from(b.z));
  const c = bearings({ ...sc, window: { start_s: 600, end_s: 1200 } });
  assert.deepEqual(Array.from(a.z), Array.from(c.z));
  const d = bearings({ ...sc, seed: 2 });
  assert.notDeepEqual(Array.from(a.z), Array.from(d.z));
  // the noise is about sigma
  let s2 = 0;
  for (let i = 0; i < a.n; i++) s2 += Math.atan2(Math.sin(a.z[i] - a.truth[i]), Math.cos(a.z[i] - a.truth[i])) ** 2;
  const sd = Math.sqrt(s2 / a.n) / T.DEG;
  assert.ok(sd > 0.9 && sd < 1.1, `noise sd ${sd}`);
});

// ---------- least squares against Python ----------
test("JavaScript least squares equals Python's on the golden problems (FR-025)", async () => {
  const golden = JSON.parse(readFileSync(here + "demo/golden-ls.json", "utf8"));
  const cases = goldenCases();
  const sha = createHash("sha256").update(JSON.stringify({ cases }) + "\n").digest("hex");
  assert.equal(sha, golden.problems_sha256, "the page builds the problems the golden file was made from");
  const ls = solver("ls-js");
  for (const c of cases) {
    const g = golden.solutions[c.id];
    const sol = await ls.solve({ t_s: c.t, bearing_rad: c.z, own_x_m: c.ox, own_y_m: c.oy, sigma_rad: 0.01 });
    const th = [sol.x_m[0], sol.y_m[0], sol.vx_mps[0], sol.vy_mps[0]];
    th.forEach((x, k) => assert.ok(Math.abs(x - g.theta[k]) <= 1e-6 * Math.max(1, Math.abs(g.theta[k])), `${c.id} theta[${k}] ${x} vs ${g.theta[k]}`));
    assert.equal(sol.iterations, g.iterations, c.id);
    assert.equal(sol.status === "converged", g.converged, c.id);
  }
});

// ---------- acceptance ----------
test("every preset solves with every dashboard number (acceptance 1)", async () => {
  for (const p of PRESETS) {
    const r = await solveScenario(clone(p.scenario));
    assert.notEqual(r.sol.status, "failed", p.id);
    for (const k of ["range_m", "bearing_deg", "course_deg", "speed_kt", "position_nm"]) assert.ok(Number.isFinite(r.ev.summary[k].rms), `${p.id} ${k}`);
    assert.ok(["green", "amber", "red"].includes(r.obs.level));
  }
});

test("zero noise, good geometry: range error under 0.1% (acceptance 2)", async () => {
  const r = await solveScenario({ ...preset("good-geometry"), sigma_deg: 0 });
  assert.ok(r.ev.summary.range_pct.max < 0.1, `${r.ev.summary.range_pct.max}`);
  assert.equal(r.obs.level, "green");
});

test("no ownship zig: observability red, solution still shown (acceptance 3)", async () => {
  const r = await solveScenario(preset("no-zig"));
  assert.equal(r.obs.level, "red");
  assert.notEqual(r.sol.status, "failed");
  assert.ok(r.ev.t.length > 0);
});

test("target turn: mismatch flagged; one target leg clears it and cuts the error (acceptance 4)", async () => {
  const sc = preset("target-turn");
  const full = await solveScenario(sc);
  assert.ok(full.kn.length > 0, "a target manoeuvre in the window");
  const leg = await solveScenario({ ...sc, window: { start_s: 0, end_s: 3500 } });
  assert.equal(leg.kn.length, 0);
  assert.ok(leg.ev.summary.range_pct.rms < full.ev.summary.range_pct.rms / 5, `${leg.ev.summary.range_pct.rms} vs ${full.ev.summary.range_pct.rms}`);
});

test("URL and JSON round trips reproduce the solution (acceptance 5, FR-042/043)", async () => {
  const sc = { ...preset("target-turn"), seed: 12345, sigma_deg: 2.5, window: { start_s: 300, end_s: 5000 } };
  const back = await decodeFragment("#" + (await encodeFragment(sc)));
  assert.deepEqual(back, sc);
  const viaJson = JSON.parse(JSON.stringify(sc, null, 2));
  assert.deepEqual(checkScenario(schema, viaJson), []);
  const a = await solveScenario(sc), b = await solveScenario(back);
  assert.deepEqual(a.sol.x_m, b.sol.x_m);
});

test("LinkML validation accepts every preset and rejects a bad file with its message (FR-043)", () => {
  for (const p of PRESETS) assert.deepEqual(checkScenario(schema, p.scenario), [], p.id);
  const bad = clone(PRESETS[0].scenario);
  bad.sigma_deg = 9;
  delete bad.ownship.legs[0].speed_kt;
  bad.extra = 1;
  const errs = checkScenario(schema, bad);
  assert.ok(errs.some((e) => e.includes("sigma_deg") && e.includes("maximum")), errs.join("; "));
  assert.ok(errs.some((e) => e.includes('"speed_kt"')), errs.join("; "));
  assert.ok(errs.some((e) => e.includes('"extra"')), errs.join("; "));
});

// ---------- ONNX ----------
test("the ONNX physics layer with one leg equals the JavaScript solve on noise-free bearings", async () => {
  const sc = { ...preset("good-geometry"), sigma_deg: 0 };
  const js = await solveScenario(sc, "ls-js");
  const nx = await solveScenario(sc, "layer-cv");
  assert.ok(nx.ev.summary.range_pct.max < 0.1, `${nx.ev.summary.range_pct.max}`);
  assert.ok(Math.abs(nx.sol.x_m.at(-1) - js.sol.x_m.at(-1)) < 1, "end positions within 1 m");
  assert.equal(nx.sol.stride, 2, "1,429 bearings thinned to 715 rows");
});

test("the oracle told the manoeuvre times removes the turn's bias", async () => {
  const sc = { ...preset("target-turn"), sigma_deg: 0 };
  const cv = await solveScenario(sc, "layer-cv");
  const or = await solveScenario(sc, "layer-oracle");
  assert.ok(or.ev.summary.range_pct.rms < 0.5 && cv.ev.summary.range_pct.rms > 20, `${or.ev.summary.range_pct.rms} vs ${cv.ev.summary.range_pct.rms}`);
});

test("the learned model E answers in the window (DEMO_E=1)", { skip: process.env.DEMO_E !== "1" }, async () => {
  const r = await solveScenario(preset("good-geometry"), "e-gate2");
  assert.equal(r.sol.status, "converged");
  assert.ok(r.ev.t.length > 50);
  assert.ok(r.ev.summary.range_pct.rms < 50);
});
