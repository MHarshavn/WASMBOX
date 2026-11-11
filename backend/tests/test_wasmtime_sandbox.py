
import unittest

import wasmtime

from backend.core.models import ResourcePolicy
from backend.sandbox.wasmtime_sandbox import WasmtimeSandbox


HELLO_MODULE = r"""
(module
  (import "wasi_snapshot_preview1" "fd_write"
    (func $fd_write (param i32 i32 i32 i32) (result i32)))
  (memory (export "memory") 1)
  (data (i32.const 8) "Hello from Wasmtime!\n")
  (func (export "_start")
    i32.const 0
    i32.const 8
    i32.store

    i32.const 4
    i32.const 21
    i32.store

    i32.const 1
    i32.const 0
    i32.const 1
    i32.const 12
    call $fd_write
    drop
  )
)
"""

INFINITE_LOOP_MODULE = r"""
(module
  (func (export "_start")
    (loop $again
      br $again
    )
  )
)
"""

INITIALIZATION_LOOP_MODULE = r"""
(module
  (func $initialize
    (loop $again
      br $again
    )
  )
  (start $initialize)
  (func (export "_start"))
)
"""


class TestWasmtimeSandbox(unittest.TestCase):

    def setUp(self):
        self.sandbox = WasmtimeSandbox()
        self.policy = ResourcePolicy(
            memory_mb=10,
            timeout_ms=2000,
            instruction_limit=100_000,
        )

    def test_executes_real_wasi_module(self):
        artifact = wasmtime.wat2wasm(HELLO_MODULE)

        result = self.sandbox.execute(
            bytes(artifact),
            {},
            self.policy,
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertIn("Hello from Wasmtime!", result.stdout)
        self.assertGreater(result.execution_time_ms, 0)
        self.assertIsNotNone(result.fuel_consumed)

    def test_rejects_invalid_wasm(self):
        result = self.sandbox.execute(
            b"not a wasm module",
            {},
            self.policy,
        )

        self.assertEqual(result.status, "SANDBOX_ERROR")

    def test_fuel_limit_stops_infinite_loop(self):
        artifact = wasmtime.wat2wasm(INFINITE_LOOP_MODULE)

        policy = ResourcePolicy(
            memory_mb=10,
            timeout_ms=5000,
            instruction_limit=1000,
        )

        result = self.sandbox.execute(
            bytes(artifact),
            {},
            policy,
        )

        self.assertEqual(result.status, "INSTRUCTION_LIMIT")
        self.assertEqual(
            result.termination_reason,
            "INSTRUCTION_LIMIT",
        )
    def test_timeout_stops_infinite_initialization(self):
        artifact = wasmtime.wat2wasm(INITIALIZATION_LOOP_MODULE)

        policy = ResourcePolicy(
            memory_mb=10,
            timeout_ms=200,
            instruction_limit=10_000_000_000,
        )

        result = self.sandbox.execute(
            bytes(artifact),
            {},
            policy,
        )

        self.assertEqual(result.status, "TIMEOUT")
        self.assertEqual(result.termination_reason, "TIMEOUT")

    def test_denies_unimplemented_capabilities(self):
        artifact = wasmtime.wat2wasm(HELLO_MODULE)

        result = self.sandbox.execute(
            bytes(artifact),
            {},
            self.policy,
            capabilities=("filesystem.read",),
        )

        self.assertEqual(result.status, "PERMISSION_DENIED")


if __name__ == "__main__":
    unittest.main()
