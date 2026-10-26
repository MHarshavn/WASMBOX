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

The repository contains the initial architecture and API documentation, compiler/runtime foundation, toolchain documentation, and contribution/security guidelines. The current MicroPython compiler work produces `.mpy` bytecode for use with a shared WebAssembly runtime; this is not the same as producing a separate standalone `.wasm` module for every plugin. Orchestrator/sandbox integration and end-to-end validation remain follow-up work. See [open issues](https://github.com/MHarshavn/WASMBOX/issues) and [pull requests](https://github.com/MHarshavn/WASMBOX/pulls) for the latest status.
