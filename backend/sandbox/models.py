
"""Shared result contract for all WASMBOX sandbox runtimes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxResult:
    """Normalized result returned by every sandbox adapter."""

    status: str
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    memory_used_mb: float = 0.0
    termination_reason: str | None = None
    fuel_consumed: int | None = None
