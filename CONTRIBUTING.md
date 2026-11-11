# Contributing to WASMBOX

## Development workflow

1. Check the current branch and worktree before editing.
2. Keep each change focused and preserve checked-in runtime artifacts.
3. Do not modify `backend/compiler/micropython.wasm` or
   `backend/compiler/micropython.mjs` when changing application code.
4. Add or update tests for changed behavior and run the relevant commands.
5. Review `git diff --check` and `git status` before committing.

## Compiler development

The current MicroPython compiler produces `.mpy` bytecode. The checked-in
WebAssembly file is a shared interpreter runtime, so `.mpy` output must never be
described as a standalone plugin WebAssembly module. Keep compilation and runtime
execution tests separate.

Do not modify the pinned local MicroPython checkout. The known Unix-port WASI
signal-handling build failure must not be retried as part of ordinary development.

## Security-sensitive changes

- Treat source, bytecode, runtime input, and artifact metadata as untrusted.
- Do not execute plugin source using host Python.
- Add a capability check before exposing any host operation.
- Preserve tenant checks on every plugin/execution access.
- Document runtime limitations instead of overstating isolation.

## Pull requests

Include the problem, implementation notes, relevant test exit codes, security
impact, and any required local dependencies. Never commit credentials, SDK
caches, local MicroPython source checkouts, or frontend build output.
