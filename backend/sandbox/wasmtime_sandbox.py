
"""Wasmtime WASI Preview 1 execution adapter.

This runtime executes genuine WASI-compatible WebAssembly modules.
It does not execute MicroPython .mpy bytecode.
"""

from __future__ import annotations
from email import policy
import json
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import wasmtime
from backend.core.models import ResourcePolicy
from backend.sandbox.models import SandboxResult





class WasmtimeSandbox:
    """Execute one WASI Preview 1 command module in a fresh Wasmtime engine."""

    def __init__(self, max_output_bytes: int = 65_536) -> None:
        if max_output_bytes < 1:
            raise ValueError("max_output_bytes must be positive")
        self.max_output_bytes = max_output_bytes

    def execute(
        self,
        artifact: bytes,
        input_data: dict[str, Any],
        policy: ResourcePolicy,
        capabilities: tuple[str, ...] = (),
    ) -> SandboxResult:
        if capabilities:
            return SandboxResult(
                "PERMISSION_DENIED",
                stderr="No host capabilities are enabled in this Wasmtime adapter.",
                termination_reason="PERMISSION_DENIED",
            )

        if not artifact:
            return SandboxResult(
                "SANDBOX_ERROR",
                stderr="WebAssembly artifact is empty.",
                termination_reason="SANDBOX_ERROR",
            )

        if policy.memory_mb < 1 or policy.timeout_ms < 1:
            return SandboxResult(
                "SANDBOX_ERROR",
                stderr="Memory and timeout limits must be positive.",
                termination_reason="INVALID_RESOURCE_POLICY",
            )

        started = time.perf_counter()
        timed_out = threading.Event()

        config = wasmtime.Config()
        config.consume_fuel = True
        config.epoch_interruption = True

        engine = wasmtime.Engine(config)
        timer: threading.Timer | None = None

        try:
            module = wasmtime.Module(engine, artifact)

            with tempfile.TemporaryDirectory(prefix="wasmbox-wasi-") as temp:
                temp_dir = Path(temp)
                stdout_path = temp_dir / "stdout.txt"
                stderr_path = temp_dir / "stderr.txt"
                stdin_path = temp_dir / "stdin.json"

                stdin_path.write_text(
                    json.dumps(input_data, separators=(",", ":")),
                    encoding="utf-8",
                )

                store = wasmtime.Store(engine)
                # Configure epoch interruption before any WebAssembly executes.
                store.set_epoch_deadline(1)

                # Enforce a limit on WebAssembly linear memory and instance
                # resources. This is not a limit on the entire Python process.
                store.set_limits(
                    memory_size=policy.memory_mb * 1024 * 1024,
                    instances=1,
                    memories=1,
                    tables=10,
                    table_elements=10_000,
                )

                store.set_fuel(policy.instruction_limit)

                wasi = wasmtime.WasiConfig()
                wasi.stdin_file = str(stdin_path)
                wasi.stdout_file = str(stdout_path)
                wasi.stderr_file = str(stderr_path)

                # Deliberately do not inherit host environment, arguments,
                # filesystem directories, or network capabilities.
                store.set_wasi(wasi)

                linker = wasmtime.Linker(engine)
                linker.define_wasi()


                def interrupt_execution() -> None:
                    timed_out.set()
                    engine.increment_epoch()


                timer = threading.Timer(
                    policy.timeout_ms / 1000,
                    interrupt_execution,
                )
                timer.daemon = True
                timer.start()

                instance = linker.instantiate(store, module)

                exports = instance.exports(store)
                start_function = exports.get("_start")

                if start_function is None:
                    return SandboxResult(
                        "SANDBOX_ERROR",
                        stderr="WASI command module does not export _start.",
                        termination_reason="INVALID_WASI_MODULE",
                    )






                execution_error: Exception | None = None

                try:
                    start_function(store)
                except Exception as exc:
                    execution_error = exc
                finally:
                    timer.cancel()

                elapsed_ms = max(
                    1,
                    round((time.perf_counter() - started) * 1000),
                )

                remaining_fuel: int | None
                try:
                    remaining_fuel = store.get_fuel()
                except Exception:
                    remaining_fuel = None

                fuel_consumed = (
                    policy.instruction_limit - remaining_fuel
                    if remaining_fuel is not None
                    else None
                )

                stdout_bytes = (
                    stdout_path.read_bytes() if stdout_path.exists() else b""
                )
                stderr_bytes = (
                    stderr_path.read_bytes() if stderr_path.exists() else b""
                )

                output_exceeded = (
                    len(stdout_bytes) + len(stderr_bytes)
                    > self.max_output_bytes
                )

                stdout = stdout_bytes[: self.max_output_bytes].decode(
                    "utf-8", errors="replace"
                )
                remaining_output = max(
                    0, self.max_output_bytes - len(stdout_bytes)
                )
                stderr = stderr_bytes[:remaining_output].decode(
                    "utf-8", errors="replace"
                )

                memory_used_mb = 0.0
                memory = exports.get("memory")
                if memory is not None:
                    memory_used_mb = round(
                        memory.size(store) * 65_536 / (1024 * 1024), 3
                    )

                if timed_out.is_set():
                    return SandboxResult(
                        "TIMEOUT", stdout, stderr, elapsed_ms,
                        memory_used_mb, "TIMEOUT", fuel_consumed,
                    )

                if output_exceeded:
                    return SandboxResult(
                        "OUTPUT_LIMIT",
                        stdout,
                        stderr,
                        elapsed_ms,
                        memory_used_mb,
                        "OUTPUT_LIMIT",
                        fuel_consumed,
                    )

                if execution_error is not None:
                    message = str(execution_error)

                    if "fuel" in message.lower():
                        return SandboxResult(
                            "INSTRUCTION_LIMIT",
                            stdout,
                            stderr or message,
                            elapsed_ms,
                            memory_used_mb,
                            "INSTRUCTION_LIMIT",
                            fuel_consumed,
                        )

                    return SandboxResult(
                        "EXECUTION_FAILED",
                        stdout,
                        stderr or message,
                        elapsed_ms,
                        memory_used_mb,
                        "RUNTIME_ERROR",
                        fuel_consumed,
                    )

                return SandboxResult(
                    "SUCCESS",
                    stdout,
                    stderr,
                    elapsed_ms,
                    memory_used_mb,
                    None,
                    fuel_consumed,
                )

        except Exception as exc:
            elapsed_ms = max(
                1,
                round((time.perf_counter() - started) * 1000),
            )

            if timed_out.is_set():
                return SandboxResult(
                   "TIMEOUT",
                    stderr="Execution timed out during WebAssembly initialization.",
                    execution_time_ms=elapsed_ms,
                    termination_reason="TIMEOUT",
                )

            return SandboxResult(
                "SANDBOX_ERROR",
                stderr=str(exc),
                execution_time_ms=elapsed_ms,
                termination_reason="WASMTIME_ERROR",
            )
        finally:
            if timer is not None:
                timer.cancel()
