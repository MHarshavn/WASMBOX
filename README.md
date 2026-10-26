# WASMBOX

**WASMBOX** is a secure, lightweight WebAssembly-based sandbox platform designed to run untrusted Python plugins in a multi-tenant SaaS environment. Its target architecture combines a Python-to-WebAssembly compilation path, Wasmtime-based isolation, per-execution resource controls, capability-based host functions, execution observability, and a React + Monaco developer portal.

> **Project status:** Development is in progress. The repository contains the initial architecture and API contracts plus a MicroPython compiler/runtime foundation. The current compiler produces `.mpy` bytecode for a shared WebAssembly runtime; it does **not yet** produce a separate standalone `.wasm` module for every plugin. Sandbox/orchestrator integration and complete end-to-end validation remain ongoing work.

## Problem Statement

Executing user-supplied code inside a backend service can expose the host to unauthorized filesystem or network access, excessive CPU/memory consumption, and cross-tenant data access. WASMBOX is being developed to provide a controlled execution boundary with explicit capabilities, resource limits, structured results, and traceable execution metrics.

## Project Objectives

- Accept supported Python source code through a backend API.
- Validate source and report compilation failures in a structured format.
- Compile code for the supported WebAssembly runtime path.
- Execute untrusted plugins within a configured sandbox.
- Deny host operations unless explicitly authorized through capabilities.
- Isolate tenants and enforce execution resource policies.
- Return execution status, stdout/stderr, duration, and resource/termination details where supported.
- Provide a developer interface for editing, running, and inspecting plugin output.
- Keep setup, testing, security assumptions, and limitations documented.

## Target Architecture and Execution Flow

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

The target flow is the agreed integration direction, not a claim that every component is already connected. The exact implementation must follow the documented API contracts and module interfaces.

## Core Components

| Component | Responsibility |
|---|---|
| Architecture and API contracts | Define module boundaries, lifecycle states, request/response shapes, and integration rules. |
| Compiler | Validate supported Python input, produce the runtime-compatible artifact, and report structured errors. |
| Sandbox and Wasmtime | Execute WebAssembly with explicit isolation and controlled host access. |
| Host functions and capabilities | Expose only approved host operations; reject unauthorized calls by default. |
| Multi-tenancy and resource limits | Scope execution to a tenant and constrain runtime resources and duration. |
| Metrics, logging, and monitoring | Capture execution outcome, output, duration, errors, and supported resource details. |
| Developer portal | Provide a React + Monaco editor, run action, and execution result display. |
| Orchestrator | Coordinate compilation, execution, policy checks, lifecycle state, and result collection. |

## Technology Stack

- **Languages:** Python, JavaScript, and TypeScript/React for the planned developer portal.
- **WebAssembly runtime:** MicroPython WebAssembly runtime artifacts are present in the compiler foundation; Wasmtime is the target runtime for sandboxed execution.
- **Backend:** Python API and orchestration components, following the repository's API contracts.
- **Frontend:** React and Monaco Editor (planned portal scope).
- **Tooling:** Git/GitHub issues, feature branches, pull requests, Docker Desktop, and the Emscripten SDK container used to build the MicroPython WebAssembly runtime.

The presence of a technology in the target stack does not necessarily mean that its integration is complete.

## Repository Guide

- `backend/compiler/` — compiler interface, result models, MicroPython compiler foundation, runtime artifacts, and compiler tests.
- `docs/architecture/` — system architecture and module boundaries.
- `docs/api/API_CONTRACTS.md` — API contract reference.
- `docs/compiler/MICROPYTHON_TOOLCHAIN.md` — MicroPython/WebAssembly toolchain notes.
- `docs/security/` — security-related documentation.
- `frontend/` — developer portal work.
- `tools/micropython/source/` — local MicroPython source checkout used during toolchain development; this checkout is intentionally ignored by Git and must be obtained separately.

## Getting Started

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

