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
9. Malformed WASM must be safely rejected.

## Threats

### T1 - Filesystem Escape

A malicious plugin may attempt to access host files such as:

```text
/etc/passwd