"""Wasmtime runtime wrapper for WASMBOX sandbox execution."""

from __future__ import annotations

from wasmtime import (
    Config,
    Engine,
    Instance,
    Linker,
    Module,
    Store,
    WasiConfig,
)


class WasmRuntime:
    """WASM runtime with deny-by-default host access and fuel limits."""

    DEFAULT_FUEL = 100_000

    def __init__(self, fuel: int = DEFAULT_FUEL) -> None:
        """Create a WASM runtime with a finite execution budget."""

        if fuel <= 0:
            raise ValueError("fuel must be greater than zero")

        config = Config()

        # Enable Wasmtime fuel consumption.
        # wasmtime-py exposes this as a setter property.
        config.consume_fuel = True

        self.engine = Engine(config)
        self.fuel = fuel

    def execute(self, wasm_bytes: bytes) -> Instance:
        """Load and instantiate a WASM module without host imports."""

        module = Module(self.engine, wasm_bytes)

        store = Store(self.engine)

        store.set_fuel(self.fuel)

        return Instance(store, module, [])

    def execute_wasi(
        self,
        wasm_bytes: bytes,
    ) -> tuple[Store, Instance]:
        """Execute a WASI module with no preopened host directories."""

        module = Module(self.engine, wasm_bytes)

        store = Store(self.engine)

        store.set_fuel(self.fuel)

        wasi = WasiConfig()
        store.set_wasi(wasi)

        linker = Linker(self.engine)
        linker.define_wasi()

        instance = linker.instantiate(store, module)

        return store, instance