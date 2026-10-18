import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadMicroPython } from "./micropython.mjs";

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const bytecodePath = path.join(currentDirectory, "test_plugin.mpy");

try {
    const mp = await loadMicroPython();
    const bytecode = fs.readFileSync(bytecodePath);

    mp.FS.writeFile("/plugin.mpy", bytecode);

    console.log("MicroPython runtime loaded");
    console.log(`Bytecode loaded: ${bytecode.length} bytes`);

    await mp.runPythonAsync("import plugin");

    console.log("Bytecode executed successfully");
} catch (error) {
    console.error("Bytecode execution failed:", error);
    process.exitCode = 1;
}
