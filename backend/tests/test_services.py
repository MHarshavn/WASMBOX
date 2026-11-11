import unittest

from backend.compiler.compiler import Compiler
from backend.compiler.models import CompilationResult
from backend.core.errors import PermissionDenied, TenantAccessDenied, WasmboxError
from backend.sandbox.emscripten_sandbox import SandboxResult
from backend.services.capabilities import CapabilityManager
from backend.services.orchestrator import Orchestrator


class FakeCompiler(Compiler):
    def compile(self, source_code, python_version):
        if source_code == "bad":
            return CompilationResult.failed("synthetic compiler failure")

        if source_code == "wasm":
            return CompilationResult.compiled(b"test-wasm", "wasm")

        return CompilationResult.compiled(b"test-bytecode", "mpy")


class FakeSandbox:
    def __init__(self):
        self.last_artifact_format = None

    def execute(self, artifact, input_data, policy, capabilities, artifact_format=None):
        self.last_artifact_format = artifact_format

        return SandboxResult(
            "SUCCESS",
            stdout=f"input={input_data['value']}",
            execution_time_ms=7,
            memory_used_mb=2.5,
        )


class TestServices(unittest.TestCase):
    def setUp(self):
        self.fake_sandbox = FakeSandbox()
        self.orchestrator = Orchestrator(
            FakeCompiler(),
            sandbox=self.fake_sandbox,
        )

    def test_compile_execute_and_retrieve(self):
        plugin, error = self.orchestrator.compile_plugin(
            tenant_id="tenant-a", plugin_name="demo", source_code="print(1)", python_version="3.x"
        )
        self.assertIsNone(error)
        execution = self.orchestrator.submit_execution(
            tenant_id="tenant-a", plugin_id=plugin.plugin_id, input_data={"value": 3},
            limits={"memory_mb": 10, "timeout_ms": 50, "instruction_limit": 100}, requested_capabilities=[]
        )
        self.assertEqual(execution.status, "RUNNING")
        self.orchestrator.run_execution(execution.execution_id, "tenant-a")
        result = self.orchestrator.repository.get_execution(execution.execution_id, "tenant-a")
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.stdout, "input=3")
        self.assertEqual(result.execution_time_ms, 7)
        self.assertEqual(self.fake_sandbox.last_artifact_format, "mpy")
    def test_wasm_artifact_format_reaches_sandbox(self):
        plugin, error = self.orchestrator.compile_plugin(
            tenant_id="tenant-a",
            plugin_name="wasm-demo",
            source_code="wasm",
            python_version="3.x",
        )

        self.assertIsNone(error)
        self.assertEqual(plugin.artifact_format, "wasm")

        execution = self.orchestrator.submit_execution(
            tenant_id="tenant-a",
            plugin_id=plugin.plugin_id,
            input_data={"value": 10},
            limits={},
            requested_capabilities=[],
        )

        self.orchestrator.run_execution(
            execution.execution_id,
            "tenant-a",
        )

        self.assertEqual(
            self.fake_sandbox.last_artifact_format,
            "wasm",
        )
    def test_compiler_failure_is_preserved(self):
        plugin, error = self.orchestrator.compile_plugin(
            tenant_id="tenant-a", plugin_name="demo", source_code="bad", python_version="3.x"
        )
        self.assertIsNone(plugin)
        self.assertEqual(error["code"], "COMPILATION_ERROR")

    def test_tenants_cannot_cross_access(self):
        plugin, _ = self.orchestrator.compile_plugin(
            tenant_id="tenant-a", plugin_name="demo", source_code="print(1)", python_version="3.x"
        )
        with self.assertRaises(TenantAccessDenied):
            self.orchestrator.submit_execution(
                tenant_id="tenant-b", plugin_id=plugin.plugin_id, input_data={}, limits={}, requested_capabilities=[]
            )

    def test_limits_and_capabilities_fail_closed(self):
        with self.assertRaises(WasmboxError):
            self.orchestrator.resources.validate({"timeout_ms": 5001})
        with self.assertRaises(PermissionDenied):
            CapabilityManager().validate(["host.log"])
        with self.assertRaises(PermissionDenied):
            CapabilityManager.require((), "host.log")

    def test_metrics_are_derived_from_tenant_records(self):
        plugin, _ = self.orchestrator.compile_plugin(
            tenant_id="tenant-a", plugin_name="demo", source_code="print(1)", python_version="3.x"
        )
        self.orchestrator.submit_execution(
            tenant_id="tenant-a", plugin_id=plugin.plugin_id, input_data={},
            limits={}, requested_capabilities=[]
        )
        self.assertEqual(self.orchestrator.repository.metrics_for_tenant("tenant-a"), {
            "plugins": {"stored": 1},
            "executions": {"stored": 1, "by_status": {"RUNNING": 1}},
        })
        self.assertEqual(self.orchestrator.repository.metrics_for_tenant("tenant-b"), {
            "plugins": {"stored": 0},
            "executions": {"stored": 0, "by_status": {}},
        })
