\# WASMBOX Runtime Security Contract



\## 1. Purpose



This document records the security boundaries, resource controls, error classifications, and verification requirements for the WASMBOX runtime.



\## 2. Execution Boundaries



\### Standard WASM execution



The runtime validates and instantiates WebAssembly modules without providing arbitrary host imports.



\### WASI execution



The runtime configures WASI without preopened host directories. Filesystem isolation tests should verify actual WASI operation results rather than relying only on a nonzero return code.



\### Host-function execution



The runtime exposes a limited host interface containing `wasmbox.host\_log`. Access is checked using a capability policy, with denial by default.



The host logging implementation must validate guest-memory bounds and message length before reading guest memory.



\## 3. Resource Limits



\- Default fuel: 100,000 units.

\- Default memory limit: 16 MiB.

\- Non-positive fuel and memory limits are rejected during initialization.

\- Fuel exhaustion during invocation is classified as `INSTRUCTION\_LIMIT`.

\- Recognized memory/resource-limit failures during instantiation are classified as `MEMORY\_LIMIT`.



Fuel is an instruction budget, not a wall-clock timeout. Resource limits alone do not establish cross-tenant isolation.



\## 4. Runtime Error Contract



| Condition | Error code |

|---|---|

| WASM validation failure | `SANDBOX\_ERROR` |

| Generic module instantiation failure | `SANDBOX\_ERROR` |

| Recognized memory/resource-limit failure during instantiation | `MEMORY\_LIMIT` |

| Fuel exhaustion during invocation | `INSTRUCTION\_LIMIT` |

| Unauthorized host capability during invocation | `PERMISSION\_DENIED` |

| Missing exported function | `SANDBOX\_ERROR` |



Runtime errors should preserve the underlying exception as their cause when available.



\## 5. Network Isolation



WASI Preview 1 does not define a standard `sock\_send` import. Rejection of that import demonstrates unsupported-import handling, not proof that an actual network connection was blocked.



A comprehensive network-isolation claim requires testing a supported networking interface and verifying that the attempted operation is denied.



\## 6. Security Verification Requirements



The security regression suite should cover:



\- Malformed and invalid WASM modules.

\- Unprovided host imports.

\- Filesystem access attempts without preopened directories.

\- Unauthorized host-function calls.

\- Fuel exhaustion and excessive memory requests.

\- Host logging with invalid memory ranges and oversized messages.

\- Cross-tenant isolation, coordinated with the tenancy implementation.



Tests should assert specific failure conditions and error codes instead of accepting arbitrary exceptions or unexplained nonzero return codes.



\## 7. Known Limitations



Passing the current test suite proves only the behaviors exercised by its tests. It does not establish comprehensive filesystem or network isolation, cross-tenant separation, or protection against every resource-exhaustion attack.



Security guarantees must be supported by implementation review and explicit regression-test evidence.
