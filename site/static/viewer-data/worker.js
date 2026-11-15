// The viewer's compute worker (specs 020 and 021), a module worker. It runs the exported graphs
// in ONNX Runtime Web (WASM, one thread): E-w on shipped inputs one row at a time, and live
// mode, the carried model end to end from bearings (js/pipeline.js). The page and the CI
// conformance leg (conformance/onnx/viewer_leg.mjs) both drive it.
//
// In:  {type: "init", ortBase, models: {ew, es, layer}}  (URLs; es and layer load on first use)
//      {type: "run", id, feeds}                           E-w on one row's feeds
//      {type: "live", id, scenario}                       the pipeline on a scenario's arrays
//      {type: "cancel", id}
// Out: {type: "ready", loadMs} | {type: "result", id, outputs, ms}
//      | {type: "progress", id, ...} | {type: "live-done", id, result, ms} | {type: "error", id?, message}
let ort = null;
let urls = null;
const sessions = {};
const cancelled = new Set();

async function session(name) {
  if (!sessions[name]) sessions[name] = ort.InferenceSession.create(urls[name], { executionProviders: ["wasm"] });
  return sessions[name];
}

function tensor(v) {
  if (v.dtype === "int64") return new ort.Tensor("int64", BigInt64Array.from(v.data, (x) => BigInt(Math.round(x))), v.shape);
  return new ort.Tensor("float64", Float64Array.from(v.data), v.shape);
}

async function run(name, feeds) {
  const s = await session(name);
  const f = {};
  for (const [k, v] of Object.entries(feeds)) f[k] = tensor(v);
  const out = await s.run(f);
  const o = {};
  for (const [k, t] of Object.entries(out)) o[k] = Float64Array.from(t.data, Number);
  return o;
}

self.onmessage = async (ev) => {
  const msg = ev.data;
  try {
    if (msg.type === "init") {
      ort = await import(msg.ortBase + "ort.wasm.min.mjs");
      ort.env.wasm.wasmPaths = msg.ortBase;
      ort.env.wasm.numThreads = 1;
      urls = msg.models;
      const t0 = performance.now();
      await session("ew");
      self.postMessage({ type: "ready", loadMs: performance.now() - t0 });
      return;
    }
    if (msg.type === "run") {
      const t0 = performance.now();
      const outputs = await run("ew", msg.feeds);
      self.postMessage({ type: "result", id: msg.id, outputs, ms: performance.now() - t0 });
      return;
    }
    if (msg.type === "cancel") {
      cancelled.add(msg.id);
      return;
    }
    if (msg.type === "live") {
      const { runLive, scenarioOf } = await import("./js/pipeline.js");
      const t0 = performance.now();
      const result = await runLive(
        scenarioOf(msg.scenario),
        run,
        (p) => self.postMessage({ type: "progress", id: msg.id, ...p }),
        () => cancelled.has(msg.id),
      );
      self.postMessage({ type: "live-done", id: msg.id, result, ms: performance.now() - t0 });
    }
  } catch (e) {
    self.postMessage({ type: "error", id: msg.id, message: String(e && e.message ? e.message : e) });
  }
};
