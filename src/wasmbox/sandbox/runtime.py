"""Wasmtime runtime wrapper for WASMBOX sandbox execution."""

from __future__ import annotations

from wasmtime import Engine, Instance, Module, Store


class WasmRuntime:
    """Minimal WASM runtime used by WASMBOX."""

    def __init__(self) -> None:
        self.engine = Engine()

    def execute(self, wasm_bytes: bytes) -> Instance:
        """Load and instantiate a WASM module without host imports."""
        module = Module(self.engine, wasm_bytes)
        store = Store(self.engine)

        return Instance(store, module, [])