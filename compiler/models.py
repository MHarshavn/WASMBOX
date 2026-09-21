from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CompilationRequest:
    """Input provided to the compiler service."""

    source: str
    output_path: Path | None = None


@dataclass
class CompilationResult:
    """Result returned by the compiler service."""

    success: bool
    artifact_path: Path | None = None
    errors: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "artifact_path": (
                str(self.artifact_path)
                if self.artifact_path
                else None
            ),
            "errors": self.errors,
        }