# WASMBOX implementation status

## Demonstrated components

| Component | Status | Notes |
|---|---|---|
| MicroPython compilation | Conditional | `MicroPythonCompiler` invokes the existing `mpy-cross` Docker path and returns `.mpy`, never renamed bytecode. It needs Docker Desktop and the existing local toolchain. |
| Shared runtime | Tested | The preserved Emscripten MicroPython runtime loads and executes `test_plugin.mpy`. |
| API | Implemented | FastAPI routes match the published paths and bodies; validation and domain errors use the standard error envelope. |
| Lifecycle and metrics | Implemented | Plugin records become ready; execution records start as `RUNNING`, then store status, output, duration, RSS, and termination reason. |
| Tenant isolation | Prototype | Records are in-memory and every plugin/execution lookup checks `X-Tenant-ID`. Deployment authentication remains future work. |
| Portal | Implemented | React, Vite, Monaco, compile/run controls, output panes, metrics, and error display. |
| Emscripten execution adapter | Tested | A child Node process uses the existing shared runtime and only receives bytecode and JSON input. |

## Security posture

The adapter invokes Node with `--permission` and a read allow-list limited to
`backend/compiler`. It does not grant filesystem write, network, child-process,
worker, addon, or WASI permissions. The test `test_permission_boundary.mjs`
successfully attempts a MicroPython-to-JavaScript filesystem read of repository
`README.md`; Node denies it because that file is outside the allow-list.

This check is evidence for the configured boundary, not proof of isolation.
The Emscripten runtime exposes a JavaScript bridge and Node permissions are not
a substitute for a full Wasmtime/WASI security review. The adapter must not be
presented as Wasmtime execution or used for production multi-tenant workloads.

## Limits and metrics

`timeout_ms` is enforced by killing the child process after the configured time
plus a small startup allowance. The request policy supports 1–128 MB, 1–5000 ms,
and 1–1,000,000 instructions, retaining the API contract's 128 MB/5000 ms
examples. The separate project examples of 10 MB/50 ms remain valid requests.

The shared runtime has a fixed approximately 16 MiB WebAssembly linear memory.
Passing a 128 MiB MicroPython heap makes it abort, so the adapter caps the
internal MicroPython heap at 8 MiB and reports actual Node child RSS. This is
measurement, not a hard process-memory cap. V8 old-space is configured from the
request, but RSS includes runtime overhead and may exceed it. Instruction limits
are validated but cannot be counted or interrupted by this runtime.

## Experimental WASI port

A separate MicroPython WASI port has been added under
`tools/micropython/source/ports/wasmbox-wasi`.

The port successfully compiles into `micropython.wasm` using the
WASI SDK Docker image. However, the generated module currently uses
legacy WebAssembly exception instructions that Wasmtime 50.0.1
rejects during module compilation.

Therefore, MicroPython execution through this WASI port is not
currently supported. The port is experimental and is not connected
to the main execution pipeline.

A separate C-based WASI smoke test successfully executed through
the Wasmtime sandbox. This validates basic WASI module execution,
not MicroPython execution.

## Not completed

1. Plugin-specific WebAssembly generation.
2. Real Wasmtime execution of a generated plugin module.
3. Production authentication and durable tenant-scoped storage.
4. Capability-backed host functions (the safe current behavior is an empty
   supported list).
5. Runtime instruction metering and hard total-memory enforcement.
6. Persistent/background execution queue and result retention policy.

## Recommended next steps

1. Obtain a MicroPython runtime compiled for WASI without the known Unix-port
   signal dependency, or a dedicated runtime with fuel/memory support.
2. Replace `EmscriptenMicroPythonSandbox` behind the existing orchestrator
   boundary with a Wasmtime adapter; leave HTTP models unchanged.
3. Add authenticated tenant identity and transactional persistent storage.
4. Implement and test narrowly scoped host functions before permitting any
   capability names.
