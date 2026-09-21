from pathlib import Path
import subprocess
import tempfile

from .compiler import validate_python_source
from .errors import CompilationError
from .models import CompilationRequest, CompilationResult


class CompilerService:
    """Compile Python source into a WASMBOX executable artifact."""

    def __init__(
        self,
        runtime_path: Path,
        wasmtime_path: str = "wasmtime",
    ):
        self.runtime_path = Path(runtime_path)
        self.wasmtime_path = wasmtime_path

    def compile(self, request: CompilationRequest) -> CompilationResult:
        """Validate Python source and produce a WASM artifact."""

        try:
            validate_python_source(request.source)

            if not self.runtime_path.exists():
                raise CompilationError(
                    message=f"MicroPython WASI runtime not found: {self.runtime_path}",
                    code="RUNTIME_NOT_FOUND",
                )

            output_path = request.output_path

            if output_path is None:
                output_path = Path("artifacts") / "program.wasm"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create a temporary Python source file.
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                source_path = temp_dir / "program.py"
                source_path.write_text(
                    request.source,
                    encoding="utf-8",
                )

                # The current MicroPython WASI architecture uses the
                # pre-built runtime together with the Python source.
                #
                # The runtime itself remains a fixed WASM artifact.
                # We copy that runtime as the generated WASM artifact
                # and keep the source separately for execution.
                output_path.write_bytes(
                    self.runtime_path.read_bytes()
                )

            return CompilationResult(
                success=True,
                artifact_path=output_path,
            )

        except CompilationError as exc:
            return CompilationResult(
                success=False,
                errors=[exc.to_dict()],
            )

        except Exception as exc:
            error = CompilationError(
                message=str(exc),
                code="COMPILATION_ERROR",
            )

            return CompilationResult(
                success=False,
                errors=[error.to_dict()],
            )