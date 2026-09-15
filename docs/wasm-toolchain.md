# WASM Compilation Toolchain

## Approach

WASMBOX uses a WebAssembly-based Python execution pipeline built around
MicroPython and Wasmtime.

The planned execution flow is:

Python source
    ↓
Compiler service
    ↓
MicroPython WASI WebAssembly runtime
    ↓
Wasmtime
    ↓
Sandboxed execution

## Toolchain Components

- Python 3
- MicroPython
- WebAssembly (WASM)
- WASI
- Wasmtime
- pytest

## Development Environment

The toolchain is developed and tested using Ubuntu under WSL2 on Windows.

## Important Design Decision

The standard MicroPython Unix port currently cloned for development does
not contain a WASI/WASM variant.

Therefore, WASMBOX will use a dedicated MicroPython WASI build rather
than attempting to produce WebAssembly from the standard Unix port.

## Reproducibility

The MicroPython WASI runtime used by WASMBOX will be pinned to a known
source revision/build configuration.

The resulting `.wasm` runtime will be stored as a versioned compiler
artifact for integration testing.

## Security Boundary

Python submitted to WASMBOX is treated as untrusted input.

Execution will later be performed through Wasmtime with restricted host
capabilities and resource limits.

## Interface

The final compiler service interface will follow the contract established
by Issue #1.
