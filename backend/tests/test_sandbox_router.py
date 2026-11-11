
import unittest
from unittest.mock import Mock

from backend.core.models import ResourcePolicy
from backend.sandbox.models import SandboxResult
from backend.sandbox.router import SandboxRouter


class TestSandboxRouter(unittest.TestCase):

    def setUp(self):
        self.emscripten = Mock()
        self.wasmtime = Mock()

        self.emscripten.execute.return_value = SandboxResult(
            status="SUCCESS",
            stdout="Executed using Emscripten",
        )

        self.wasmtime.execute.return_value = SandboxResult(
            status="SUCCESS",
            stdout="Executed using Wasmtime",
        )

        self.router = SandboxRouter(
            emscripten=self.emscripten,
            wasmtime=self.wasmtime,
        )

        self.policy = ResourcePolicy(
            memory_mb=10,
            timeout_ms=2000,
            instruction_limit=100000,
        )

    def test_mpy_routes_to_emscripten(self):
        result = self.router.execute(
            b"mpy-artifact",
            {},
            self.policy,
            artifact_format="mpy",
        )

        self.emscripten.execute.assert_called_once()
        self.wasmtime.execute.assert_not_called()
        self.assertEqual(result.stdout, "Executed using Emscripten")

    def test_wasm_routes_to_wasmtime(self):
        result = self.router.execute(
            b"wasm-artifact",
            {},
            self.policy,
            artifact_format="wasm",
        )

        self.wasmtime.execute.assert_called_once()
        self.emscripten.execute.assert_not_called()
        self.assertEqual(result.stdout, "Executed using Wasmtime")

    def test_unknown_format_is_rejected(self):
        result = self.router.execute(
            b"unknown-artifact",
            {},
            self.policy,
            artifact_format="unknown",
        )

        self.emscripten.execute.assert_not_called()
        self.wasmtime.execute.assert_not_called()
        self.assertEqual(result.status, "SANDBOX_ERROR")
        self.assertEqual(
            result.termination_reason,
            "UNSUPPORTED_ARTIFACT_FORMAT",
        )


if __name__ == "__main__":
    unittest.main()
