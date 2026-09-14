# WASMBOX API Contracts

## 1. Purpose

This document defines the interfaces between the WASMBOX frontend,
API layer, orchestrator, compiler, sandbox, resource manager,
host-function layer, and metrics system.

All team members must follow these contracts when implementing
their modules.

---

## 2. High-Level Execution Flow

Developer Portal
        |
        v
   API Layer
        |
        v
   Orchestrator
        |
        +----------------+
        |                |
        v                v
    Compiler          Sandbox
        |                |
        +-------+--------+
                |
                v
        Resource Manager
                |
                v
          Host Functions
                |
                v
          WASM Execution
                |
                v
             Metrics
                |
                v
         Execution Result
                |
                v
           API Response
                |
                v
        Developer Portal

---

## 3. Plugin Compilation API

### Endpoint

POST /api/v1/plugins/compile

### Request

```json
{
  "plugin_name": "example-plugin",
  "source_code": "print('Hello WASMBOX')",
  "python_version": "3.x"
}
```

### Response — Success

```json
{
  "status": "COMPILED",
  "plugin_id": "plugin-123",
  "wasm_artifact": "artifact-reference"
}
```

### Response — Failure

```json
{
  "status": "COMPILATION_FAILED",
  "error": {
    "code": "COMPILATION_ERROR",
    "message": "Plugin compilation failed"
  }
}
```

---

## 4. Plugin Execution API

### Endpoint

POST /api/v1/plugins/execute

### Request

```json
{
  "plugin_id": "plugin-123",
  "input": {},
  "limits": {
    "memory_mb": 128,
    "timeout_ms": 5000
  },
  "capabilities": []
}
```

### Response

```json
{
  "execution_id": "execution-123",
  "status": "RUNNING"
}
```

---

## 5. Execution Result API

### Endpoint

GET /api/v1/executions/{execution_id}

### Successful Execution

```json
{
  "execution_id": "execution-123",
  "status": "SUCCESS",
  "stdout": "Hello WASMBOX",
  "stderr": "",
  "execution_time_ms": 42,
  "memory_used_mb": 8,
  "termination_reason": null
}
```

### Failed Execution

```json
{
  "execution_id": "execution-123",
  "status": "EXECUTION_FAILED",
  "stdout": "",
  "stderr": "Execution failed",
  "execution_time_ms": 25,
  "memory_used_mb": 6,
  "termination_reason": "RUNTIME_ERROR"
}
```

---

## 6. Execution States

The following states are standardized across the system:

### Normal states

- CREATED
- COMPILING
- READY
- RUNNING
- SUCCESS

### Failure states

- COMPILATION_FAILED
- EXECUTION_FAILED
- TIMEOUT
- MEMORY_LIMIT
- INSTRUCTION_LIMIT
- PERMISSION_DENIED
- SANDBOX_ERROR

Modules must not invent alternative state names.

---

## 7. Resource Limits

The execution request may contain:

```json
{
  "limits": {
    "memory_mb": 128,
    "timeout_ms": 5000,
    "instruction_limit": 1000000
  }
}
```

The sandbox/resource layer is responsible for enforcing these limits.

The API layer validates that requested values are within the
platform's allowed maximum.

---

## 8. Capability Model

Capabilities are explicitly granted to a plugin.

Example:

```json
{
  "capabilities": [
    "host.log"
  ]
}
```

Default:

```
capabilities = []
```

No capability means no host access.

Example allowed capability:

```
host.log
```

Example future capability:

```
host.storage.read
```

Capabilities must be checked before executing a host function.

---

## 9. Host Function Contract

A host function request contains:

```json
{
  "capability": "host.log",
  "operation": "log",
  "arguments": {
    "message": "Hello"
  }
}
```

Success:

```json
{
  "success": true
}
```

Permission failure:

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Capability not granted"
  }
}
```

---

## 10. Security Contract

The system must enforce:

1. Untrusted plugin code executes inside WebAssembly.
2. Plugins cannot directly access the host filesystem.
3. Plugins cannot directly access the host network.
4. Host functions use explicit capabilities.
5. Capabilities are deny-by-default.
6. Resource limits are enforced.
7. Tenant data must remain isolated.
8. Sandbox failures must not crash the API service.

---

## 11. Standard Error Format

All modules should return errors using:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable explanation"
  }
}
```

Standard error codes include:

```
INVALID_REQUEST
COMPILATION_ERROR
COMPILATION_FAILED
EXECUTION_FAILED
TIMEOUT
MEMORY_LIMIT
INSTRUCTION_LIMIT
PERMISSION_DENIED
SANDBOX_ERROR
PLUGIN_NOT_FOUND
TENANT_ACCESS_DENIED
INTERNAL_ERROR
```

---

## 12. Module Boundaries

### API Layer

Responsible for:

- Request validation
- Authentication/tenant context
- Calling the orchestrator
- Formatting API responses

The API layer must not execute WASM directly.

### Orchestrator

Responsible for:

- Managing the execution lifecycle
- Calling the compiler when necessary
- Creating sandbox executions
- Passing resource limits
- Passing capabilities
- Collecting execution results

### Compiler

Responsible for:

- Converting supported Python source into WASM
- Returning a WASM artifact
- Returning structured compilation errors

### Sandbox

Responsible for:

- Loading WASM
- Isolating execution
- Enforcing security restrictions
- Executing the WASM module

### Resource Manager

Responsible for:

- Memory limits
- Timeout limits
- Instruction/execution limits where supported
- Resource accounting

### Host Function Layer

Responsible for:

- Exposing only approved host functionality
- Checking capabilities
- Rejecting unauthorized operations

### Metrics

Responsible for:

- Execution duration
- Memory usage
- stdout
- stderr
- execution status
- termination reason

### Developer Portal

Responsible for:

- Plugin editing
- Compilation requests
- Execution requests
- Displaying stdout/stderr
- Displaying execution status
- Displaying execution metrics

---

## 13. Contract Rule

If a module needs to change an API contract, the change must be
discussed with the Team Lead before implementation.

The API contract must remain the single source of truth for
communication between modules.
