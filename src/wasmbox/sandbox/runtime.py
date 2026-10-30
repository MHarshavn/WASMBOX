"""Wasmtime runtime wrapper for WASMBOX sandbox execution."""

from __future__ import annotations

from wasmtime import (
    Config,
    Engine,
    FuncType,
    Instance,
    Linker,
    Module,
    Store,
    ValType,
    WasiConfig,
)

from wasmbox.sandbox.host import host_log_wasm
from wasmbox.sandbox.policy import SecurityPolicy, default_policy
from wasmbox.sandbox.errors import SandboxRuntimeError


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

        # Enable Wasmtime fuel-based execution limiting.
        config.consume_fuel = True

        self.engine = Engine(config)
        self.fuel = fuel
        self.memory_limit = memory_limit

    def _create_store(self) -> Store:
        """Create a store with execution and memory limits."""

        store = Store(self.engine)

        store.set_limits(
            memory_size=self.memory_limit,
            memories=1,
        )

        store.set_fuel(self.fuel)

        return store

    def _load_module(self, wasm_bytes: bytes) -> Module:
        """Load and validate WASM with a stable sandbox error."""
        try:
            return Module(self.engine, wasm_bytes)
        except Exception as error:
            raise SandboxRuntimeError(
                "SANDBOX_ERROR",
                "WASM module validation failed",
            ) from error

    def _instantiate_module(
        self,
        store: Store,
        module: Module,
        linker: Linker | None = None,
    ) -> Instance:
        """Instantiate WASM and classify instantiation failures."""
        try:
            if linker is None:
                return Instance(store, module, [])

            return linker.instantiate(store, module)

        except Exception as error:
            message = str(error)
            lowered = message.lower()

            if "memory" in lowered or "resource limit" in lowered:
                raise SandboxRuntimeError(
                    "MEMORY_LIMIT",
                    "WASM memory limit exceeded",
                ) from error

            raise SandboxRuntimeError(
                "SANDBOX_ERROR",
                "WASM module instantiation failed",
            ) from error

    def execute(self, wasm_bytes: bytes) -> Instance:
        """Load and instantiate WASM without host imports."""

        module = self._load_module(wasm_bytes)

        store = self._create_store()

        return self._instantiate_module(store, module)

    def execute_wasi(
        self,
        wasm_bytes: bytes,
    ) -> tuple[Store, Instance]:
        """Execute WASI with no preopened host directories."""

        module = self._load_module(wasm_bytes)

        store = self._create_store()

        wasi = WasiConfig()
        store.set_wasi(wasi)

        linker = Linker(self.engine)
        linker.define_wasi()

        instance = self._instantiate_module(
            store,
            module,
            linker,
        )

        return store, instance

    def execute_with_host_functions(
        self,
        wasm_bytes: bytes,
        policy: SecurityPolicy | None = None,
    ) -> tuple[Store, Instance]:
        """Execute WASM with only explicitly authorized host functions.

        The runtime exposes a deliberately small host interface.
        No arbitrary Python or operating-system APIs are exposed.
        """

        if policy is None:
            policy = default_policy()

        module = self._load_module(wasm_bytes)

        store = self._create_store()

        linker = Linker(self.engine)

        # ---------------------------------------------------------
        # WASM host.log signature:
        #
        # host_log(pointer: i32, length: i32) -> i32
        # ---------------------------------------------------------
        host_log_type = FuncType(
            [
                ValType.i32(),
                ValType.i32(),
            ],
            [
                ValType.i32(),
            ],
        )

        linker.define_func(
            "wasmbox",
            "host_log",
            host_log_type,
            lambda caller, pointer, length: host_log_wasm(
                policy,
                caller,
                pointer,
                length,
            ),
            access_caller=True,
        )

        instance = self._instantiate_module(
            store,
            module,
            linker,
        )

        return store, instance

    def invoke(
        self,
        store: Store,
        instance: Instance,
        export_name: str,
        *args: int,
    ) -> int | None:
        """Invoke a WASM function and classify runtime failures."""

        from wasmtime import Trap

        from wasmbox.sandbox.errors import SandboxRuntimeError

        try:
            exports = instance.exports(store)
            function = exports[export_name]
            result = function(store, *args)
            return result

        except KeyError as error:
            raise SandboxRuntimeError(
                "SANDBOX_ERROR",
                f"WASM export not found: {export_name}",
            ) from error

        except Trap as error:
            message = str(error)
            lowered = message.lower()

            if "fuel" in lowered:
                code = "INSTRUCTION_LIMIT"
            elif "capability_denied" in lowered:
                code = "PERMISSION_DENIED"
            elif (
                "memory limit" in lowered
                or "resource limit" in lowered
                or "growth operation limited" in lowered
            ):
                code = "MEMORY_LIMIT"
            else:
                code = "SANDBOX_ERROR"

            raise SandboxRuntimeError(code, message) from error
