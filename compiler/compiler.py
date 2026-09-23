import ast

from .errors import CompilationError


def validate_python_source(source: str) -> None:
    """Validate Python source before sending it to the WASM runtime."""

    if not source or not source.strip():
        raise CompilationError(
            message="Python source cannot be empty",
            code="EMPTY_SOURCE",
        )

    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise CompilationError(
            message=exc.msg,
            code="PYTHON_SYNTAX_ERROR",
            line=exc.lineno,
            column=exc.offset,
        ) from exc