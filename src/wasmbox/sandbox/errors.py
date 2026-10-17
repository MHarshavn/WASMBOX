
"""Structured security errors for the WASMBOX sandbox."""

from __future__ import annotations


class SandboxSecurityError(RuntimeError):
    """Base class for structured sandbox and security failures."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class CapabilityDeniedError(PermissionError):
    """Raised when a plugin requests an unauthorized capability."""

    code = "capability_denied"

    def __init__(self, capability: str) -> None:
        self.capability = capability
        self.message = f"Capability denied: {capability}"
        super().__init__(self.message)


class SandboxRuntimeError(SandboxSecurityError):
    """Raised when sandbox execution fails with a classified error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message)
