"""Wasmtime runtime wrapper for WASMBOX sandbox execution."""

from __future__ import annotations

from wasmtime import (
    Engine,
    Instance,
    Linker,
    Module,
    Store,
    WasiConfig,
)


class WasmRuntime:
    """WASM runtime with deny-by-default host access."""

    def __init__(self) -> None:
        self.engine = Engine()

    def execute(self, wasm_bytes: bytes) -> Instance:
        """Load and instantiate a WASM module without host imports."""

        module = Module(self.engine, wasm_bytes)

        store = Store(self.engine)

        return Instance(store, module, [])

    def execute_wasi(
        self,
        wasm_bytes: bytes,
    ) -> tuple[Store, Instance]:
        """Execute a WASI module with no filesystem preopens."""

        module = Module(self.engine, wasm_bytes)

        store = Store(self.engine)

        wasi = WasiConfig()
        store.set_wasi(wasi)

        linker = Linker(self.engine)
        linker.define_wasi()

        instance = linker.instantiate(store, module)

        return store, instance