// Regenerate the data dictionary from the schema before every site build.
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
execFileSync("uv", ["run", "--frozen", "python", "scripts/data_dictionary.py"], {
  cwd: root,
  stdio: "inherit",
});

// Spec 020: the viewer's runtime, copied from the pinned onnxruntime-web (the version the
// conformance legs use) so the page fetches nothing from outside the site. Generated, not
// committed (static/ort/ is gitignored).
import { copyFileSync, mkdirSync } from "node:fs";
const ortDist = join(root, "site", "node_modules", "onnxruntime-web", "dist");
const ortOut = join(root, "site", "static", "ort");
mkdirSync(ortOut, { recursive: true });
for (const f of ["ort.wasm.min.mjs", "ort-wasm-simd-threaded.wasm", "ort-wasm-simd-threaded.mjs"]) {
  copyFileSync(join(ortDist, f), join(ortOut, f));
}
