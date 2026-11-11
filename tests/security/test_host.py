"""Security tests for WASMBOX host functions."""

import pytest
from wasmtime import Trap, wat2wasm

from wasmbox.sandbox.errors import CapabilityDeniedError
from wasmbox.sandbox.host import host_log
from wasmbox.sandbox.policy import (
    Capability,
    default_policy,
    policy_with,
)
from wasmbox.sandbox.runtime import WasmRuntime


def test_host_log_succeeds_with_capability(capsys):
    """host.log must succeed when explicitly authorized."""

    policy = policy_with(Capability.HOST_LOG)

    result = host_log(
        policy,
        "hello",
    )

    captured = capsys.readouterr()

    assert result == "ok"
    assert "[WASMBOX] hello" in captured.out


def test_host_log_rejects_without_capability():
    """host.log must be rejected when not authorized."""

    policy = default_policy()

    with pytest.raises(CapabilityDeniedError) as exc_info:
        host_log(
            policy,
            "blocked",
        )

    error = exc_info.value

    assert error.code == "capability_denied"
    assert error.capability == Capability.HOST_LOG.value


def test_wasm_host_log_succeeds_with_capability(capsys):
    """A WASM plugin can call host.log when authorized."""

    wasm = """
    (module
        (import "wasmbox" "host_log"
            (func $host_log
                (param i32 i32)
                (result i32)
            )
        )

        (memory 1)
        (export "memory" (memory 0))

        (data (i32.const 0) "hello")

        (func (export "run") (result i32)
            i32.const 0
            i32.const 5
            call $host_log
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_with_host_functions(
        wat2wasm(wasm),
        policy_with(Capability.HOST_LOG),
    )

    run = instance.exports(store)["run"]

    result = run(store)

    captured = capsys.readouterr()

    assert result == 0
    assert "[WASMBOX] hello" in captured.out


def test_wasm_host_log_rejects_without_capability():
    """A WASM plugin cannot call host.log without authorization."""

    wasm = """
    (module
        (import "wasmbox" "host_log"
            (func $host_log
                (param i32 i32)
                (result i32)
            )
        )

        (memory 1)
        (export "memory" (memory 0))

        (data (i32.const 0) "blocked")

        (func (export "run") (result i32)
            i32.const 0
            i32.const 7
            call $host_log
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_with_host_functions(
        wat2wasm(wasm),
        default_policy(),
    )

    run = instance.exports(store)["run"]

    # A Python CapabilityDeniedError is converted into a Wasmtime Trap
    # at the WASM/host boundary.
    with pytest.raises(Trap) as exc_info:
        run(store)

    error = exc_info.value

    assert "capability_denied" in str(error)
    assert "host.log" in str(error)


def test_wasm_host_log_rejects_out_of_bounds_memory():
    """host.log must reject memory ranges outside guest memory."""

    wasm = """
    (module
        (import "wasmbox" "host_log"
            (func $host_log
                (param i32 i32)
                (result i32)
            )
        )

        (memory 1)
        (export "memory" (memory 0))

        (func (export "run") (result i32)
            i32.const 65530
            i32.const 20
            call $host_log
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_with_host_functions(
        wat2wasm(wasm),
        policy_with(Capability.HOST_LOG),
    )

    run = instance.exports(store)["run"]

    with pytest.raises(Trap) as exc_info:
        run(store)

    assert "invalid_memory_range" in str(exc_info.value)


def test_wasm_host_log_rejects_oversized_message():
    """host.log must enforce the maximum message size."""

    wasm = """
    (module
        (import "wasmbox" "host_log"
            (func $host_log
                (param i32 i32)
                (result i32)
            )
        )

        (memory 1)
        (export "memory" (memory 0))

        (func (export "run") (result i32)
            i32.const 0
            i32.const 4097
            call $host_log
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_with_host_functions(
        wat2wasm(wasm),
        policy_with(Capability.HOST_LOG),
    )

    run = instance.exports(store)["run"]

    with pytest.raises(Trap) as exc_info:
        run(store)

    assert "resource_limit" in str(exc_info.value)