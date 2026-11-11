
"""Coordinates compilation, policy validation, and sandbox execution."""

from __future__ import annotations

from typing import Any

from backend.compiler.compiler import Compiler
from backend.core.models import ExecutionRecord, PluginRecord
from backend.sandbox.models import SandboxResult
from backend.sandbox.router import SandboxRouter
from backend.services.capabilities import CapabilityManager
from backend.services.repository import InMemoryRepository
from backend.services.resources import ResourceManager


class Orchestrator:
    """Keeps API, compiler, and runtime responsibilities separate."""

    def __init__(
        self,
        compiler: Compiler,
        repository: InMemoryRepository | None = None,
        resources: ResourceManager | None = None,
        capabilities: CapabilityManager | None = None,
        sandbox: SandboxRouter | None = None,
    ) -> None:
        self.compiler = compiler
        self.repository = repository or InMemoryRepository()
        self.resources = resources or ResourceManager()
        self.capabilities = capabilities or CapabilityManager()
        self.sandbox = sandbox or SandboxRouter()

    def compile_plugin(
        self,
        *,
        tenant_id: str,
        plugin_name: str,
        source_code: str,
        python_version: str,
    ) -> tuple[PluginRecord | None, dict[str, str] | None]:

        result = self.compiler.compile(source_code, python_version)

        if result.status != "COMPILED" or result.artifact is None:
            error = result.error
            return None, {
                "code": error.code if error else "COMPILATION_ERROR",
                "message": error.message if error else "Plugin compilation failed.",
            }

        if result.artifact_format not in ("mpy", "wasm"):
            return None, {
                "code": "COMPILATION_ERROR",
                "message": "Compiler returned an unsupported artifact format.",
            }

        return self.repository.create_plugin(
            tenant_id=tenant_id,
            plugin_name=plugin_name,
            source_code=source_code,
            python_version=python_version,
            artifact=result.artifact,
            artifact_format=result.artifact_format,
        ), None

    def submit_execution(
        self,
        *,
        tenant_id: str,
        plugin_id: str,
        input_data: dict[str, Any],
        limits: dict[str, Any] | None,
        requested_capabilities: list[str] | None,
    ) -> ExecutionRecord:

        self.repository.get_plugin(plugin_id, tenant_id)
        policy = self.resources.validate(limits)
        capabilities = self.capabilities.validate(requested_capabilities)

        return self.repository.create_execution(
            ExecutionRecord(
                execution_id=self.repository.new_execution_id(),
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                policy=policy,
                capabilities=capabilities,
                input_data=input_data,
            )
        )

    def run_execution(self, execution_id: str, tenant_id: str) -> None:
        execution = self.repository.get_execution(execution_id, tenant_id)
        plugin = self.repository.get_plugin(execution.plugin_id, tenant_id)

        result = self.sandbox.execute(
            plugin.artifact,
            execution.input_data,
            execution.policy,
            execution.capabilities,
            artifact_format=plugin.artifact_format,
        )

        self._apply_result(execution, result)

    @staticmethod
    def _apply_result(
        execution: ExecutionRecord,
        result: SandboxResult,
    ) -> None:
        execution.status = result.status
        execution.stdout = result.stdout
        execution.stderr = result.stderr
        execution.execution_time_ms = result.execution_time_ms
        execution.memory_used_mb = result.memory_used_mb
        execution.termination_reason = result.termination_reason
