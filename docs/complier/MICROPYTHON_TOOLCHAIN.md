# WASMBOX MicroPython Compiler Toolchain

## 1. Overview

WASMBOX uses MicroPython's `mpy-cross` compiler to compile
supported Python source code into MicroPython bytecode (`.mpy`).

The compiler runs through Docker using the
`emscripten/emsdk:latest` image.

## 2. Compilation Flow

1. The compiler receives Python source code.
2. It validates the source and requested Python version.
3. It creates a temporary workspace.
4. Docker runs `mpy-cross` against the source file.
5. The compiler reads the generated `.mpy` artifact.
6. A successful compilation returns `COMPILED`.
7. Compilation failures return `COMPILATION_FAILED`
   with a structured error.

## 3. Requirements

- Python
- Git
- Docker Desktop
- The `emscripten/emsdk:latest` Docker image
- MicroPython source repository and submodules
- A built `mpy-cross` executable

## 4. Verify Docker

Run:

```powershell
docker info
docker image inspect emscripten/emsdk:latest