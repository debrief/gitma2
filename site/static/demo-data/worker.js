// The demonstrator's solver worker (spec 035 FR-023), a module worker. JavaScript solvers run
// at once; ONNX solvers load ONNX Runtime Web (WASM, one thread) on first use. The page posts
// one request per recompute and discards any result older than its latest request.
//
// In:  {type: "init", ortBase, models: {"tl-layer", "tlm-s1", "tlm-s2", "tlm-s3", "c-layer"}}  (URLs)
//      {type: "solve", id, solver, splitter, problem}
//      {type: "compare", id, solver, splitters: [names], problem}  (spec 036)
//      {type: "cancel", id}
// Out: {type: "ready"} | {type: "solved", id, solution} | {type: "progress", id, stage, ...}
//      | {type: "compared-one", id, splitter, solution} | {type: "compared", id}
//      | {type: "error", id, message}
//
// Spec 036: a solver that accepts knots first runs the leg splitter; only the "truth" splitter is
// given the problem's true manoeuvre spans.
import { solverByName } from "./js/solvers.js";
import { splitterByName } from "./js/splitters.js";

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

// graph names: "tl-layer", "tlm-s1".."tlm-s3" and "c-layer" (spec 021's layer at confirmation's settings)
async function run(name, feeds) {
  const s = await session(name);
  const f = {};
  for (const [k, v] of Object.entries(feeds)) f[k] = tensor(v);
  const out = await s.run(f);
  const o = {};
  for (const [k, t] of Object.entries(out)) o[k] = Float64Array.from(t.data, Number);
  return o;
}

function context(id, post) {
  return {
    // the first ONNX solve loads the runtime and the graph: say so
    run: async (name, feeds) => {
      if (!sessions[name]) post({ stage: `loading the ${name} graph` });
      return run(name, feeds);
    },
    progress: post,
    cancelled: () => cancelled.has(id),
  };
}

async function splitAndSolve(solverName, splitterName, problem, ctx) {
  const solver = solverByName(solverName);
  if (!solver.info.accepts_knots) return solver.solve(problem, ctx);
  const splitter = splitterByName(splitterName);
  const given = splitter.info.told_truth ? problem : { ...problem, knots: [] };
  const split = await splitter.split(given, ctx);
  const solution = await solver.solve({ ...problem, knots: split.spans }, ctx);
  return { ...solution, splitter: splitter.info.name, splitter_spans: split.spans, splitter_runtime_ms: split.runtime_ms, splitter_message: split.message };
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
      const post = (p) => self.postMessage({ type: "progress", id: msg.id, ...p });
      const solution = await splitAndSolve(msg.solver, msg.splitter, msg.problem, context(msg.id, post));
      self.postMessage({ type: "solved", id: msg.id, solution });
    }
    if (msg.type === "compare") {
      for (const name of msg.splitters) {
        if (cancelled.has(msg.id)) throw new Error("cancelled");
        const post = (p) => self.postMessage({ type: "progress", id: msg.id, splitter: name, ...p });
        post({ stage: `splitter ${name}` });
        let solution;
        try {
          solution = await splitAndSolve(msg.solver, name, msg.problem, context(msg.id, post));
        } catch (e) {
          if (cancelled.has(msg.id)) throw e;
          solution = { solver: msg.solver, solver_version: "", status: "failed", message: String(e && e.message ? e.message : e), runtime_ms: 0, splitter: name };
        }
        self.postMessage({ type: "compared-one", id: msg.id, splitter: name, solution });
      }
      self.postMessage({ type: "compared", id: msg.id });
    }
  } catch (e) {
    self.postMessage({ type: "error", id: msg.id, message: String(e && e.message ? e.message : e) });
  }
};
