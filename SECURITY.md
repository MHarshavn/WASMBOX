# Security Policy

## Reporting a vulnerability

Report suspected vulnerabilities privately to the repository maintainers. Include
the affected component, configuration, reproduction steps, impact, and any
proposed mitigation. Do not include credentials, private keys, or personal data.

## Current security posture

WASMBOX treats plugin source, compiled bytecode, runtime input, and artifact
metadata as untrusted. The API never executes plugin source with host Python.
The current Emscripten prototype runs bytecode in a new Node process with Node's
permission model enabled and access restricted to the runtime directory. It does
not grant filesystem write, network, child process, worker, addon, WASI, or host
function permissions.

All records are tenant-scoped in memory and every lookup verifies the request's
tenant context. The prototype requires `X-Tenant-ID` because authentication is
not yet implemented; this header must not be accepted as a production identity
mechanism.

## Limitations

This project does not currently execute generated plugin modules under Wasmtime.
The Emscripten runtime includes a JavaScript bridge, and Node's permission model
is not a substitute for a complete runtime security review. The permission test
demonstrates denial of a repository filesystem read outside the runtime
allow-list; it does not prove comprehensive isolation.

Wall-clock timeout is enforced by terminating the child process. The current
shared runtime cannot provide complete process-memory enforcement or instruction
fuel accounting. Passing tests does not establish that the sandbox is secure for
production multi-tenant workloads.
