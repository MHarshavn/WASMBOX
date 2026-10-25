"""Security tests for the WASMBOX sandbox runtime."""

import pytest
from wasmtime import wat2wasm

from wasmbox.sandbox.runtime import WasmRuntime

from wasmbox.sandbox.errors import SandboxRuntimeError


def test_wasmtime_can_execute_wasm():
    """The runtime can load and instantiate a basic WASM module."""

    wasm = b"\x00asm\x01\x00\x00\x00"

    runtime = WasmRuntime()
    instance = runtime.execute(wasm)

    assert instance is not None


@pytest.mark.parametrize(
    "entrypoint",
    [
        "execute",
        "execute_wasi",
        "execute_with_host_functions",
    ],
)
def test_runtime_classifies_unprovided_host_import(entrypoint):
    """Unprovided imports produce a structured instantiation error."""
    wasm = """
    (module
        (import "host" "dangerous_operation" (func))
    )
    """

    runtime = WasmRuntime()
    wasm_bytes = wat2wasm(wasm)

    with pytest.raises(SandboxRuntimeError) as exc_info:
        if entrypoint == "execute":
            runtime.execute(wasm_bytes)
        elif entrypoint == "execute_wasi":
            runtime.execute_wasi(wasm_bytes)
        else:
            runtime.execute_with_host_functions(wasm_bytes)

    error = exc_info.value

    assert error.code == "SANDBOX_ERROR"
    assert error.message == "WASM module instantiation failed"
    assert error.__cause__ is not None

