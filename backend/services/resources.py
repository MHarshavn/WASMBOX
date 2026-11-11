"""Platform-level validation for execution resource policies."""

from __future__ import annotations

from typing import Any

from backend.core.errors import WasmboxError
from backend.core.models import ResourcePolicy


class ResourceManager:
    """Validate request limits before they reach an execution runtime."""

    DEFAULT_MEMORY_MB = 128
    DEFAULT_TIMEOUT_MS = 5000
    DEFAULT_INSTRUCTION_LIMIT = 1_000_000
    MAX_MEMORY_MB = 128
    MAX_TIMEOUT_MS = 5000
    MAX_INSTRUCTION_LIMIT = 1_000_000

    def validate(self, requested: dict[str, Any] | None) -> ResourcePolicy:
        requested = requested or {}
        if not isinstance(requested, dict):
            raise WasmboxError("INVALID_REQUEST", "limits must be an object.")
        memory_mb = requested.get("memory_mb", self.DEFAULT_MEMORY_MB)
        timeout_ms = requested.get("timeout_ms", self.DEFAULT_TIMEOUT_MS)
        instruction_limit = requested.get("instruction_limit", self.DEFAULT_INSTRUCTION_LIMIT)
        self._validate_integer("memory_mb", memory_mb, 1, self.MAX_MEMORY_MB)
        self._validate_integer("timeout_ms", timeout_ms, 1, self.MAX_TIMEOUT_MS)
        self._validate_integer("instruction_limit", instruction_limit, 1, self.MAX_INSTRUCTION_LIMIT)
        return ResourcePolicy(memory_mb, timeout_ms, instruction_limit)

    @staticmethod
    def _validate_integer(name: str, value: Any, minimum: int, maximum: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise WasmboxError("INVALID_REQUEST", f"{name} must be an integer.")
        if not minimum <= value <= maximum:
            raise WasmboxError("INVALID_REQUEST", f"{name} must be between {minimum} and {maximum}.")
