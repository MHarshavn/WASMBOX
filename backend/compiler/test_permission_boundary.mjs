import assert from "node:assert/strict";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const directory = dirname(fileURLToPath(import.meta.url));
const probe = `
import { loadMicroPython } from ${JSON.stringify(new URL("./micropython.mjs", import.meta.url).href)};
const mp = await loadMicroPython({ stdout: () => {}, stderr: () => {} });
try {
  await mp.runPythonAsync("import js\\njs.process.getBuiltinModule('node:fs').readFileSync('README.md')");
  process.stdout.write("UNEXPECTED_HOST_READ");
} catch (error) {
  process.stdout.write("HOST_READ_DENIED");
}
`;
const result = spawnSync(
  process.execPath,
  ["--permission", `--allow-fs-read=${directory}`, "--input-type=module", "--eval", probe],
  { encoding: "utf8", cwd: directory },
);
assert.equal(result.status, 0, result.stderr);
assert.equal(result.stdout, "HOST_READ_DENIED");
console.log("Node permission boundary test passed");
