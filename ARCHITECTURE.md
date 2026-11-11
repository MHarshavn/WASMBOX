# WASMBOX Architecture

## Target architecture

```text
React + Monaco Portal
        |
        v
     FastAPI API
        |
        v
   Orchestrator
   /     |      \
  v      v       v
Compiler Policy  Sandbox adapter
  |              |
  v              v
.mpy artifact  Shared MicroPython WebAssembly runtime
        \       /
          Metrics + ExecutionResult
```

WASMBOX separates HTTP validation, compilation, policy, and execution. The API
does not evaluate source or load a runtime. The orchestrator stores tenant-owned
plugin/execution records, validates limits and capabilities, then delegates a
bytecode artifact to a sandbox adapter.

## Current implementation

The current compiler produces MicroPython `.mpy` bytecode. The current adapter
executes it with the checked-in Emscripten MicroPython runtime in a separately
spawned Node process using a restrictive Node permission configuration. This is
an Emscripten prototype, **not** Wasmtime and not a plugin-specific `.wasm`
artifact. `EmscriptenMicroPythonSandbox` is intentionally isolated behind the
orchestrator boundary so a future Wasmtime/WASI adapter can replace it without
altering API paths or JSON models.

## Lifecycle

```text
CREATED -> COMPILING -> READY -> RUNNING -> SUCCESS
```

Failure states are `COMPILATION_FAILED`, `EXECUTION_FAILED`, `TIMEOUT`,
`MEMORY_LIMIT`, `INSTRUCTION_LIMIT`, `PERMISSION_DENIED`, and `SANDBOX_ERROR`.
The implementation uses these exact state names.

## Security boundaries

- `X-Tenant-ID` scopes all in-memory plugin and execution records for the
  prototype; production must derive tenant identity from authentication.
- Capabilities deny by default. No host function is enabled today, so any
  requested capability is rejected.
- The API never calls Python `exec()` on plugin source.
- The adapter accepts bytecode only, uses the Emscripten in-memory filesystem,
  and does not grant Node filesystem-write, network, child-process, worker,
  addon, WASI, or host-function permissions.
- Wall-clock timeout is enforced by the parent process. Hard total-memory and
  instruction limits remain unsupported by the current shared runtime.

See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for the
tested status and limitations.
