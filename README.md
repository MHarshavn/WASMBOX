# WASMBOX

WASMBOX is a multi-tenant developer portal and API for compiling supported
Python source to MicroPython bytecode (`.mpy`) and running that bytecode through
the repository's preserved Emscripten MicroPython runtime.

## Implementation status

The project now has a FastAPI API, tenant-scoped in-memory plugin/execution
records, lifecycle results, resource-policy validation, a React + Monaco portal,
and a separately spawned Emscripten execution adapter. The adapter captures
stdout/stderr, reports child-process RSS, enforces a wall-clock timeout, and
starts Node with its permission model enabled. It allows runtime-file reads only
from `backend/compiler`; filesystem writes, child processes, and network access
are not granted.

This is **not** a Wasmtime implementation and the compiler does **not** produce
a plugin-specific `.wasm` module. The compiler output is `.mpy` bytecode and the
checked-in `micropython.wasm` is a shared interpreter runtime. The stable
`wasm_artifact` response field is currently an opaque artifact reference retained
for API compatibility, not a claim about the artifact's format.

The Emscripten path is a submission prototype, not a production security
boundary. Node permissions mitigate direct host access but need independent
security review. The fixed-memory runtime prevents a true per-execution process
memory limit; see [implementation status](docs/IMPLEMENTATION_STATUS.md).

## Run locally

Prerequisites: a normal CPython 3.11+ installation, Node.js 18.3+ (Node 24 was
used for the permission-boundary test), and Docker Desktop plus the existing
MicroPython compiler toolchain when compiling new plugins.

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.api.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The backend requires `X-Tenant-ID` on every API
request; the portal defaults it to `demo-tenant`. This is the minimal explicit
tenant context required because the published JSON request bodies contain no
tenant field. A real deployment must derive this value from authenticated
identity, not trust a caller-supplied header.

## API

The endpoint paths and JSON bodies remain in
[API_CONTRACTS.md](docs/api/API_CONTRACTS.md):

- `POST /api/v1/plugins/compile`
- `POST /api/v1/plugins/execute`
- `GET /api/v1/executions/{execution_id}`
- `GET /metrics` (tenant-scoped, in-memory record counts)

Compilation creates an in-memory, tenant-owned record only after `mpy-cross`
returns a non-empty `.mpy` artifact. Execution returns `RUNNING` and then the
result endpoint returns the standard lifecycle state, output, timing, RSS metric,
and termination reason.

## Test commands

## Test commands

Run from the repository root:

```powershell
python -m pytest backend/tests -v
python -m unittest backend.compiler.test_micropython_compiler -v

node backend/compiler/test_bytecode.mjs
node backend/compiler/test_emscripten_runner.mjs
node backend/compiler/test_permission_boundary.mjs

npm run build --prefix frontend

## Security and limits

- No host functions are currently implemented; every requested capability fails
  closed with `PERMISSION_DENIED`.
- Plugin/execution IDs are tenant-checked on every read and execution request.
- The API never uses Python `exec()` or evaluates plugin source.
- The runner accepts only compiled bytecode over base64 and writes it solely to
  Emscripten's in-memory virtual filesystem.
- Configured limits allow 1–128 MB, 1–5000 ms, and 1–1,000,000 instructions.
  Only wall-clock timeout is fully enforced today. The adapter constrains V8's
  old-space value and MicroPython's heap where possible, but the fixed shared
  runtime cannot enforce an end-to-end memory ceiling. Instruction accounting is
  validated but unsupported by the selected runtime.

See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for the
honest feature matrix and next steps.
