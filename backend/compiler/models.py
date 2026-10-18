
from dataclasses import dataclass
from typing import Optional


@dataclass
class CompilationError:
    code: str
    message: str


@dataclass
class CompilationResult:
    status: str
    artifact: Optional[bytes] = None
    artifact_format: Optional[str] = None
    error: Optional[CompilationError] = None

    @classmethod
    def compiled(
        cls,
        artifact: bytes,
        artifact_format: str,
    ) -> "CompilationResult":
        return cls(
            status="COMPILED",
            artifact=artifact,
            artifact_format=artifact_format,
        )

    @classmethod
    def failed(cls, message: str) -> "CompilationResult":
        return cls(
            status="COMPILATION_FAILED",
            error=CompilationError(
                code="COMPILATION_ERROR",
                message=message,
            ),
        )