def test_wasi_has_no_host_filesystem_access():
    """WASI must not have host filesystem access by default."""

    wasm = """
    (module
        (import "wasi_snapshot_preview1" "fd_prestat_get"
            (func $fd_prestat_get
                (param i32 i32)
                (result i32)
            )
        )

        (memory 1)
        (export "memory" (memory 0))

        (func (export "check_filesystem") (result i32)
            i32.const 3
            i32.const 0
            call $fd_prestat_get
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_wasi(
        wat2wasm(wasm)
    )

    check_filesystem = instance.exports(store)["check_filesystem"]

    result = check_filesystem(store)

    assert result != 0


def test_wasi_cannot_read_host_passwd():
    """A WASI plugin must not read /etc/passwd from the host."""

    wasm = """
    (module
        (import "wasi_snapshot_preview1" "path_open"
            (func $path_open
                (param i32 i32 i32 i32 i32 i64 i64 i32 i32)
                (result i32)
            )
        )

        (memory 1)
        (export "memory" (memory 0))

        (data (i32.const 0) "/etc/passwd")

        (func (export "attempt_read_passwd") (result i32)
            i32.const 3
            i32.const 0
            i32.const 0
            i32.const 11
            i32.const 0
            i64.const 0
            i64.const 0
            i32.const 0
            i32.const 100
            call $path_open
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_wasi(
        wat2wasm(wasm)
    )

    attempt_read_passwd = instance.exports(store)["attempt_read_passwd"]

    result = attempt_read_passwd(store)

    assert result != 0


def test_wasi_network_access_is_denied():
    """A WASI plugin must not use a network socket by default."""

    wasm = """
    (module
        (import "wasi_snapshot_preview1" "sock_send"
            (func $sock_send
                (param i32 i32 i32 i32 i32)
                (result i32)
            )
        )

        (memory 1)
        (export "memory" (memory 0))

        (func (export "attempt_network") (result i32)
            i32.const 3
            i32.const 0
            i32.const 0
            i32.const 0
            i32.const 100
            call $sock_send
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_wasi(
        wat2wasm(wasm)
    )

    attempt_network = instance.exports(store)["attempt_network"]

    result = attempt_network(store)

    assert result != 0


def test_runtime_stops_infinite_loop():
    """An infinite WASM loop must be stopped by the fuel limit."""

    wasm = """
    (module
        (func (export "infinite_loop")
            (loop
                br 0
            )
        )
    )
    """

    runtime = WasmRuntime(fuel=10_000)

    store, instance = runtime.execute_wasi(
        wat2wasm(wasm)
    )

    with pytest.raises(SandboxRuntimeError) as exc_info:
        runtime.invoke(store, instance, "infinite_loop")

    assert exc_info.value.code == "INSTRUCTION_LIMIT"


def test_runtime_limits_excessive_instruction_execution():
    """Runtime must classify fuel exhaustion as INSTRUCTION_LIMIT."""

    wasm = """
    (module
        (func (export "run")
            (loop
                br 0
            )
        )
    )
    """

    runtime = WasmRuntime(fuel=1_000)

    store, instance = runtime.execute_wasi(
        wat2wasm(wasm)
    )

    with pytest.raises(SandboxRuntimeError) as exc_info:
        runtime.invoke(store, instance, "run")

    assert exc_info.value.code == "INSTRUCTION_LIMIT"


def test_runtime_rejects_excessive_memory():
    """A WASM module exceeding the memory limit must be rejected."""

    wasm = """
    (module
        ;; 257 pages x 64 KiB = 16,842,752 bytes.
        ;; Runtime limit is 16 MiB = 16,777,216 bytes.
        (memory 257)
    )
    """

    runtime = WasmRuntime(
        memory_limit=16 * 1024 * 1024
    )

    with pytest.raises(SandboxRuntimeError) as exc_info:
        runtime.execute_wasi(
            wat2wasm(wasm)
        )

    error = exc_info.value

    assert error.code == "MEMORY_LIMIT"
    assert error.message == "WASM memory limit exceeded"
    assert error.__cause__ is not None

@pytest.mark.parametrize(
    "entrypoint",
    [
        "execute",
        "execute_wasi",
        "execute_with_host_functions",
    ],
)
def test_runtime_classifies_malformed_wasm(entrypoint):
    """Malformed WASM produces a structured sandbox error."""
    runtime = WasmRuntime()
    malformed_wasm = b"this-is-not-valid-wasm"

    with pytest.raises(SandboxRuntimeError) as exc_info:
        if entrypoint == "execute":
            runtime.execute(malformed_wasm)
        elif entrypoint == "execute_wasi":
            runtime.execute_wasi(malformed_wasm)
        else:
            runtime.execute_with_host_functions(malformed_wasm)

    error = exc_info.value

    assert error.code == "SANDBOX_ERROR"
    assert error.message == "WASM module validation failed"
    assert error.__cause__ is not None



def test_invoke_returns_structured_instruction_limit_error():
    """Fuel exhaustion is reported as INSTRUCTION_LIMIT."""

    wasm = """
    (module
        (func (export "run")
            (loop
                br 0
            )
        )
    )
    """

    runtime = WasmRuntime(fuel=1_000)
    store, instance = runtime.execute_wasi(wat2wasm(wasm))

    with pytest.raises(SandboxRuntimeError) as exc_info:
        runtime.invoke(store, instance, "run")

    assert exc_info.value.code == "INSTRUCTION_LIMIT"


def test_invoke_reports_missing_export_structurally():
    """A missing export produces a standardized sandbox error."""
    wasm = '(module (func (export "run")))'

    runtime = WasmRuntime()
    store, instance = runtime.execute_wasi(wat2wasm(wasm))

    with pytest.raises(SandboxRuntimeError) as exc_info:
        runtime.invoke(store, instance, "missing_export")

    error = exc_info.value

    assert error.code == "SANDBOX_ERROR"
    assert "missing_export" in error.message
    assert error.__cause__ is not None

def test_runtime_reports_structured_host_capability_denial():
    """Calling a host function without permission is denied structurally."""

    wasm = """
    (module
        (import "wasmbox" "host_log"
            (func $host_log
                (param i32 i32)
                (result i32)
            )
        )

        (memory (export "memory") 1)

        (data (i32.const 0) "denied")

        (func (export "run") (result i32)
            i32.const 0
            i32.const 6
            call $host_log
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_with_host_functions(
        wat2wasm(wasm)
    )

    with pytest.raises(SandboxRuntimeError) as exc_info:
        runtime.invoke(store, instance, "run")

    error = exc_info.value

    assert error.code == "PERMISSION_DENIED"
    assert error.message


@pytest.mark.parametrize(
    ("kwargs", "expected_message"),
    [
        ({"fuel": 0}, "fuel must be greater than zero"),
        ({"fuel": -1}, "fuel must be greater than zero"),
        (
            {"memory_limit": 0},
            "memory_limit must be greater than zero",
        ),
        (
            {"memory_limit": -1},
            "memory_limit must be greater than zero",
        ),
    ],
)
def test_runtime_rejects_non_positive_resource_limits(
    kwargs,
    expected_message,
):
    """Runtime rejects invalid fuel and memory limits at initialization."""

    with pytest.raises(ValueError, match=expected_message):
        WasmRuntime(**kwargs)
