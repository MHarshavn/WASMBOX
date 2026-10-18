
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

from .compiler import Compiler
from .models import CompilationResult


class MicroPythonCompiler(Compiler):
    """Compile supported Python source to MicroPython bytecode (.mpy).

    Note: this produces .mpy bytecode, not a standalone .wasm module.
    The WebAssembly runtime is a separate artifact.
    """

    def __init__(
        self,
        repository_root: Path | None = None,
        docker_image: str = "emscripten/emsdk:latest",
    ) -> None:
        self.repository_root = (
            repository_root or Path(__file__).resolve().parents[2]
        ).resolve()
        self.docker_image = docker_image

        source_root = self.repository_root / "tools" / "micropython" / "source"
        self.mpy_cross_relative = (
            source_root / "mpy-cross" / "build" / "mpy-cross"
        ).relative_to(self.repository_root).as_posix()

    def compile(
        self,
        source_code: str,
        python_version: str,
    ) -> CompilationResult:
        if not isinstance(source_code, str) or not source_code.strip():
            return CompilationResult.failed("Source code must not be empty.")

        if not isinstance(python_version, str) or not python_version.strip():
            return CompilationResult.failed("Python version must be specified.")

        # Avoid passing arbitrary command-line flags through the version field.
        if not re.fullmatch(r"[A-Za-z0-9._+-]+", python_version):
            return CompilationResult.failed("Invalid Python version value.")

        if not (self.repository_root / self.mpy_cross_relative).is_file():
            return CompilationResult.failed(
                "MicroPython mpy-cross compiler was not found."
            )

        try:
            with tempfile.TemporaryDirectory(prefix="wasmbox-compile-") as temp:
                temp_dir = Path(temp)
                source_file = temp_dir / "plugin.py"
                output_file = temp_dir / "plugin.mpy"

                source_file.write_text(source_code, encoding="utf-8")

                # The temporary directory is mounted into the container.
                mount_path = "/wasmbox-tmp"
                source_root = self.repository_root / "tools" / "micropython" / "source"
                compiler_path = f"/workspace/{self.mpy_cross_relative}"

                command = [
                    "docker", "run", "--rm",
                    "-v", f"{self.repository_root}:/workspace",
                    "-v", f"{temp_dir}:{mount_path}",
                    "-w", "/workspace",
                    self.docker_image,
                    "bash", "-lc",
                    (
                        f'"{compiler_path}" '
                        f'-o "{mount_path}/plugin.mpy" '
                        f'"{mount_path}/plugin.py"'
                    ),
                ]

                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )

                if completed.returncode != 0:
                    details = (completed.stderr or completed.stdout).strip()
                    return CompilationResult.failed(
                        details or "MicroPython compilation failed."
                    )

                if not output_file.is_file():
                    return CompilationResult.failed(
                        "Compiler completed without producing bytecode."
                    )

                bytecode = output_file.read_bytes()
                if not bytecode:
                    return CompilationResult.failed(
                        "Compiler produced an empty bytecode artifact."
                    )

                return CompilationResult.compiled(
                    artifact=bytecode,
                    artifact_format="mpy",
                )

        except subprocess.TimeoutExpired:
            return CompilationResult.failed("Compilation timed out.")
        except FileNotFoundError:
            return CompilationResult.failed(
                "Docker was not found. Ensure Docker Desktop is running."
            )
        except OSError as exc:
            return CompilationResult.failed(f"Compilation failed: {exc}")
