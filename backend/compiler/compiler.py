
from abc import ABC, abstractmethod

from .models import CompilationResult


class Compiler(ABC):
    """Interface for converting supported Python source into WASM."""

    @abstractmethod
    def compile(
        self,
        source_code: str,
        python_version: str,
    ) -> CompilationResult:
        """Compile supported Python source into a WASM artifact."""
        raise NotImplementedError
