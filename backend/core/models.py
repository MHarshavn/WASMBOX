"""Internal records. These do not define the public HTTP contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ResourcePolicy:
    memory_mb: int
    timeout_ms: int
    instruction_limit: int


@dataclass
class PluginRecord:
    plugin_id: str
    tenant_id: str
    plugin_name: str
    source_code: str
    python_version: str
    artifact: bytes
    artifact_format: str
    status: str = "READY"
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class ExecutionRecord:
    execution_id: str
    tenant_id: str
    plugin_id: str
    policy: ResourcePolicy
    capabilities: tuple[str, ...]
    input_data: dict[str, Any]
    status: str = "RUNNING"
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: Optional[int] = None
    memory_used_mb: Optional[float] = None
    termination_reason: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)

    def as_api_response(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "memory_used_mb": self.memory_used_mb,
            "termination_reason": self.termination_reason,
        }
