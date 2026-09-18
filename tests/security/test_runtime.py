import pytest

from wasmbox.sandbox.runtime import WasmRuntime


def test_wasmtime_can_execute_wasm():
    # Minimal valid WebAssembly module.
    wasm = b"\x00asm\x01\x00\x00\x00"

    runtime = WasmRuntime()
    instance = runtime.execute(wasm)

    assert instance is not None


def test_runtime_rejects_unprovided_host_import():
    # This module requests a host function.
    wasm = """
    (module
        (import "host" "dangerous_operation" (func))
    )
    """

    runtime = WasmRuntime()

    with pytest.raises(Exception):
        runtime.execute(wasm)