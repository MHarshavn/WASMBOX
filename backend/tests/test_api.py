import unittest

try:
    from fastapi.testclient import TestClient
    from backend.api.main import create_app
    from backend.compiler.compiler import Compiler
    from backend.compiler.models import CompilationResult
    from backend.sandbox.emscripten_sandbox import SandboxResult
    from backend.services.orchestrator import Orchestrator
except ModuleNotFoundError:
    TestClient = None


class FakeCompiler(Compiler if TestClient else object):
    def compile(self, source_code, python_version):
        if source_code == "broken":
            return CompilationResult.failed("synthetic failure")
        return CompilationResult.compiled(b"bytecode", "mpy")


class FakeSandbox:
    def execute(self, artifact, input_data, policy, capabilities, artifact_format=None):
        if input_data.get("fail"):
            return SandboxResult("EXECUTION_FAILED", stderr="synthetic runtime failure", execution_time_ms=2, memory_used_mb=1.0, termination_reason="RUNTIME_ERROR")
        return SandboxResult("SUCCESS", stdout="hello", execution_time_ms=2, memory_used_mb=1.0)


@unittest.skipUnless(TestClient, "FastAPI dependencies are not installed")
class TestApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(Orchestrator(FakeCompiler(), sandbox=FakeSandbox())))
        self.headers = {"X-Tenant-ID": "tenant-a"}

    def compile(self, source_code="print('ok')"):
        return self.client.post("/api/v1/plugins/compile", headers=self.headers, json={
            "plugin_name": "demo", "source_code": source_code, "python_version": "3.x"
        })

    def test_compile_invalid_request_and_failure(self):
        invalid = self.client.post("/api/v1/plugins/compile", headers=self.headers, json={})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(invalid.json()["error"]["code"], "INVALID_REQUEST")
        failed = self.compile("broken")
        self.assertEqual(failed.status_code, 400)
        self.assertEqual(failed.json()["status"], "COMPILATION_FAILED")

    def test_compile_execute_and_result(self):
        compiled = self.compile()
        self.assertEqual(compiled.status_code, 200)
        plugin_id = compiled.json()["plugin_id"]
        submitted = self.client.post("/api/v1/plugins/execute", headers=self.headers, json={
            "plugin_id": plugin_id, "input": {}, "limits": {"memory_mb": 10, "timeout_ms": 50}, "capabilities": []
        })
        self.assertEqual(submitted.json()["status"], "RUNNING")
        result = self.client.get(f"/api/v1/executions/{submitted.json()['execution_id']}", headers=self.headers)
        self.assertEqual(result.json()["status"], "SUCCESS")
        self.assertEqual(result.json()["stdout"], "hello")

    def test_missing_plugin_and_tenant_isolation(self):
        missing = self.client.post("/api/v1/plugins/execute", headers=self.headers, json={"plugin_id": "missing"})
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "PLUGIN_NOT_FOUND")
        plugin_id = self.compile().json()["plugin_id"]
        denied = self.client.post("/api/v1/plugins/execute", headers={"X-Tenant-ID": "tenant-b"}, json={"plugin_id": plugin_id})
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.json()["error"]["code"], "TENANT_ACCESS_DENIED")

    def test_metrics_returns_only_actual_tenant_scoped_counts(self):
        empty = self.client.get("/metrics", headers=self.headers)
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json(), {
            "plugins": {"stored": 0},
            "executions": {"stored": 0, "by_status": {}},
        })

        self.compile()
        metrics = self.client.get("/metrics", headers=self.headers)
        self.assertEqual(metrics.status_code, 200)
        self.assertEqual(metrics.json(), {
            "plugins": {"stored": 1},
            "executions": {"stored": 0, "by_status": {}},
        })

        other_tenant = self.client.get("/metrics", headers={"X-Tenant-ID": "tenant-b"})
        self.assertEqual(other_tenant.status_code, 200)
        self.assertEqual(other_tenant.json()["plugins"]["stored"], 0)
