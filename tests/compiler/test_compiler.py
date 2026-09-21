import pytest

from compiler.compiler import validate_python_source
from compiler.errors import CompilationError


def test_valid_python_source():
    source = 'print("Hello WASMBOX")'
    validate_python_source(source)


def test_invalid_python_source():
    source = 'print("Hello"'

    with pytest.raises(CompilationError) as exc_info:
        validate_python_source(source)

    assert exc_info.value.code == "PYTHON_SYNTAX_ERROR"
    assert exc_info.value.line == 1


def test_empty_python_source():
    with pytest.raises(CompilationError) as exc_info:
        validate_python_source("")

    assert exc_info.value.code == "EMPTY_SOURCE"