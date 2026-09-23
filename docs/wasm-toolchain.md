# WASM Compilation Toolchain

## Overview

WASMBOX accepts Python source code and compiles it into a
source-specific WebAssembly (`.wasm`) artifact.

The current compilation pipeline is:

Python source
    ↓
CompilerService
    ↓
Python syntax validation
    ↓
MicroPython WASI build
    ↓
Frozen Python module
    ↓
WebAssembly artifact
    ↓
Wasmtime

## Toolchain Components

- Python 3
- MicroPython
- WebAssembly (WASM)
- WASI
- WASI SDK
- Binaryen / wasm-opt
- Wasmtime
- pytest

## Development Environment

The current compiler toolchain is developed on Windows using
Ubuntu under WSL2.

The MicroPython WASI build requires:

- Ubuntu/WSL2
- WASI SDK 25.0
- Binaryen (`wasm-opt`)
- Clang/LLVM
- Make
- MicroPython WASI source tree

## MicroPython WASI

WASMBOX uses the MicroPython WASI variant rather than the standard
MicroPython Unix build.

The WASI-enabled MicroPython source is maintained separately in:

`toolchain/micropython-wasi`

The WASI variant is built using:

`ports/unix/variants/wasi`

The resulting runtime is a WebAssembly module that can execute
Python code through the MicroPython runtime.

## Source-Specific Compilation

The compiler service creates a temporary Python source file and a
MicroPython frozen-module manifest.

The manifest contains:

```python
module("program.py")

## Known-Good WASM Artifact

A known-good WASM artifact can be generated from the example Python program:

```text
examples/hello.py
```

Run:

```powershell
python -m compiler.cli examples\hello.py --output artifacts\hello.wasm
```

The generated artifact is:

```text
artifacts/hello.wasm
```

This artifact is intended for compiler and integration testing. It can be regenerated using the documented compilation pipeline rather than being treated as a source file.

The artifact was verified by successfully compiling the valid `examples/hello.py` input through `CompilerService`.
