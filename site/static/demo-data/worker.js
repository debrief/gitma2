// The demonstrator's solver worker (spec 035 FR-023), a module worker. JavaScript solvers run
// at once; ONNX solvers load ONNX Runtime Web (WASM, one thread) on first use. The page posts
// one request per recompute and discards any result older than its latest request.
//
// In:  {type: "init", ortBase, models: {"tl-layer", "tlm-s1", "tlm-s2", "tlm-s3"}}  (URLs)
//      {type: "solve", id, solver, problem}
//      {type: "cancel", id}
// Out: {type: "ready"} | {type: "solved", id, solution} | {type: "progress", id, stage, ...}
//      | {type: "error", id, message}
import { solverByName } from "./js/solvers.js";

let ortBase = null;
let urls = {};
let ort = null;
const sessions = {};
const cancelled = new Set();

async function session(name) {
  if (!urls[name]) throw new Error(`the ${name} graph is not available`);
  if (!ort) {
    ort = await import(ortBase + "ort.wasm.min.mjs");
    ort.env.wasm.wasmPaths = ortBase;
    ort.env.wasm.numThreads = 1;
  }
  if (!sessions[name]) {
    sessions[name] = ort.InferenceSession.create(urls[name], { executionProviders: ["wasm"] });
    sessions[name].catch(() => delete sessions[name]);
  }
  return sessions[name];
}

function tensor(v) {
  if (v.dtype === "float32") return new ort.Tensor("float32", Float32Array.from(v.data), v.shape);
  if (v.dtype === "bool") return new ort.Tensor("bool", Uint8Array.from(v.data), v.shape);
  if (v.dtype === "int64") return new ort.Tensor("int64", BigInt64Array.from(v.data, (x) => BigInt(Math.round(x))), v.shape);
  return new ort.Tensor("float64", Float64Array.from(v.data), v.shape);
}

// graph names: "tl-layer" and "tlm-s1".."tlm-s3"
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
      ortBase = msg.ortBase;
      urls = msg.models || {};
      self.postMessage({ type: "ready" });
      return;
    }
    if (msg.type === "cancel") {
      cancelled.add(msg.id);
      return;
    }
    if (msg.type === "solve") {
      const solver = solverByName(msg.solver);
      const post = (p) => self.postMessage({ type: "progress", id: msg.id, ...p });
      const solution = await solver.solve(msg.problem, {
        // the first ONNX solve loads the runtime and the graph: say so
        run: async (name, feeds) => {
          if (!sessions[name]) post({ stage: `loading the ${name} graph` });
          const out = await run(name, feeds);
          return out;
        },
        progress: post,
        cancelled: () => cancelled.has(msg.id),
      });
      self.postMessage({ type: "solved", id: msg.id, solution });
    }
  } catch (e) {
    self.postMessage({ type: "error", id: msg.id, message: String(e && e.message ? e.message : e) });
  }
};
