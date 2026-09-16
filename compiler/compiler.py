import ast


class CompilationError(Exception):
    """Raised when Python source cannot be compiled/validated."""
    pass


def validate_source(source: str) -> bool:
    """
    Validate Python source syntax.

    Returns True for valid Python syntax.
    Raises CompilationError for empty or invalid source.
    """
    if not source or not source.strip():
        raise CompilationError("Python source cannot be empty")

    try:
        ast.parse(source)
        return True
    except SyntaxError as exc:
        raise CompilationError(
            f"Invalid Python source at line {exc.lineno}: {exc.msg}"
        ) from exc
