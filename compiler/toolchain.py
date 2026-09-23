from pathlib import Path
import subprocess


MICROPYTHON_REVISION = "52b5fbcb4b7961356c83ba0c533ee42acdfa0169"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MICROPYTHON_DIR = PROJECT_ROOT / "toolchain" / "micropython"


class ToolchainError(Exception):
    """Raised when the WASM toolchain is not correctly configured."""


class WasmToolchain:
    """Describes and validates the WASMBOX MicroPython toolchain."""

    def __init__(self, micropython_dir: Path = MICROPYTHON_DIR):
        self.micropython_dir = Path(micropython_dir)

    def validate(self) -> None:
        if not self.micropython_dir.exists():
            raise ToolchainError(
                f"MicroPython source directory not found: {self.micropython_dir}"
            )

        if not (self.micropython_dir / ".git").exists():
            raise ToolchainError(
                f"MicroPython directory is not a Git repository: "
                f"{self.micropython_dir}"
            )

        mpy_cross = self.micropython_dir / "mpy-cross"

        if not mpy_cross.exists():
            raise ToolchainError(
                f"mpy-cross directory not found: {mpy_cross}"
            )

        actual_revision = self.current_revision()

        if actual_revision != MICROPYTHON_REVISION:
            raise ToolchainError(
                "MicroPython revision mismatch: "
                f"expected {MICROPYTHON_REVISION}, "
                f"found {actual_revision}"
            )

    def current_revision(self) -> str:
        """Return the actual checked-out MicroPython Git revision."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.micropython_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, OSError) as exc:
            raise ToolchainError(
                "Unable to determine MicroPython Git revision"
            ) from exc

        return result.stdout.strip()

    def revision(self) -> str:
        """Return the expected pinned MicroPython revision."""
        return MICROPYTHON_REVISION