The MicroPython source checkout is not included in the repository. Follow [the toolchain guide](docs/compiler/MICROPYTHON_TOOLCHAIN.md) to obtain the expected source revision and build the required `mpy-cross` compiler and WebAssembly runtime artifacts. Keep generated source/build trees out of commits unless a task explicitly requires a reviewed artifact.

### Run compiler unit tests

From the repository root, with Docker Desktop running and the toolchain prepared:

```bash
python -m unittest backend.compiler.test_micropython_compiler -v
```

These tests cover valid Python compilation, empty-source rejection, and invalid-syntax rejection. They validate the compiler foundation, not the complete end-to-end WASMBOX system.

## Two-Week Project Process

### Week 1 — Architecture, Contracts, and Technical Validation

**Goal:** Agree on the design and divide work before building modules in parallel.

- Defined the system architecture and execution lifecycle.
- Documented API request/response contracts and core interfaces for the compiler, sandbox, resource policy, host capabilities, and execution results.
- Identified module boundaries, dependencies, and ownership across the team.
- Investigated the Python-to-WebAssembly approach and validated the MicroPython/WebAssembly toolchain.
- Created issue-based feature branches and established pull-request-based collaboration.

**Deliverables:** architecture documentation, API contracts, module ownership, and a validated technical direction for the compiler/runtime.

### Week 2 — Parallel Implementation, Testing, and Integration

**Goal:** Implement each subsystem against the agreed interfaces, test it independently, and begin connecting the components.

- **Compiler:** source validation, compilation artifacts, structured errors, and compiler tests.
- **Sandbox and capabilities:** isolated execution, deny-by-default host access, and security tests.
- **Multi-tenancy and resource limits:** tenant isolation, execution timeouts, memory limits, and termination reporting.
- **Developer portal:** React + Monaco interface and backend API connection.
- **Metrics and monitoring:** execution status, output, duration, errors, and supported resource information.
- **Integration:** connect the frontend, API, orchestrator, compiler, sandbox, and metrics layer; test success and failure paths.
- **Review and documentation:** review pull requests, record test results, document setup, and track remaining work.

**Deliverables:** independently tested modules, reviewed pull requests, and an incremental end-to-end execution path. Full integration is complete only after the complete flow and required security/resource-limit tests pass.

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

1. Take work from the relevant GitHub issue and coordinate dependencies with module owners.
2. Create or use a dedicated feature branch; do not commit implementation work directly to `main`.
3. Keep pull requests focused and link them to their issues.
4. Run relevant unit/integration tests and include actual results in the pull request.
5. Review interface compatibility before merging modules.
6. Treat user-supplied Python and plugin artifacts as untrusted; test isolation, resource limits, and capability checks before claiming the system is secure.

## Security Principles

- Treat all submitted source code, artifacts, and runtime inputs as untrusted.
- Use deny-by-default host capabilities.
- Apply filesystem/network isolation and resource limits in the runtime configuration.
- Return structured errors for compilation, permission, and execution failures.
- Test expected denial of unauthorized operations, resource exhaustion, and cross-tenant access.
- Passing unit tests alone is not proof of sandbox security.

See [SECURITY.md](SECURITY.md) for the security policy and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Current Status and Next Steps

The repository contains the initial architecture and API documentation, compiler/runtime foundation, toolchain documentation, and contribution/security guidelines. The compiler unit tests have passed in the development environment. The current MicroPython compiler work produces `.mpy` bytecode for use with a shared WebAssembly runtime; it is not yet a standalone WebAssembly artifact generated separately for every plugin.

Next steps are to agree on the canonical compiler implementation, integrate bytecode loading with the runtime, connect the compiler to the orchestrator and sandbox, implement and verify resource/capability enforcement, and run the full end-to-end and security test suites.

- [GitHub Issues](https://github.com/MHarshavn/WASMBOX/issues)
- [Pull Requests](https://github.com/MHarshavn/WASMBOX/pulls)
- [Architecture](docs/architecture/)
- [API Contracts](docs/api/API_CONTRACTS.md)
- [Compiler Toolchain Guide](docs/compiler/MICROPYTHON_TOOLCHAIN.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.
