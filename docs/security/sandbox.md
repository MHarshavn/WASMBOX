# WASMBOX WASM Sandbox

## Purpose

The sandbox isolates untrusted WebAssembly plugins from the host system.

## Default Security Policy

The sandbox follows a deny-by-default security model.

### Filesystem

No host filesystem access is granted by default.

### Network

No network access is granted by default.

### Host Functions

No host functions are available unless explicitly authorized.

### Resources

Plugin execution must be subject to configured resource limits.

## Required Security Demonstrations

1. Attempt to read `/etc/passwd` -> BLOCKED
2. Attempt external network access -> BLOCKED
3. Attempt unauthorized host operation -> BLOCKED
4. Infinite execution -> TERMINATED
5. Excessive resource usage -> TERMINATED

## Security Boundary

The WASM runtime is responsible for executing untrusted plugin code
under the configured sandbox policy.

Application-level capability checks provide an additional security
boundary for host operations.

## Security Assumptions

- The WASM runtime correctly enforces WebAssembly isolation.
- Host functions are explicitly registered by WASMBOX.
- Capabilities are checked before sensitive host operations.
- Resource limits are configured before plugin execution.
- Plugins are considered untrusted by default.