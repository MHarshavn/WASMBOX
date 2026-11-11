# WASMBOX

WASMBOX is a secure, lightweight WebAssembly-based sandbox for executing untrusted Python plugins in a multi-tenant SaaS environment. The project is designed around Wasmtime isolation, resource limits, capability-based host functions, and a React + Monaco developer portal.

## Project Goal

Provide an end-to-end workflow where a developer writes Python code, submits it through the API, compiles it for the supported runtime, executes it inside a sandbox, and receives the result and execution metrics without granting the plugin unrestricted host access.

## Two-Week Project Process

### Week 1 — Architecture, Contracts, and Technical Validation

**Goal:** Agree on the design and divide work before building modules in parallel.

- Defined the system architecture and execution lifecycle.
- Documented API request/response contracts and core interfaces for the compiler, sandbox, resource policy, host capabilities, and execution results.
- Identified module boundaries, dependencies, and ownership across the team.
- Investigated the Python-to-WebAssembly approach and validated the MicroPython/WebAssembly toolchain.
- Created issue-based feature branches and established pull-request-based collaboration.

**Week 1 deliverables:** architecture documentation, API contracts, module ownership, and a validated technical direction for the compiler/runtime.

### Week 2 — Parallel Implementation, Testing, and Integration

**Goal:** Implement each subsystem against the agreed interfaces, test it independently, and begin connecting the components.

- **Compiler:** implement source validation, compilation artifacts, structured errors, and compiler tests.
- **Sandbox and capabilities:** configure isolated execution, deny-by-default host access, and security tests.
- **Multi-tenancy and resource limits:** define tenant isolation, execution timeouts, memory limits, and termination reporting.
- **Developer portal:** build the React + Monaco interface and connect it to the backend API.
- **Metrics and monitoring:** capture execution status, output, duration, errors, and resource information where supported.
- **Integration:** connect the frontend, API, orchestrator, compiler, sandbox, and metrics layer; test success and failure paths.
- **Review and documentation:** review pull requests, record test results, document setup, and track remaining work.

**Week 2 deliverables:** independently tested modules, reviewed pull requests, and an incremental end-to-end execution path. Full integration is considered complete only when the complete flow and the required security/resource-limit tests pass.

## Team Responsibilities

