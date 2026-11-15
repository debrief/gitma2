// The viewer's compute worker (spec 020): loads the exported E-w graph in ONNX Runtime Web
// (WASM, one thread) and runs one row at a time. The page and the CI conformance leg
// (conformance/onnx/viewer_leg.mjs) both drive the graph through this file.
//
// Messages in:  {type: "init", ortBase, modelUrl}
//               {type: "run", id, feeds: {name: {dtype, shape, data: Float64Array}}}
// Messages out: {type: "ready", loadMs} | {type: "result", id, outputs, ms} | {type: "error", id?, message}
/* global ort, importScripts */
let session = null;

self.onmessage = async (ev) => {
  const msg = ev.data;
  try {
    if (msg.type === "init") {
      importScripts(msg.ortBase + "ort.wasm.min.js");
      ort.env.wasm.wasmPaths = msg.ortBase;
      ort.env.wasm.numThreads = 1;
      const t0 = performance.now();
      session = await ort.InferenceSession.create(msg.modelUrl, { executionProviders: ["wasm"] });
      self.postMessage({ type: "ready", loadMs: performance.now() - t0 });
      return;
    }
    if (msg.type === "run") {
      const feeds = {};
      for (const [name, v] of Object.entries(msg.feeds)) {
        if (v.dtype === "int64") {
          feeds[name] = new ort.Tensor("int64", BigInt64Array.from(v.data, (x) => BigInt(Math.round(x))), v.shape);
        } else {
          feeds[name] = new ort.Tensor("float64", Float64Array.from(v.data), v.shape);
        }
      }
      const t0 = performance.now();
      const out = await session.run(feeds);
      const ms = performance.now() - t0;
      const outputs = {};
      for (const [k, t] of Object.entries(out)) outputs[k] = Float64Array.from(t.data, Number);
      self.postMessage({ type: "result", id: msg.id, outputs, ms });
    }
  } catch (e) {
    self.postMessage({ type: "error", id: msg.id, message: String(e && e.message ? e.message : e) });
  }
};
