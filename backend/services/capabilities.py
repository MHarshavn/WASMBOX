"""Deny-by-default capability policy."""

from __future__ import annotations

from typing import Any

from backend.core.errors import PermissionDenied, WasmboxError


class CapabilityManager:
    """The current prototype intentionally exposes no host functions."""

    SUPPORTED_CAPABILITIES: frozenset[str] = frozenset()

    def validate(self, requested: Any) -> tuple[str, ...]:
        if requested is None:
            return ()
        if not isinstance(requested, list) or not all(isinstance(item, str) for item in requested):
            raise WasmboxError("INVALID_REQUEST", "capabilities must be an array of strings.")
        unknown = set(requested).difference(self.SUPPORTED_CAPABILITIES)
        if unknown:
            raise PermissionDenied("Requested capability is not implemented by this runtime: " + ", ".join(sorted(unknown)))
        return tuple(requested)

    @staticmethod
    def require(granted: tuple[str, ...], capability: str) -> None:
        if capability not in granted:
            raise PermissionDenied()