| Issue | Owner | Responsibility |
|---|---|---|
| [#1](https://github.com/MHarshavn/WASMBOX/issues/1) | Team Lead | Core architecture and API contracts |
| [#2](https://github.com/MHarshavn/WASMBOX/issues/2) | Member 2 — `mrunali24-hatwar` | WASM compilation engine |
| [#3](https://github.com/MHarshavn/WASMBOX/issues/3) | Member 3 — `Abhi-3690` | Sandbox and security isolation |
| [#4](https://github.com/MHarshavn/WASMBOX/issues/4) | Member 4 — `akshat15codes` | Multi-tenancy and resource limits |
| [#5](https://github.com/MHarshavn/WASMBOX/issues/5) | Member 5 — `w2323` | React + Monaco developer portal |
| [#6](https://github.com/MHarshavn/WASMBOX/issues/6) | Member 3 — `Abhi-3690` | Host functions and capability access |
| [#7](https://github.com/MHarshavn/WASMBOX/issues/7) | Member 4 — `akshat15codes` | Execution metrics and monitoring |
| [#8](https://github.com/MHarshavn/WASMBOX/issues/8) | Team Lead | End-to-end pipeline integration |
| [#9](https://github.com/MHarshavn/WASMBOX/issues/9) | Member 3 — `Abhi-3690` | Security and abuse test suite |
| [#10](https://github.com/MHarshavn/WASMBOX/issues/10) | Team Lead | Final review, documentation, and deployment |

## Development Workflow

1. Take work from the relevant GitHub issue and coordinate dependencies with the module owners.
2. Create or use a dedicated feature branch; do not commit implementation work directly to `main`.
3. Keep pull requests focused and link them to their issues.
4. Run the relevant unit and integration tests and include the actual results in the pull request.
5. Review interface compatibility before merging modules.
6. Treat user-supplied Python and plugin artifacts as untrusted; test isolation, resource limits, and capability checks before claiming the system is secure.

## Current Implementation Status

The repository includes a FastAPI backend, compiler foundation, execution orchestrator, sandbox router, resource-policy validation, and React + Monaco developer portal.

The MicroPython compiler produces `.mpy` bytecode, which runs through the shared Emscripten MicroPython runtime. A separate Wasmtime adapter supports WASI WebAssembly modules. However, a complete Python-to-WASI `.wasm` compilation pipeline is not yet implemented.

The current system is a development prototype, not a production-ready security boundary. Tenant storage is in-memory, and host capabilities are deny-by-default. See [implementation status](docs/IMPLEMENTATION_STATUS.md) for limitations.


## Problem Statement

Running user-supplied code directly inside a backend service can expose the host to unauthorized filesystem or network access, excessive resource consumption, and cross-tenant data access. WASMBOX is being developed to provide a controlled execution boundary with explicit capabilities, resource policies, structured results, and execution metrics.

## Target Architecture

```text
React + Monaco Developer Portal
              |
              v
         Backend API
              |
              v
          Orchestrator
              |
              v
       Python Compiler
              |
              v
      WebAssembly Runtime
              |
              v
       Sandbox / Wasmtime
              |
              v
   Host Capabilities + Resource Policy
              |
              v
       Execution Metrics
              |
              v
     API Response to the UI
```

This is the target integration flow. It should not be interpreted as evidence that every component is already integrated.

## Core Components

| Component | Responsibility |
|---|---|
| Architecture and API contracts | Define module boundaries, lifecycle states, request/response shapes, and integration rules. |
| Compiler | Validate supported Python input, produce a runtime-compatible artifact, and report structured errors. |
| Sandbox and Wasmtime | Execute WebAssembly with explicit isolation and controlled host access. |
| Host functions and capabilities | Expose approved host operations and reject unauthorized calls by default. |
| Multi-tenancy and resource limits | Scope execution to a tenant and constrain runtime resources and duration. |
| Metrics and monitoring | Capture execution outcome, output, duration, errors, and supported resource details. |
| Developer portal | Provide a React + Monaco editor, run action, and execution result display. |
| Orchestrator | Coordinate compilation, execution, policy checks, lifecycle state, and result collection. |

## Technology Stack

- **Languages:** Python and JavaScript; React/TypeScript for the planned developer portal.
- **WebAssembly:** MicroPython WebAssembly runtime artifacts are present in the compiler foundation; Wasmtime is the target for sandboxed execution.
- **Backend:** Python API and orchestration components, following the repository's API contracts.
- **Frontend:** React and Monaco Editor.
- **Tooling:** Git/GitHub, Docker Desktop, and the Emscripten SDK container used to build the MicroPython WebAssembly runtime.

The presence of a technology in the target stack does not necessarily mean its integration is complete.

## Repository Guide

- `backend/compiler/` — compiler interface, result models, MicroPython compiler foundation, runtime artifacts, and compiler tests.
- `docs/architecture/` — system architecture and module boundaries.
- `docs/api/API_CONTRACTS.md` — API contract reference.
- `docs/compiler/MICROPYTHON_TOOLCHAIN.md` — MicroPython/WebAssembly toolchain notes.
- `frontend/` — developer portal work.
- `tools/micropython/source/` — local MicroPython source checkout used during toolchain development; it is intentionally ignored by Git and must be obtained separately.

## Getting Started

### Developer portal (Issue #5)

The React + TypeScript portal in `frontend/` includes a locally bundled Monaco Python
editor, compile/execute/result API integration, output and metrics, browser-local
plugin save/load, and simulated webhook input.

```bash
cd frontend
npm ci
npm run dev
```

The development server proxies `/api` to `http://127.0.0.1:8000`. Start the backend
separately. See the [frontend guide](frontend/README.md) for configuration, tests,
deployment, and the remaining real-backend integration checks. Frontend browser tests
use contract fixtures and do not validate sandbox security.

### Prerequisites

- Git
- Python compatible with the project's dependencies
- Node.js for JavaScript runtime smoke tests
- Docker Desktop with its Linux engine running for the current Docker-based MicroPython compilation workflow

### Clone the repository

```bash
git clone https://github.com/MHarshavn/WASMBOX.git
cd WASMBOX
```

### Prepare the MicroPython toolchain

The MicroPython source checkout is not included in the repository. Follow the [toolchain guide](docs/compiler/MICROPYTHON_TOOLCHAIN.md) to obtain the expected source revision and build the required `mpy-cross` compiler and WebAssembly runtime artifacts. Keep generated source/build trees out of commits unless a task explicitly requires a reviewed artifact.

### Run compiler unit tests

From the repository root, with Docker Desktop running and the toolchain prepared:

```bash
python -m unittest backend.compiler.test_micropython_compiler -v
```

These tests cover valid Python compilation, empty-source rejection, and invalid-syntax rejection. They validate the compiler foundation, not the complete end-to-end WASMBOX system.

## Security Principles

- Treat submitted source code, artifacts, and runtime inputs as untrusted.
- Use deny-by-default host capabilities.
- Apply filesystem/network isolation and resource limits in the runtime configuration.
- Return structured errors for compilation, permission, and execution failures.
- Test unauthorized operations, resource exhaustion, and cross-tenant access.
- Passing unit tests alone is not proof of sandbox security.

See [SECURITY.md](SECURITY.md) for the security policy and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Current Status and Next Steps

The backend, compiler foundation, sandbox adapters, frontend portal, and security tests have been implemented and integrated to varying degrees. The MicroPython `.mpy` execution path and the separate Wasmtime WASI execution path are distinct.

Remaining work includes resolving integration conflicts, validating the complete frontend/backend workflow, running the full test suite, and documenting the limitations of the experimental WASI compiler port.

- [GitHub Issues](https://github.com/MHarshavn/WASMBOX/issues)
- [Pull Requests](https://github.com/MHarshavn/WASMBOX/pulls)
- [Architecture](docs/architecture/)
- [API Contracts](docs/api/API_CONTRACTS.md)
- [Compiler Toolchain Guide](docs/compiler/MICROPYTHON_TOOLCHAIN.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.
