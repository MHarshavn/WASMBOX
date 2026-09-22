import argparse
from pathlib import Path

from .models import CompilationRequest
from .service import CompilerService


DEFAULT_RUNTIME = Path(
    "toolchain/micropython-wasi/ports/unix/build-wasi/"
    "micropython.spilled.exnref"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile Python source into a WASMBOX WASM artifact."
    )

    parser.add_argument(
        "source",
        type=Path,
        help="Path to the Python source file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/program.wasm"),
        help="Output WASM artifact path.",
    )

    parser.add_argument(
        "--runtime",
        type=Path,
        default=DEFAULT_RUNTIME,
        help="Path to the MicroPython WASI runtime.",
    )

    args = parser.parse_args()

    if not args.source.exists():
        print(f"ERROR: source file not found: {args.source}")
        return 1

    source = args.source.read_text(encoding="utf-8")

    service = CompilerService(
        runtime_path=args.runtime,
    )

    request = CompilationRequest(
        source=source,
        output_path=args.output,
    )

    result = service.compile(request)

    if result.success:
        print(f"Compilation successful: {result.artifact_path}")
        return 0

    print("Compilation failed:")

    for error in result.errors:
        print(f"  [{error['code']}] {error['message']}")

        if error.get("line") is not None:
            print(
                f"    at line {error['line']}, "
                f"column {error.get('column')}"
            )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())