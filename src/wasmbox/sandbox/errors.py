"""Structured security errors for the WASMBOX sandbox."""

from __future__ import annotations


class SandboxSecurityError(RuntimeError):
    """Base class for security-related sandbox failures."""

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