\# WASMBOX



WASMBOX — A secure, lightweight WebAssembly-based sandbox for executing untrusted Python plugins in a multi-tenant SaaS environment. Uses Wasmtime for isolated execution, strict resource limits, capability-based host functions, and a React + Monaco developer portal.



\# Compiler Development Status



\## Issue #2 — WASM Compilation Engine



The Python → WebAssembly compilation engine for WASMBOX has been implemented.



\### Completed



\* Python source validation

\* Python syntax error detection

\* MicroPython WASI toolchain

\* Python → WASM compilation pipeline

\* `CompilerService`

\* Structured compilation errors

\* Standalone compiler CLI

\* Valid and invalid Python examples

\* Automated tests

\* Known-good WASM artifact

\* WASM toolchain documentation



\### Verification



```text

pytest -q

7 passed

```



A valid Python program has been successfully compiled into:



```text

artifacts/hello.wasm

```



The compiler can be invoked independently from the frontend using the CLI.



\### Integration



The compiler produces the WASM artifact that will be consumed by the higher-level WASMBOX execution pipeline.



Integration with the orchestrator will be performed after the compiler interface is approved according to the project architecture and API contracts.



\## Compiler Usage



\### Compile Python to WASM



From the WASMBOX repository root:



```powershell

python -m compiler.cli examples\\hello.py --output artifacts\\hello.wasm

```



Expected output:



```text

Compilation successful: artifacts/hello.wasm

```



\### Compile Invalid Python



```powershell

python -m compiler.cli examples\\invalid.py --output artifacts\\invalid.wasm

```



The compiler returns a structured compilation error and does not generate a WASM artifact.



\### Run Tests



```powershell

pytest -q

```



Current verified result:



```text

7 passed

```



For complete WASM/MicroPython toolchain setup, see:



```text

docs/wasm-toolchain.md

```



