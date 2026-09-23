from pathlib import Path

from compiler.models import CompilationRequest
from compiler.service import CompilerService


RUNTIME = Path(
    "toolchain/micropython-wasi/ports/unix/build-wasi/"
    "micropython.spilled.exnref"
)


def create_service():
    return CompilerService(RUNTIME)


def test_compile_valid_python(tmp_path):
    service = create_service()

    request = CompilationRequest(
        source="""
print("Hello from automated test")
x = 10
y = 20
print(x + y)
""",
        output_path=tmp_path / "program.wasm",
    )

    result = service.compile(request)

    assert result.success is True
    assert result.artifact_path is not None
    assert result.artifact_path.exists()
    assert result.artifact_path.stat().st_size > 0


def test_compile_invalid_python():
    service = create_service()

    request = CompilationRequest(
        source='print("hello"',
    )

    result = service.compile(request)

    assert result.success is False
    assert result.artifact_path is None
    assert len(result.errors) == 1

    error = result.errors[0]

    assert error["code"] == "PYTHON_SYNTAX_ERROR"
    assert error["line"] == 1


def test_compile_empty_source():
    service = create_service()

    request = CompilationRequest(
        source="",
    )

    result = service.compile(request)

    assert result.success is False
    assert result.artifact_path is None
    assert len(result.errors) == 1

    error = result.errors[0]

    assert error["code"] == "EMPTY_SOURCE"


def test_missing_runtime():
    service = CompilerService(
        Path("toolchain/micropython-wasi/does-not-exist.wasm")
    )

    request = CompilationRequest(
        source='print("hello")',
    )

    result = service.compile(request)

    assert result.success is False
    assert result.artifact_path is None
    assert len(result.errors) == 1

    error = result.errors[0]

    assert error["code"] == "RUNTIME_NOT_FOUND"