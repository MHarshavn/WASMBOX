"""A guarded adapter for the preserved Emscripten MicroPython runtime.

This is an execution prototype, not a Wasmtime sandbox. It receives only
already-compiled `.mpy` bytes and starts Node with its permission model. No
source is ever evaluated by host Python.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.core.models import ResourcePolicy


@dataclass(frozen=True)
class SandboxResult:
    status: str
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    memory_used_mb: float = 0.0
    termination_reason: str | None = None


class EmscriptenMicroPythonSandbox:
    """Execute `.mpy` under a separately spawned, permission-limited Node process."""

    def __init__(self, repository_root: Path | None = None, node_binary: str = "node") -> None:
        self.repository_root = (repository_root or Path(__file__).resolve().parents[2]).resolve()
        self.node_binary = node_binary
        self.runtime_dir = self.repository_root / "backend" / "compiler"
        self.runner = self.runtime_dir / "emscripten_runner.mjs"

    def execute(
        self, artifact: bytes, input_data: dict[str, Any], policy: ResourcePolicy,
        capabilities: tuple[str, ...],
    ) -> SandboxResult:
        if capabilities:
            return SandboxResult("PERMISSION_DENIED", stderr="No host capabilities are implemented by this runtime.", termination_reason="PERMISSION_DENIED")
        if not artifact:
            return SandboxResult("SANDBOX_ERROR", stderr="Compiled artifact is empty.", termination_reason="SANDBOX_ERROR")
        if not self.runner.is_file():
            return SandboxResult("SANDBOX_ERROR", stderr="Emscripten runner is unavailable.", termination_reason="SANDBOX_ERROR")
        if shutil.which(self.node_binary) is None:
            return SandboxResult("SANDBOX_ERROR", stderr="Node.js is required for the Emscripten runtime adapter.", termination_reason="SANDBOX_ERROR")

        artifact_b64 = base64.b64encode(artifact).decode("ascii")
        input_b64 = base64.b64encode(json.dumps(input_data, separators=(",", ":")).encode("utf-8")).decode("ascii")
        # The checked-in module has a fixed ~16 MiB WebAssembly linear memory
        # and cannot grow. Keep its GC heap below that implementation ceiling.
        # The requested policy is still applied to V8, but is not a complete
        # process-memory enforcement mechanism; see the documentation.
        micropython_heap_bytes = min(policy.memory_mb * 1024 * 1024, 8 * 1024 * 1024)
        command = [
            self.node_binary, "--permission", f"--allow-fs-read={self.runtime_dir}",
            f"--max-old-space-size={policy.memory_mb}", str(self.runner), artifact_b64,
            input_b64, str(micropython_heap_bytes),
        ]
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command, cwd=self.runtime_dir, capture_output=True, text=True,
                timeout=(policy.timeout_ms / 1000) + 0.25, check=False,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult("TIMEOUT", stderr="Execution exceeded its configured timeout.", execution_time_ms=policy.timeout_ms, termination_reason="TIMEOUT")
        except OSError as exc:
            return SandboxResult("SANDBOX_ERROR", stderr=f"Unable to start sandbox runtime: {exc}", termination_reason="SANDBOX_ERROR")

        elapsed_ms = max(1, round((time.perf_counter() - started) * 1000))
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            details = (completed.stderr or completed.stdout).strip()
            return SandboxResult("SANDBOX_ERROR", stderr=details or "Sandbox runner returned an invalid response.", execution_time_ms=elapsed_ms, termination_reason="SANDBOX_ERROR")

        memory_used_mb = round(float(payload.get("rss_bytes", 0)) / (1024 * 1024), 3)
        if completed.returncode != 0 or payload.get("status") != "SUCCESS":
            return SandboxResult("EXECUTION_FAILED", str(payload.get("stdout", "")), str(payload.get("stderr", "Execution failed.")), elapsed_ms, memory_used_mb, "RUNTIME_ERROR")
        return SandboxResult("SUCCESS", str(payload.get("stdout", "")), str(payload.get("stderr", "")), elapsed_ms, memory_used_mb)
