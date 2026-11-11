# WASMBOX

WASMBOX is a prototype platform for compiling, running, and inspecting untrusted Python plugins through a developer portal and a multi-tenant API. It combines a FastAPI backend, a MicroPython bytecode compiler, two distinct execution adapters, resource-policy validation, deny-by-default capability checks, and a React + TypeScript + Monaco developer portal.

> **Implementation accuracy:** The current MicroPython compiler produces `.mpy` bytecode, not a standalone `.wasm` module for each plugin. The `.mpy` artifact runs in the shared Emscripten-compiled MicroPython runtime. Separately, the project has a Wasmtime adapter for already-compiled WASI WebAssembly modules. These are two different execution paths. The complete Python-source-to-WASI-`.wasm` compilation pipeline is not yet implemented.

## Contents

- [Project goals](#project-goals)
- [Features](#features)
- [Architecture and execution flows](#architecture-and-execution-flows)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Getting started](#getting-started)
- [API reference](#api-reference)
- [Execution states and errors](#execution-states-and-errors)
- [Resource policies and capabilities](#resource-policies-and-capabilities)
- [Security model and limitations](#security-model-and-limitations)
- [Developer portal guide](#developer-portal-guide)
- [Testing and validation](#testing-and-validation)
- [Current implementation status](#current-implementation-status)
- [Team workflow and responsibilities](#team-workflow-and-responsibilities)
- [Contributing](#contributing)
- [Project documentation](#project-documentation)

## Project goals

Running user-supplied Python directly inside an API process is unsafe. Untrusted code can attempt unauthorized filesystem or network access, consume excessive CPU or memory, crash a service, or access another tenant's data.

WASMBOX is designed to provide a controlled plugin execution workflow:

1. A developer writes Python in the browser-based portal.
2. The portal submits the source to the backend compile API.
3. The compiler validates the source and creates a runtime-compatible artifact.
4. The developer submits an execution request with JSON input, resource limits, and requested capabilities.
5. The orchestrator validates the request and routes the artifact to the matching runtime adapter.
6. The runtime executes the artifact under its configured restrictions.
7. The backend records the execution state, output, duration, resource measurements where available, and termination reason.
8. The portal retrieves and displays the result.

The project emphasizes explicit module boundaries, structured errors, tenant-scoped records, deny-by-default capabilities, resource controls, and testable runtime behavior.

## Features

### Backend and API

- FastAPI application with request validation and structured error responses.
- Compile, execute, execution-result, and metrics endpoints.
- Orchestrator coordinating compilation, policy validation, artifact routing, and result collection.
- Tenant-scoped plugin and execution records using a required `X-Tenant-ID` request header.
- In-memory repository for the current prototype.
- Standardized execution states, output fields, and termination reasons.

### Compiler foundation

- `MicroPythonCompiler` validates non-empty Python source and parses its syntax before invoking the compiler toolchain.
- Uses the MicroPython `mpy-cross` compiler to produce genuine `.mpy` bytecode.
- Compilation runs through the repository's Docker-based toolchain workflow.
- Returns structured compilation failures for invalid source, missing compiler artifacts, Docker failures, and compilation timeouts.
- Does not evaluate submitted plugin source using the backend's host Python interpreter.

### Execution adapters

WASMBOX routes artifacts according to their actual format:

| Artifact format | Runtime adapter | What it executes |
|---|---|---|
| `mpy` | Emscripten MicroPython adapter | MicroPython bytecode using the shared Emscripten MicroPython runtime |
| `wasm` | Wasmtime adapter | A precompiled WASI Preview 1 WebAssembly command module |

The router rejects unknown artifact formats rather than guessing which runtime should load them.

**Emscripten MicroPython path**

- Starts a separate Node.js process to run the shared MicroPython WebAssembly runtime.
- Passes compiled bytecode and JSON input to the runner.
- Uses Node's permission model with a read allow-list for the runtime directory.
- Captures standard output, standard error, execution duration, and child-process RSS.
- Applies a wall-clock timeout by terminating the child process.
- Rejects non-empty capability requests because host functions are not implemented.

**Wasmtime WASI path**

- Loads a genuine WASI-compatible WebAssembly module through the Python Wasmtime API.
- Configures WASI standard input, standard output, and standard error using temporary files.
- Does not preopen host directories or inherit arbitrary host environment variables or arguments.
- Applies WebAssembly linear-memory limits, fuel accounting, and epoch-based timeout interruption.
- Rejects non-empty capability requests because no host capabilities are currently enabled.
- Requires a WASI command module with an exported `_start` function.

### Developer portal

- React and TypeScript single-page application.
- Monaco editor with a basic-editor fallback.
- Compile and execute workflow connected to the API contract.
- JSON input and configurable execution limits.
- Plugin draft save/load/delete in browser-local storage.
- Execution status, stdout, stderr, error details, duration, and memory display.
- Simulated webhook input for testing event-style payloads.
- Responsive layout, accessible status/error messaging, and frontend tests.
- Python source is sent to the backend; the browser does not evaluate plugin code.

### Security and policy foundations

- Deny-by-default capability validation.
- Resource-policy validation before execution.
- Tenant checks on plugin and execution record access.
- Runtime adapters return normalized execution results.
- Tests cover invalid modules, fuel exhaustion, timeout during initialization, tenant access boundaries, and denied capabilities.

## Architecture and execution flows

### High-level system architecture

```text
+---------------------------------------------+
|       React + TypeScript Developer Portal   |
|  Monaco Editor | Plugin Library | Results   |
+----------------------+----------------------+
                       |
                       | HTTP / JSON
                       v
+---------------------------------------------+
|                 FastAPI API                 |
| Compile | Execute | Result | Metrics        |
| Request validation | Tenant context         |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
|                 Orchestrator                |
| Repository | Resource Policy | Capabilities |
| Execution lifecycle | Artifact routing      |
+----------------------+----------------------+
                       |
             +---------+---------+
             |                   |
             v                   v
+----------------------+  +----------------------+
| MicroPython Compiler |  | Existing WASM input  |
| Python -> .mpy       |  | format: .wasm        |
+----------+-----------+  +----------+-----------+
           |                         |
           v                         v
+----------------------+  +----------------------+
| Emscripten MicroPython| | Wasmtime WASI        |
| shared .wasm runtime  | | Preview 1 adapter    |
| executes .mpy         | | executes .wasm       |
+----------+-----------+  +----------+-----------+
           |                         |
           +------------+------------+
                        |
                        v
+---------------------------------------------+
| Normalized execution result                  |
| status | stdout | stderr | duration | limits |
+----------------------+----------------------+
                       |
                       v
              Developer Portal
```

The diagram shows the two runtime routes. It does **not** mean the MicroPython compiler currently emits WASI modules: it emits `.mpy` bytecode for the Emscripten runtime. A plugin-specific Python-to-WASI compiler remains future work.

### MicroPython bytecode execution flow

1. The portal calls `POST /api/v1/plugins/compile`.
2. The API validates the request and tenant context.
3. The orchestrator calls `MicroPythonCompiler`.
4. The compiler checks source syntax and invokes `mpy-cross` through Docker.
5. The resulting `.mpy` bytes and their `mpy` artifact format are stored in the in-memory repository.
6. The portal submits `POST /api/v1/plugins/execute`.
7. The orchestrator validates limits and requested capabilities, creates an execution record, and schedules execution.
8. The router selects `EmscriptenMicroPythonSandbox` for the `mpy` artifact.
9. A separate Node process runs the shared MicroPython runtime and returns the execution payload.
10. The API exposes the final execution record to the portal.

### WASI WebAssembly execution flow

1. A caller supplies an already compiled WASI-compatible `.wasm` artifact to the Wasmtime adapter through the sandbox routing layer.
2. The router selects `WasmtimeSandbox` for the `wasm` artifact format.
3. Wasmtime validates and instantiates the module with a WASI context that has standard streams but no preopened host directories.
4. Fuel, WebAssembly linear-memory limits, and an epoch timeout are configured.
5. The module's `_start` command entry point is invoked.
6. The adapter captures output and returns a normalized result.

The current MicroPython compiler does not generate the input artifact for this WASI path.

## Technology stack

| Layer | Technologies |
|---|---|
| Backend language | Python |
| API framework | FastAPI, Pydantic |
| MicroPython compiler | MicroPython `mpy-cross` |
| Bytecode runtime | MicroPython compiled to WebAssembly with Emscripten |
| Bytecode runner | Node.js permission model |
| WASI runtime | Wasmtime Python bindings, WASI Preview 1 |
| Frontend | React 19, TypeScript, Vite |
| Code editor | Monaco Editor |
| Frontend testing | Vitest, Testing Library, Playwright configuration |
| Backend testing | pytest, unittest |
| Tooling | Docker Desktop, Git, GitHub, npm |

## Repository structure

The main directories and their responsibilities are:

```text
WASMBOX/
├── .github/
│   └── workflows/
│       └── frontend.yml              # Frontend CI workflow
├── backend/
│   ├── api/
│   │   └── main.py                   # FastAPI routes and request models
│   ├── compiler/
│   │   ├── compiler.py               # Compiler interface
│   │   ├── micropython_compiler.py   # Python source -> .mpy
│   │   ├── emscripten_runner.mjs     # Node/Emscripten runtime runner
│   │   └── test_*.mjs                # Runtime smoke/security tests
│   ├── core/
│   │   ├── errors.py                 # Domain errors
│   │   └── models.py                 # Plugin, execution, policy models
│   ├── sandbox/
│   │   ├── models.py                 # Shared SandboxResult
│   │   ├── router.py                 # Artifact-format dispatch
│   │   ├── emscripten_sandbox.py     # .mpy execution adapter
│   │   └── wasmtime_sandbox.py       # WASI .wasm execution adapter
│   ├── services/
│   │   ├── orchestrator.py           # Execution coordination
│   │   ├── repository.py             # In-memory tenant-scoped records
│   │   ├── resources.py              # Resource policy validation
│   │   └── capabilities.py           # Deny-by-default policy
│   ├── tests/                        # Backend API/service/sandbox tests
│   └── requirements.txt              # Backend Python dependencies
├── docs/
│   ├── architecture/                 # Architecture documentation
│   ├── api/
│   │   └── API_CONTRACTS.md          # HTTP/API contracts
│   ├── compiler/
│   │   └── MICROPYTHON_TOOLCHAIN.md  # Compiler/runtime setup
│   ├── security/                     # Security model and contracts
│   └── IMPLEMENTATION_STATUS.md      # Demonstrated behavior and limitations
├── frontend/
│   ├── src/
│   │   ├── api/                      # API client, types, polling
│   │   ├── components/               # Editor, settings, output, metrics
│   │   ├── hooks/                    # Execution workflow
│   │   ├── utils/                    # Validation and local plugin storage
│   │   ├── App.tsx                   # Main portal
│   │   └── main.tsx                  # Frontend entry point
│   ├── tests/e2e/                    # Playwright browser tests
│   ├── package.json
│   └── README.md                     # Portal-specific setup and details
├── src/
│   └── wasmbox/sandbox/              # Additional sandbox policy/runtime package
├── tests/
│   └── security/                     # Security policy/runtime tests
└── tools/
    └── micropython/source/           # Local MicroPython source checkout
```

The MicroPython source checkout and generated toolchain artifacts are not committed as ordinary application source. Follow the toolchain guide to obtain the expected revision and build prerequisites.

## Requirements

- Git.
- Python compatible with the backend dependencies (Python 3.13 was used for the recorded local validation).
- Node.js 22.12 or newer (Node.js 24 recommended for the portal).
- npm.
- Docker Desktop with its Linux engine running for the Docker-based MicroPython compiler workflow.
- The MicroPython source checkout and built `mpy-cross` artifact described in the [toolchain guide](docs/compiler/MICROPYTHON_TOOLCHAIN.md).

The Wasmtime adapter uses the pinned Python package in `backend/requirements.txt`. A host `wasmtime` command-line executable is not required by the Python adapter.

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/MHarshavn/WASMBOX.git
cd WASMBOX
```

### 2. Install backend dependencies

From the repository root:

```bash
python -m pip install -r backend/requirements.txt
```

### 3. Prepare the MicroPython toolchain

Follow [MICROPYTHON_TOOLCHAIN.md](docs/compiler/MICROPYTHON_TOOLCHAIN.md). The compiler expects the MicroPython source checkout and the built `mpy-cross` binary at the documented repository-relative path. Docker Desktop must be running because the compiler invokes the configured Docker image.

The checked-in Emscripten runtime artifacts are used by the bytecode runner. The local MicroPython source tree is not downloaded automatically by the API.

### 4. Start the backend

From the repository root:

```bash
python -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`. FastAPI's interactive API documentation is available at `http://127.0.0.1:8000/docs`.

Every API operation requires a valid `X-Tenant-ID` header in the current prototype. This header is a tenant-context mechanism only; it is not authentication.

### 5. Start the developer portal

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, normally `http://127.0.0.1:5173`. The development server proxies `/api` to `http://127.0.0.1:8000`. See [frontend/README.md](frontend/README.md) for environment configuration, browser testing, deployment, and portal behavior.

### 6. Run a compiler smoke test

With Docker and the MicroPython toolchain prepared:

```bash
python -m unittest backend.compiler.test_micropython_compiler -v
node backend/compiler/test_bytecode.mjs
```

These verify the compiler foundation and the shared runtime bytecode smoke test. They do not prove a complete Python-to-WASI compilation path.

## API reference

The published API contract is documented in [docs/api/API_CONTRACTS.md](docs/api/API_CONTRACTS.md).

All endpoints below require the `X-Tenant-ID` header in the current implementation.

### Compile a plugin

`POST /api/v1/plugins/compile`

Example request:

```json
{
  "plugin_name": "example-plugin",
  "source_code": "print('Hello WASMBOX')",
  "python_version": "3.x"
}
```

Successful response:

```json
{
  "status": "COMPILED",
  "plugin_id": "plugin-123",
  "wasm_artifact": "artifact:plugin-123"
}
```

**Important:** The `wasm_artifact` field is retained for API compatibility and is an opaque artifact reference. The current MicroPython compiler stores `.mpy` bytecode for this plugin; the field does not mean that the compiler generated a plugin-specific `.wasm` module.

### Submit an execution

`POST /api/v1/plugins/execute`

Example request:

```json
{
  "plugin_id": "plugin-123",
  "input": {},
  "limits": {
    "memory_mb": 128,
    "timeout_ms": 5000,
    "instruction_limit": 1000000
  },
  "capabilities": []
}
```

The endpoint creates an execution record and schedules the execution as a background task. The initial response contains the execution identifier and `RUNNING` status:

```json
{
  "execution_id": "execution-123",
  "status": "RUNNING"
}
```

### Retrieve an execution result

`GET /api/v1/executions/{execution_id}`

The response includes the execution identifier, final/current status, stdout, stderr, execution duration, memory measurement where available, and termination reason.

### Read tenant-scoped metrics

`GET /metrics`

Returns stored plugin and execution counts for the tenant identified by `X-Tenant-ID`. These are in-memory record counts, not durable historical analytics.

## Execution states and errors

The API and sandbox use standardized statuses, including:

| Status | Meaning |
|---|---|
| `CREATED` | Record created |
| `COMPILING` | Compilation in progress where represented |
| `READY` | Plugin is compiled and stored |
| `RUNNING` | Execution has been submitted |
| `SUCCESS` | Runtime completed successfully |
| `COMPILATION_FAILED` | Source compilation failed |
| `EXECUTION_FAILED` | Plugin execution failed |
| `TIMEOUT` | Runtime exceeded its configured time |
| `MEMORY_LIMIT` | A supported memory/resource limit was reached |
| `INSTRUCTION_LIMIT` | Wasmtime fuel was exhausted |
| `PERMISSION_DENIED` | Requested host capability was rejected |
| `SANDBOX_ERROR` | Invalid artifact or runtime infrastructure failure |

Errors use a structured response with an error code and human-readable message. Common codes include `INVALID_REQUEST`, `COMPILATION_ERROR`, `PLUGIN_NOT_FOUND`, `TENANT_ACCESS_DENIED`, `PERMISSION_DENIED`, `TIMEOUT`, `MEMORY_LIMIT`, `INSTRUCTION_LIMIT`, and `SANDBOX_ERROR`.

## Resource policies and capabilities

The backend validates the following request limits:

| Policy | Default | Allowed range |
|---|---:|---:|
| Memory request | 128 MB | 1–128 MB |
| Timeout | 5,000 ms | 1–5,000 ms |
| Instruction/fuel request | 1,000,000 | 1–1,000,000 |

How these limits are enforced depends on the runtime:

- **Wasmtime:** Applies a limit to WebAssembly linear memory, fuel accounting, and epoch-based timeout interruption.
- **Emscripten MicroPython:** Applies a child-process timeout and configures the Node/V8 heap option. The shared runtime has fixed WebAssembly memory and its internal MicroPython heap is capped at 8 MiB. Child-process RSS is measured, but the requested memory value is not a hard cap on total process RSS. Instruction counting is not enforced by this adapter.

Capabilities are deny-by-default. The current backend supports no host capabilities, so the supported capability set is empty. Non-empty capability requests are rejected. The portal's capability controls do not imply that a host function is implemented or available.

## Security model and limitations

WASMBOX treats plugin source and compiled artifacts as untrusted. The intended design is to keep the API, compiler, orchestrator, and runtime responsibilities separate and to grant host access only through explicitly reviewed capabilities.

The current implementation is a development prototype, not a production security boundary.

### Current protections

- The compiler parses source for syntax validity and invokes `mpy-cross`; it does not execute plugin source in the API's Python interpreter.
- The Emscripten runner executes in a separate Node process with a read allow-list limited to the runtime directory and without granted filesystem-write or network permissions.
- The Wasmtime adapter creates a WASI context without preopened host directories and does not inherit arbitrary host environment variables or arguments.
- The Wasmtime adapter uses fuel, linear-memory limits, and epoch interruption.
- Capability checks reject all non-empty capability requests.
- Repository lookups check tenant context to prevent cross-tenant record access within the current process.

### Known limitations

1. **No complete Python-to-WASI compiler:** The MicroPython WASI port under development is experimental. It can produce a module, but the current output uses legacy WebAssembly exception instructions rejected by Wasmtime 50.0.1. It is not integrated into the normal execution path.
2. **Two distinct runtimes:** The Emscripten adapter executes `.mpy` bytecode; the Wasmtime adapter executes precompiled WASI `.wasm` modules. The former is not Wasmtime isolation.
3. **Prototype tenant identity:** `X-Tenant-ID` is supplied by the request and is not derived from an authenticated principal. It must not be treated as authentication.
4. **In-memory persistence:** Plugin and execution records are lost when the backend process restarts. There is no durable database or background job queue.
5. **No host capabilities:** No capability-backed host functions are enabled.
6. **Emscripten memory limitations:** Child-process RSS is measured, not strictly capped by the requested memory policy. Instruction limits are validated but not metered by this adapter.
7. **Security review required:** Tests prove only the behaviors they exercise. They are not proof of comprehensive filesystem/network isolation, cross-tenant security, or resistance to all denial-of-service attacks.

See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md), [docs/security/](docs/security/), and [SECURITY.md](SECURITY.md) for the detailed security posture and remaining work.

## Developer portal guide

The portal is located in `frontend/`. It provides:

- Monaco-based Python editing with a basic editor fallback.
- Plugin name and JSON input editing.
- Compile, execute, and result-polling workflow.
- Requested memory, timeout, and instruction limits.
- stdout/stderr streams, status, termination reason, and execution metrics.
- Browser-local plugin save/load/delete.
- Simulated webhook event input.

### Browser-local plugin storage

Saved plugins are stored in the current browser profile using `localStorage`. This is not server-side persistence, is not tenant-scoped, and must not be used for secrets. The simulated webhook panel sends an event payload through the normal compile/execute flow; it does not register a real webhook listener.

The portal's **Stop waiting** action aborts browser requests. It does not guarantee termination of an execution that has already started on the backend. See [frontend/README.md](frontend/README.md) for the complete portal workflow, environment variables, and deployment notes.

## Testing and validation

Run the backend tests from the repository root:

```bash
python -m pytest backend/tests -v
python -m unittest backend.compiler.test_micropython_compiler -v
```

Run the runtime smoke/security checks:

```bash
node backend/compiler/test_bytecode.mjs
node backend/compiler/test_emscripten_runner.mjs
node backend/compiler/test_permission_boundary.mjs
```

Run frontend checks from the repository root:

```bash
npm test --prefix frontend
npm run build --prefix frontend
```

Additional frontend checks are documented in [frontend/README.md](frontend/README.md), including formatting and Playwright browser tests.

### Recorded local validation

The following checks passed in the development environment on 11 November 2026:

| Check | Result |
|---|---:|
| Frontend Vitest suite | 77 passed |
| Backend pytest suite | 18 passed |
| MicroPython compiler unittest suite | 4 passed |
| Bytecode runtime smoke test | Passed |
| Emscripten runner test | Passed |
| Node permission-boundary test | Passed |
| TypeScript check and Vite production build | Passed |
| Git whitespace check | Passed |

The frontend production build reported a large Monaco editor chunk warning. The backend test run reported a Starlette/httpx deprecation warning. Neither warning caused the recorded test/build commands to fail.

These results are a local validation snapshot, not a guarantee that every environment or deployment will produce identical results. Frontend fixture tests do not prove real runtime security or complete production end-to-end behavior.

## Current implementation status

| Area | Current state |
|---|---|
| FastAPI endpoints and request validation | Implemented and tested |
| Orchestrator and artifact-format routing | Implemented and tested |
| MicroPython `.mpy` compiler foundation | Implemented; requires local toolchain and Docker |
| Shared Emscripten MicroPython runtime | Bytecode smoke test passes |
| Emscripten execution adapter | Implemented and tested; prototype isolation only |
| Wasmtime WASI adapter | Executes genuine WASI modules; tested |
| React + Monaco developer portal | Implemented; frontend tests and production build pass |
| Resource-policy validation | Implemented; enforcement differs by runtime |
| Capability-backed host functions | Not implemented; requests fail closed |
| Durable storage and authenticated tenant identity | Not implemented |
| Python source to plugin-specific WASI `.wasm` | Not implemented |
| Experimental MicroPython WASI port | Not yet compatible with the configured Wasmtime runtime |

### Recommended next steps

1. Complete a compatible MicroPython WASI runtime/compiler pipeline, or formally scope the project to the current separate `.mpy` and WASI-`.wasm` routes.
2. Integrate and verify the real frontend-to-backend-to-runtime workflow with representative success and failure cases.
3. Replace caller-supplied tenant context with authenticated identity and durable tenant-scoped storage.
4. Implement narrowly scoped host capabilities only after defining and testing their security contracts.
5. Improve hard resource enforcement for the Emscripten process path and define the semantics of instruction limits across runtimes.
6. Perform an independent security review before any production multi-tenant deployment.

## Team workflow and responsibilities

The project was organized around issue-based branches and pull requests.

| Issue | Responsibility |
|---|---|
| [#1](https://github.com/MHarshavn/WASMBOX/issues/1) | Core architecture and API contracts |
| [#2](https://github.com/MHarshavn/WASMBOX/issues/2) | WASM compilation engine |
| [#3](https://github.com/MHarshavn/WASMBOX/issues/3) | Sandbox and security isolation |
| [#4](https://github.com/MHarshavn/WASMBOX/issues/4) | Multi-tenancy and resource limits |
| [#5](https://github.com/MHarshavn/WASMBOX/issues/5) | React + Monaco developer portal |
| [#6](https://github.com/MHarshavn/WASMBOX/issues/6) | Host functions and capability access |
| [#7](https://github.com/MHarshavn/WASMBOX/issues/7) | Execution metrics and monitoring |
| [#8](https://github.com/MHarshavn/WASMBOX/issues/8) | End-to-end pipeline integration |
| [#9](https://github.com/MHarshavn/WASMBOX/issues/9) | Security and abuse test suite |
| [#10](https://github.com/MHarshavn/WASMBOX/issues/10) | Final review, documentation, and deployment |

Recommended contribution workflow:

1. Start from the latest relevant branch.
2. Work in an issue-specific feature branch.
3. Keep pull requests focused and link them to their issues.
4. Run relevant tests and include actual results in the pull request.
5. Review API and artifact-format compatibility before integrating modules.
6. Treat source code and artifacts as untrusted; do not claim production security based on unit tests alone.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request. Changes to API contracts, artifact formats, runtime behavior, or security boundaries should be reflected in the relevant documentation and regression tests.

## Project documentation

- [API contracts](docs/api/API_CONTRACTS.md)
- [Implementation status and limitations](docs/IMPLEMENTATION_STATUS.md)
- [Architecture documentation](docs/architecture/)
- [MicroPython toolchain guide](docs/compiler/MICROPYTHON_TOOLCHAIN.md)
- [Runtime security contract](docs/security/RUNTIME_SECURITY_CONTRACT.md)
- [Capability model](docs/security/capabilities.md)
- [Sandbox notes](docs/security/sandbox.md)
- [Threat model](docs/security/threat-model.md)
- [Frontend guide](frontend/README.md)
- [GitHub issues](https://github.com/MHarshavn/WASMBOX/issues)
- [GitHub pull requests](https://github.com/MHarshavn/WASMBOX/pulls)
