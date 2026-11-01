// Browser (WASM) leg of the export conformance check: serves the exported model and the golden
// batch to a page running onnxruntime-web in Chromium (Playwright), compares the outputs with the
// torch reference, and writes results.json alongside the Python leg's numbers.
//
// Usage: node wasm_leg.mjs [--dir <export dir>] [--out results.json]
import { createServer } from "node:http";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join, extname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const arg = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : dflt;
};
const dir = arg("--dir", join(here, "export", "f64"));
const outPath = arg("--out", join(here, "results.json"));
const TOL = 1e-5;

// The export writes raw little-endian arrays and a manifest of shapes and dtypes.
const manifest = JSON.parse(readFileSync(join(dir, "manifest.json"), "utf8"));
function readBin(prefix, name, spec) {
  const buf = readFileSync(join(dir, `${prefix}_${name}.bin`));
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  let data;
  if (spec.dtype === "float64") data = Array.from(new Float64Array(ab));
  else if (spec.dtype === "float32") data = Array.from(new Float32Array(ab));
  else if (spec.dtype === "int64") data = Array.from(new BigInt64Array(ab)).map(String);
  else throw new Error(`unsupported dtype ${spec.dtype}`);
  return { descr: spec.dtype, shape: spec.shape, data };
}
const inputs = Object.fromEntries(Object.entries(manifest.inputs).map(([n, s]) => [n, readBin("in", n, s)]));
// Reference: torch's outputs (out_*.bin); the Python onnxruntime outputs (ort_*.bin) beside it.
const expected = Object.fromEntries(Object.entries(manifest.outputs).map(([n, s]) => [n, readBin("out", n, s)]));
const ortRef = Object.fromEntries(Object.entries(manifest.outputs).map(([n, s]) => [n, readBin("ort", n, s)]));
const model = readFileSync(join(dir, "toy.onnx"));
const ortDir = join(here, "node_modules", "onnxruntime-web", "dist");

const server = createServer((req, res) => {
  const url = req.url.split("?")[0];
  if (url === "/") {
    res.setHeader("Content-Type", "text/html");
    res.end(`<!doctype html><html><body><script src="/ort/ort.wasm.min.js"></script><script>window.ortReady = true;</script></body></html>`);
    return;
  }
  if (url.startsWith("/ort/")) {
    const f = join(ortDir, url.slice(5));
    if (!existsSync(f)) {
      res.statusCode = 404;
      res.end();
      return;
    }
    const types = { ".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm" };
    res.setHeader("Content-Type", types[extname(f)] || "application/octet-stream");
    res.end(readFileSync(f));
    return;
  }
  if (url === "/toy.onnx") {
    res.setHeader("Content-Type", "application/octet-stream");
    res.end(model);
    return;
  }
  if (url === "/inputs.json") {
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(inputs));
    return;
  }
  res.statusCode = 404;
  res.end();
});

await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port;
const browser = await chromium.launch({
  args: ["--no-sandbox"],
  ...(process.env.PW_EXECUTABLE ? { executablePath: process.env.PW_EXECUTABLE } : {}),
});
let results;
try {
  const page = await browser.newPage();
  page.on("console", (m) => console.error("[browser]", m.text()));
  await page.goto(`http://127.0.0.1:${port}/`);
  await page.waitForFunction(() => window.ortReady === true);
  results = await page.evaluate(async () => {
    ort.env.wasm.wasmPaths = "/ort/";
    ort.env.wasm.numThreads = 1;
    const inputs = await (await fetch("/inputs.json")).json();
    const session = await ort.InferenceSession.create("/toy.onnx", { executionProviders: ["wasm"] });
    const feeds = {};
    for (const [name, v] of Object.entries(inputs)) {
      if (v.descr === "int64") feeds[name] = new ort.Tensor("int64", BigInt64Array.from(v.data.map(BigInt)), v.shape);
      else if (v.descr === "float64") feeds[name] = new ort.Tensor("float64", Float64Array.from(v.data), v.shape);
      else feeds[name] = new ort.Tensor("float32", Float32Array.from(v.data), v.shape);
    }
    const t0 = performance.now();
    const out = await session.run(feeds);
    const ms = performance.now() - t0;
    const o = {};
    for (const [k, t] of Object.entries(out)) o[k] = Array.from(t.data);
    return { outputs: o, ms, userAgent: navigator.userAgent };
  });
} finally {
  await browser.close();
  server.close();
}
function maxRel(ref) {
  const out = {};
  for (const [name, exp] of Object.entries(ref)) {
    const got = results.outputs[name];
    let worst = 0;
    for (let i = 0; i < exp.data.length; i++) {
      const scale = Math.max(Math.abs(exp.data[i]), 1);
      worst = Math.max(worst, Math.abs(got[i] - exp.data[i]) / scale);
    }
    out[name] = worst;
  }
  return out;
}
const diffs = maxRel(expected);
const vsOrtPython = maxRel(ortRef);
const pythonLeg = existsSync(join(dir, "python_leg.json")) ? JSON.parse(readFileSync(join(dir, "python_leg.json"), "utf8")) : null;
const prior = existsSync(outPath) ? JSON.parse(readFileSync(outPath, "utf8")) : {};
const pythonF64 = pythonLeg;
const report = {
  ...prior,
  python: pythonF64,
  wasm: {
    max_rel_diff: diffs,
    reference: "torch (float64)",
    vs_onnxruntime_python: vsOrtPython,
    ms: results.ms,
    tol: TOL,
    onnx_sha256: createHash("sha256").update(model).digest("hex"),
    runtime: `onnxruntime-web ${JSON.parse(readFileSync(join(here, "node_modules", "onnxruntime-web", "package.json"), "utf8")).version}`,
    browser: results.userAgent,
  },
};
writeFileSync(outPath, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify({ wasm: diffs, ms: results.ms }));
const bad = Object.entries(diffs).filter(([, v]) => v > TOL);
if (bad.length) {
  console.error(`wasm leg exceeds ${TOL}:`, bad);
  process.exit(1);
}
