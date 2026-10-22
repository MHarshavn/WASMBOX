@'
# Contributing to WASMBOX

Thank you for contributing to WASMBOX.

## Development Workflow

1. Check out the latest `main` branch before starting new work.
2. Create a feature branch for each issue or task.
3. Keep changes focused and follow the existing project structure.
4. Add or update tests for changes to application behavior.
5. Run the relevant tests before committing.
6. Review your changes and ensure no secrets, credentials, or unrelated build artifacts are included.

## Commit Guidelines

Use clear, descriptive commit messages. Examples:

- `feat(compiler): add MicroPython compilation support`
- `fix(sandbox): handle invalid execution requests`
- `test(compiler): add compilation failure tests`
- `docs: update toolchain instructions`

## Pull Requests

- Explain the problem and the proposed solution.
- Link the related issue.
- Include relevant test results.
- Document configuration or compatibility requirements.
- Request review before merging.

## Compiler Development

The current MicroPython compiler implementation produces `.mpy` bytecode artifacts. The shared WebAssembly runtime and bytecode execution path must be tested separately from compilation. Do not describe `.mpy` output as a standalone WebAssembly module.
'@ | Set-Content -Path .\CONTRIBUTING.md -Encoding utf8