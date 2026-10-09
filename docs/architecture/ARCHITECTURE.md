# WASMBOX Core Architecture

## 1. Purpose

WASMBOX is a secure, lightweight WebAssembly execution platform for running untrusted Python plugins in a multi-tenant SaaS environment.

This document freezes the implementation boundaries used by Issues #2–#7.

## 2. System Architecture

```text
React + Monaco Developer Portal
            |
            v
       API Layer
            |
            v
      Orchestrator
       /       \
      v         v
 Compiler     Sandbox
      |         |
      |      Resource Policy
      |         |
      |      Host Capabilities
      |         |
      +----> Wasmtime
                 |
                 v
             Execution
                 |
                 v
              Metrics
                 |
                 v
          ExecutionResult
                 |
                 v
             API / UI
```

## 3. Ownership and Boundaries

| Component | Owner | Responsibility |
|---|---|---|
| Architecture & Orchestrator | Team Lead | Lifecycle, integration, execution coordination |
| Compiler | Member 2 | Python source → WASM artifact |
| Sandbox & Security | Member 3 | Wasmtime isolation and security policy |
| Multi-Tenancy & Resources | Member 4 | Tenant isolation and resource limits |
| Developer Portal | Member 5 | React + Monaco UI and API consumption |
| Host Capabilities | Member 3 | Deny-by-default host operations |
| Metrics | Member 4 | Execution telemetry and structured results |

## 4. Execution Lifecycle

Normal lifecycle:

```text
CREATED
  -> COMPILING
  -> READY
  -> RUNNING
  -> SUCCESS
```

Failure states:

- COMPILATION_FAILED
- EXECUTION_FAILED
- TIMEOUT
- MEMORY_LIMIT
- INSTRUCTION_LIMIT
- PERMISSION_DENIED
- SANDBOX_ERROR

Modules must use these exact state names.

## 5. Core Data Models

### Plugin

```text
Plugin
- plugin_id
- tenant_id
- plugin_name
- source_code
- wasm_artifact
- python_version
```

### ExecutionRequest

```text
ExecutionRequest
- plugin_id
- tenant_id
- input
- limits
  - memory_mb
  - timeout_ms
  - instruction_limit
- capabilities[]
```

### ExecutionResult

```text
ExecutionResult
- execution_id
- status
- stdout
- stderr
- execution_time_ms
- memory_used_mb
- termination_reason
```

### ResourcePolicy

```text
ResourcePolicy
- memory_mb
- timeout_ms
- instruction_limit
```

## 6. Stable Interfaces

### Compiler

```text
compile(source_code, python_version)
    -> CompilationResult
```

The compiler returns either a WASM artifact or a structured compilation error. It must not execute the artifact.

### Sandbox

```text
execute(wasm_artifact, input, resource_policy, capabilities)
    -> SandboxResult
```

The sandbox owns WASM loading, isolation, runtime execution, and security failures.

### Resource Manager

```text
validate(policy)
    -> ResourcePolicy | Error

enforce(policy)
    -> RuntimeLimits
```

The API validates platform-level maximums; the runtime/resource layer enforces execution limits.

### Capability Manager

```text
check(capabilities, requested_capability)
    -> allowed | PERMISSION_DENIED
```

Capabilities are deny-by-default. An empty capability list grants no host access.

### Orchestrator

```text
execute(request)
    -> ExecutionResult
```

The orchestrator coordinates compilation, resource policy, sandbox execution, capabilities, lifecycle state, and metrics. It does not implement compiler or sandbox internals.

## 7. Module Dependencies

```text
API
 |
 v
Orchestrator
 |------> Compiler
 |------> Resource Manager
 |------> Capability Manager
 |------> Sandbox
 |             |
 |             v
 |          Wasmtime
 |
 +-------> Metrics
```

The frontend depends only on the API contract.

The API layer must not execute WASM directly.

The compiler and sandbox are independently testable.

## 8. Security Boundary

1. Untrusted plugin code executes inside WebAssembly.
2. Host filesystem access is denied unless an explicit capability is implemented.
3. Network access is denied unless an explicit capability is implemented.
4. Host functions require capability checks.
5. Resource limits apply per execution.
6. Tenant context is attached to plugin and execution operations.
7. Sandbox failures are converted into structured errors and must not crash the API service.

## 9. Integration Rules

- `docs/api/API_CONTRACTS.md` is the single source of truth for API communication.
- Modules must not invent alternative lifecycle state names.
- API contract changes require Team Lead approval before implementation.
- Each implementation issue must preserve the interfaces defined here.
- Internal implementation details may change without changing the public contracts.
- End-to-end integration occurs only after the required module interfaces are available.

## 10. Issue Dependency Graph

```text
Issue #1 Core Architecture & API Contracts
              |
      +-------+-------+
      |       |       |
      v       v       v
     #2      #3      #4
 Compiler  Sandbox  Tenant/Resources
      \       |       /
       \      |      /
        +-----+-----+
              |
             #6 Host Capabilities
              |
             #7 Metrics
              |
             #5 Developer Portal
              |
             #8 End-to-End Integration
              |
             #9 Security Tests
              |
             #10 Final Review
```

## 11. Acceptance Checklist

- [x] Core architecture documented
- [x] Execution lifecycle states defined
- [x] Plugin and execution models defined
- [x] Compiler interface defined
- [x] Sandbox interface defined
- [x] Resource policy interface defined
- [x] Capability interface defined
- [x] ExecutionResult schema defined
- [x] Module ownership and dependencies documented
- [x] Integration rules documented
- [x] API contract maintained in `docs/api/API_CONTRACTS.md`
