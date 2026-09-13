# WASMBOX Security Threat Model

## Objective

WASMBOX executes untrusted Python plugins compiled to WebAssembly.

The security architecture must prevent untrusted plugins from obtaining
unrestricted access to the host system.

## Security Principles

1. Deny by default.
2. Grant only explicitly authorized capabilities.
3. Do not expose arbitrary host APIs.
4. Filesystem access must be isolated.
5. Network access must be denied unless explicitly authorized.
6. Resource limits must be enforced per execution.
7. Security violations must return structured errors.
8. Tenant resources must remain isolated.

## Threats

### T1 - Filesystem Escape

A malicious plugin may attempt to access host files such as:

/etc/passwd

Expected result:

BLOCKED

### T2 - Network Access

A malicious plugin may attempt to connect to an external network.

Expected result:

BLOCKED

### T3 - Unauthorized Host Function

A plugin may attempt to call a host function that was not granted.

Expected result:

BLOCKED

### T4 - Infinite Execution

A plugin may execute an infinite loop.

Expected result:

TIMEOUT or TERMINATED

### T5 - Resource Abuse

A plugin may attempt to consume excessive memory or instructions.

Expected result:

RESOURCE LIMIT or TERMINATED

### T6 - Cross-Tenant Access

A plugin belonging to one tenant may attempt to access another tenant's resources.

Expected result:

BLOCKED

### T7 - Malformed WASM

A malformed or invalid WASM module may be submitted.

Expected result:

SAFELY REJECTED

## Default Security Policy

| Capability | Default |
|---|---|
| Filesystem | DENY |
| Network | DENY |
| Environment access | DENY |
| Host functions | DENY |
| Cross-tenant access | DENY |

## Security Boundary

Untrusted plugin code executes inside the configured WebAssembly sandbox.

Host functionality is exposed only through explicitly authorized capabilities.

No arbitrary host API should be directly accessible to plugins.