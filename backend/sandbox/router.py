
"""Selects the appropriate runtime for each compiled artifact."""

from typing import Any

from backend.core.models import ResourcePolicy
from backend.sandbox.emscripten_sandbox import EmscriptenMicroPythonSandbox
from backend.sandbox.models import SandboxResult
from backend.sandbox.wasmtime_sandbox import WasmtimeSandbox


class SandboxRouter:
    """Dispatches artifacts to the runtime matching their format."""

    def __init__(
        self,
        emscripten: EmscriptenMicroPythonSandbox | None = None,
        wasmtime: WasmtimeSandbox | None = None,
    ) -> None:
        self.emscripten = emscripten or EmscriptenMicroPythonSandbox()
        self.wasmtime = wasmtime or WasmtimeSandbox()

    def execute(
        self,
        artifact: bytes,
        input_data: dict[str, Any],
        policy: ResourcePolicy,
        capabilities: tuple[str, ...] = (),
        artifact_format: str | None = None,
    ) -> SandboxResult:

        if artifact_format == "mpy":
            return self.emscripten.execute(
                artifact, input_data, policy, capabilities
            )

        if artifact_format == "wasm":
            return self.wasmtime.execute(
                artifact, input_data, policy, capabilities
            )

        return SandboxResult(
            status="SANDBOX_ERROR",
            stderr=f"Unsupported artifact format: {artifact_format!r}",
            termination_reason="UNSUPPORTED_ARTIFACT_FORMAT",
        )
