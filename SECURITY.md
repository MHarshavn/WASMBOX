@'
# Security Policy

## Reporting a Vulnerability

Please do not disclose exploitable vulnerabilities in public issues before the maintainers have had an opportunity to assess them.

Report suspected vulnerabilities privately to the repository maintainers through a private communication channel available to the project. Include:

- A description of the vulnerability.
- Steps to reproduce it.
- The affected component and configuration.
- Potential impact and any suggested mitigation.

Do not include real credentials, private keys, personal data, or sensitive production information in reports.

## Security Considerations

WASMBOX executes user-supplied code. Treat source code, compiled artifacts, runtime inputs, and plugin requests as untrusted.

Security-sensitive changes should consider:

- WebAssembly sandbox isolation.
- Execution time and resource limits.
- Host-function permissions and capability boundaries.
- Input validation and error handling.
- Tests for malformed inputs and attempts to exceed execution limits.

Passing tests does not, by itself, establish that the sandbox is secure.

## Supported Versions

A supported-version policy has not yet been defined. Check the repository's current release and maintenance status before relying on a version for security-sensitive use.
'@ | Set-Content -Path .\SECURITY.md -Encoding utf8
