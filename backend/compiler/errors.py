class CompilationError(Exception):
    """Base exception raised when compilation fails."""

    def __init__(self, message: str):
        super().__init__(message)
        self.code = "COMPILATION_ERROR"
        self.message = message