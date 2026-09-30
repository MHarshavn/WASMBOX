"""Security tests for the WASMBOX sandbox runtime."""

import pytest
from wasmtime import wat2wasm

from wasmbox.sandbox.runtime import WasmRuntime


def test_wasmtime_can_execute_wasm():
    """The runtime can load and instantiate a basic WASM module."""

    wasm = b"\x00asm\x01\x00\x00\x00"

    runtime = WasmRuntime()
    instance = runtime.execute(wasm)

    assert instance is not None


def test_runtime_rejects_unprovided_host_import():
    """An arbitrary host import must be rejected."""

    wasm = """
    (module
        (import "host" "dangerous_operation" (func))
    )
    """

    runtime = WasmRuntime()

    with pytest.raises(Exception):
        runtime.execute(wat2wasm(wasm))


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

    store, instance = runtime.execute_wasi(wat2wasm(wasm))

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

            ;; fd = 3
            i32.const 3

            ;; dirflags = 0
            i32.const 0

            ;; path pointer = 0
            i32.const 0

            ;; path length = 11
            i32.const 11

            ;; oflags = 0 (read-only)
            i32.const 0

            ;; rights_base = 0
            i64.const 0

            ;; rights_inheriting = 0
            i64.const 0

            ;; fdflags = 0
            i32.const 0

            ;; result fd pointer = 100
            i32.const 100

            call $path_open
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_wasi(wat2wasm(wasm))

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

            ;; fd = 3
            i32.const 3

            ;; pointer to iovec array
            i32.const 0

            ;; number of iovecs = 0
            i32.const 0

            ;; flags = 0
            i32.const 0

            ;; result length pointer
            i32.const 100

            call $sock_send
        )
    )
    """

    runtime = WasmRuntime()

    store, instance = runtime.execute_wasi(wat2wasm(wasm))

    attempt_network = instance.exports(store)["attempt_network"]

    result = attempt_network(store)

    # No socket is available because the sandbox does not provide
    # a network socket capability.
    assert result != 0