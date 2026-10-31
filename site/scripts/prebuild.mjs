// Regenerate the data dictionary from the schema before every site build.
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
execFileSync("uv", ["run", "--frozen", "python", "scripts/data_dictionary.py"], {
  cwd: root,
  stdio: "inherit",
});
