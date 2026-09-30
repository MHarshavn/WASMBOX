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
    """WASM runtime with deny-by-default host access and resource limits."""

    DEFAULT_FUEL = 100_000
    DEFAULT_MEMORY_LIMIT = 16 * 1024 * 1024  # 16 MiB

    def __init__(
        self,
        fuel: int = DEFAULT_FUEL,
        memory_limit: int = DEFAULT_MEMORY_LIMIT,
    ) -> None:
        """Create a WASM runtime with CPU and memory limits."""

        if fuel <= 0:
            raise ValueError("fuel must be greater than zero")

        if memory_limit <= 0:
            raise ValueError("memory_limit must be greater than zero")

        config = Config()

        # Enable Wasmtime fuel consumption.
        config.consume_fuel = True

        self.engine = Engine(config)
        self.fuel = fuel
        self.memory_limit = memory_limit

    def _create_store(self) -> Store:
        """Create a store with execution and memory limits."""

        store = Store(self.engine)

        # Limit linear memory available to this execution.
        store.set_limits(
            memory_size=self.memory_limit,
            memories=1,
        )

        # Limit CPU execution through Wasmtime fuel.
        store.set_fuel(self.fuel)

        return store

    def execute(self, wasm_bytes: bytes) -> Instance:
        """Load and instantiate a WASM module without host imports."""

        module = Module(self.engine, wasm_bytes)

        store = self._create_store()

        return Instance(store, module, [])

    def execute_wasi(
        self,
        wasm_bytes: bytes,
    ) -> tuple[Store, Instance]:
        """Execute a WASI module with no preopened host directories."""

        module = Module(self.engine, wasm_bytes)

        store = self._create_store()

        wasi = WasiConfig()
        store.set_wasi(wasi)

        linker = Linker(self.engine)
        linker.define_wasi()

        instance = linker.instantiate(store, module)

        return store, instance