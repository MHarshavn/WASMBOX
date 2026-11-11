import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const directory = dirname(fileURLToPath(import.meta.url));
const artifact = readFileSync(join(directory, "test_plugin.mpy")).toString("base64");
const input = Buffer.from("{}", "utf8").toString("base64");
const result = spawnSync(
  process.execPath,
  ["--permission", `--allow-fs-read=${directory}`, "--max-old-space-size=128", join(directory, "emscripten_runner.mjs"), artifact, input, "8388608"],
  { encoding: "utf8", cwd: directory },
);

assert.equal(result.status, 0, result.stderr);
const payload = JSON.parse(result.stdout);
assert.equal(payload.status, "SUCCESS");
assert.match(payload.stdout, /Hello from WASMBOX compiler test/);
assert.equal(payload.stderr, "");
assert.ok(payload.rss_bytes > 0);
console.log("Emscripten sandbox runner test passed");
