// Internal protocol runner. It accepts bytecode only, never API source text.
import { loadMicroPython } from "./micropython.mjs";

const [artifactBase64, inputBase64, heapSize] = process.argv.slice(2);
let stdout = "";
let stderr = "";

function respond(payload, exitCode = 0) {
  process.stdout.write(JSON.stringify({
    stdout,
    stderr,
    rss_bytes: process.memoryUsage().rss,
    ...payload,
  }));
  process.exitCode = exitCode;
}

try {
  if (!artifactBase64 || !inputBase64 || !heapSize) {
    throw new Error("Missing sandbox runner arguments.");
  }
  const artifact = Buffer.from(artifactBase64, "base64");
  const inputJson = Buffer.from(inputBase64, "base64").toString("utf8");
  JSON.parse(inputJson);
  const mp = await loadMicroPython({
    heapsize: Number.parseInt(heapSize, 10),
    stdout: (line) => { stdout += `${line}\n`; },
    stderr: (line) => { stderr += `${line}\n`; },
  });
  mp.FS.writeFile("/plugin.mpy", artifact);
  const bootstrap = `import json\nWASMBOX_INPUT = json.loads(${JSON.stringify(inputJson)})\nimport plugin`;
  await mp.runPythonAsync(bootstrap);
  respond({ status: "SUCCESS" });
} catch (error) {
  stderr += `${error instanceof Error ? error.stack || error.message : String(error)}\n`;
  respond({ status: "EXECUTION_FAILED" }, 1);
}
