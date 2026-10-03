# WASMBOX WASM Sandbox

## Purpose

The WASMBOX sandbox isolates untrusted WebAssembly plugins from
unrestricted access to the host system.

Plugin execution is performed through Wasmtime under a deny-by-default
security policy.

## Default Security Policy

The sandbox follows a deny-by-default security model.

Capabilities and host resources are unavailable unless they are
explicitly authorized.

### Filesystem

Host filesystem access is denied by default.

WASI is configured without preopened host directories.

Therefore, a plugin cannot access arbitrary host paths such as:

```text
/etc/passwd