from pathlib import Path
import subprocess
import tempfile

from .compiler import validate_python_source
from .errors import CompilationError
from .models import CompilationRequest, CompilationResult


class CompilerService:
    """Compile Python source into a source-specific WASM artifact."""

    def __init__(
        self,
        runtime_path: Path,
        wasmtime_path: str = "wasmtime",
        wsl_distribution: str = "Ubuntu",
    ):
        self.runtime_path = Path(runtime_path)
        self.wasmtime_path = wasmtime_path
        self.wsl_distribution = wsl_distribution

    def compile(self, request: CompilationRequest) -> CompilationResult:
        """Validate Python source and compile it into a WASM artifact."""

        try:
            validate_python_source(request.source)

            if not self.runtime_path.exists():
                raise CompilationError(
                    message=(
                        f"MicroPython WASI runtime not found: "
                        f"{self.runtime_path}"
                    ),
                    code="RUNTIME_NOT_FOUND",
                )

            output_path = request.output_path

            if output_path is None:
                output_path = Path("artifacts") / "program.wasm"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.TemporaryDirectory(
                prefix="wasmbox_compile_"
            ) as temp_dir:

                temp_dir = Path(temp_dir)

                source_path = temp_dir / "program.py"
                manifest_path = temp_dir / "manifest.py"

                source_path.write_text(
                    request.source,
                    encoding="utf-8",
                )

                manifest_path.write_text(
                    'module("program.py")\n',
                    encoding="utf-8",
                )

                artifact = self._build_wasm(
                    source_path=source_path,
                    manifest_path=manifest_path,
                )

                output_path.write_bytes(
                    artifact.read_bytes()
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

    def _build_wasm(
        self,
        source_path: Path,
        manifest_path: Path,
    ) -> Path:
        """Build the MicroPython WASI runtime with frozen Python source."""

        repo_path = self.runtime_path.parent.parent.parent.parent

        wsl_repo_path = self._windows_to_wsl_path(repo_path)
        wsl_manifest_path = self._windows_to_wsl_path(manifest_path)

        command = [
            "wsl.exe",
            "-d",
            self.wsl_distribution,
            "--",
            "bash",
            "-lc",
            (
                f"cd '{wsl_repo_path}' && "
                "make -C ports/unix clean && "
                "make -C ports/unix "
                "VARIANT=wasi "
                f"FROZEN_MANIFEST='{wsl_manifest_path}'"
            ),
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        if process.returncode != 0:
            diagnostics = (
                process.stderr.strip()
                or process.stdout.strip()
                or "MicroPython WASI build failed."
            )

            raise CompilationError(
                message=diagnostics,
                code="MICROPYTHON_BUILD_ERROR",
            )

        artifact = (
            self.runtime_path.parent
            / "micropython.spilled.exnref"
        )

        if not artifact.exists():
            raise CompilationError(
                message=(
                    "MicroPython build completed but the expected "
                    "WASM artifact was not generated."
                ),
                code="WASM_ARTIFACT_NOT_FOUND",
            )

        return artifact

    @staticmethod
    def _windows_to_wsl_path(path: Path) -> str:
        """Convert a Windows path into a /mnt/<drive>/ WSL path."""

        resolved = path.resolve()

        drive = resolved.drive.rstrip(":").lower()
        remaining = resolved.as_posix()[2:]

        return f"/mnt/{drive}{remaining}"