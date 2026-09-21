from pathlib import Path

from compiler.service import CompilerService
from compiler.models import CompilationRequest


runtime = Path(
    "toolchain/micropython-wasi/ports/unix/build-wasi/"
    "micropython.spilled.exnref"
)

service = CompilerService(runtime)

request = CompilationRequest(
    source='print("Hello from CompilerService")',
    output_path=Path("artifacts/hello.wasm"),
)

result = service.compile(request)

print(result.to_dict())