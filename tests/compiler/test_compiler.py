import pytest

from compiler.compiler import CompilationError, validate_source


def test_valid_python_source():
    validate_source('print("Hello WASMBOX")')


def test_invalid_python_source():
    with pytest.raises(CompilationError):
        validate_source('print("Hello"')


def test_empty_python_source():
    with pytest.raises(CompilationError):
        validate_source("")
