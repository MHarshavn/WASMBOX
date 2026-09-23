class CompilationError(Exception):
    """Base exception for compiler errors."""

    def __init__(
        self,
        message: str,
        code: str = "COMPILATION_ERROR",
        line: int | None = None,
        column: int | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.line = line
        self.column = column

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
        }