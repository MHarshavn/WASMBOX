"""Thread-safe, tenant-scoped in-memory storage for the demonstration service."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from backend.core.errors import ExecutionNotFound, PluginNotFound, TenantAccessDenied
from backend.core.models import ExecutionRecord, PluginRecord


class InMemoryRepository:
    """Stores artifacts in process memory only; no tenant artifact reaches disk."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginRecord] = {}
        self._executions: dict[str, ExecutionRecord] = {}
        self._lock = RLock()

    def create_plugin(
        self, *, tenant_id: str, plugin_name: str, source_code: str,
        python_version: str, artifact: bytes, artifact_format: str,
    ) -> PluginRecord:
        record = PluginRecord(
            plugin_id=f"plugin-{uuid4().hex}", tenant_id=tenant_id,
            plugin_name=plugin_name, source_code=source_code,
            python_version=python_version, artifact=artifact,
            artifact_format=artifact_format,
        )
        with self._lock:
            self._plugins[record.plugin_id] = record
        return record

    def get_plugin(self, plugin_id: str, tenant_id: str) -> PluginRecord:
        with self._lock:
            record = self._plugins.get(plugin_id)
            if record is None:
                raise PluginNotFound(plugin_id)
            if record.tenant_id != tenant_id:
                raise TenantAccessDenied()
            return record

    def create_execution(self, record: ExecutionRecord) -> ExecutionRecord:
        with self._lock:
            self._executions[record.execution_id] = record
        return record

    def new_execution_id(self) -> str:
        return f"execution-{uuid4().hex}"

    def get_execution(self, execution_id: str, tenant_id: str) -> ExecutionRecord:
        with self._lock:
            record = self._executions.get(execution_id)
            if record is None:
                raise ExecutionNotFound(execution_id)
            if record.tenant_id != tenant_id:
                raise TenantAccessDenied()
            return record

    def metrics_for_tenant(self, tenant_id: str) -> dict[str, object]:
        """Return only counters that can be derived from this process's records."""
        with self._lock:
            plugin_count = sum(
                1 for plugin in self._plugins.values() if plugin.tenant_id == tenant_id
            )
            executions = [
                execution
                for execution in self._executions.values()
                if execution.tenant_id == tenant_id
            ]

        by_status: dict[str, int] = {}
        for execution in executions:
            by_status[execution.status] = by_status.get(execution.status, 0) + 1

        return {
            "plugins": {"stored": plugin_count},
            "executions": {"stored": len(executions), "by_status": by_status},
        }
