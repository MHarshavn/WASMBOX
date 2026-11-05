"""Narrowly scoped host functions for WASMBOX."""

from __future__ import annotations

from wasmtime import Caller, Trap

from wasmbox.sandbox.errors import CapabilityDeniedError
from wasmbox.sandbox.policy import Capability, SecurityPolicy


MAX_LOG_BYTES = 4096


def host_log(policy: SecurityPolicy, message: str) -> str:
    """Log a message only when the host.log capability is authorized."""

    policy.require(Capability.HOST_LOG)

    print(f"[WASMBOX] {message}")

    return "ok"


def host_log_wasm(
    policy: SecurityPolicy,
    caller: Caller,
    pointer: int,
    length: int,
) -> int:
    """WASM-facing implementation of the host.log capability.

    The WASM module supplies a pointer and length into its exported
    linear memory. Authorization is checked before reading memory.
    """

    # ---------------------------------------------------------
    # 1. Capability check
    # ---------------------------------------------------------
    try:
        policy.require(Capability.HOST_LOG)
    except CapabilityDeniedError as error:
        # Python exceptions cannot safely cross the Wasmtime boundary.
        # Convert the structured security error into a WASM trap.
        raise Trap(
            f"{error.code}: {error.message}"
        ) from error

    # ---------------------------------------------------------
    # 2. Validate pointer
    # ---------------------------------------------------------
    if pointer < 0:
        raise Trap("invalid_memory_range: log pointer must not be negative")

    # ---------------------------------------------------------
    # 3. Validate length
    # ---------------------------------------------------------
    if length < 0:
        raise Trap("invalid_memory_range: log length must not be negative")

    if length > MAX_LOG_BYTES:
        raise Trap(
            f"resource_limit: log message exceeds "
            f"maximum size of {MAX_LOG_BYTES} bytes"
        )

    # ---------------------------------------------------------
    # 4. Get WASM memory
    # ---------------------------------------------------------
    memory = caller.get("memory")

    if memory is None:
        raise Trap(
            "invalid_host_interface: WASM module must export memory"
        )

    # ---------------------------------------------------------
    # 5. Explicit bounds check
    # ---------------------------------------------------------
    memory_size = memory.data_len(caller)

    if pointer + length > memory_size:
        raise Trap(
            "invalid_memory_range: "
            f"requested range [{pointer}, {pointer + length}) "
            f"exceeds memory size {memory_size}"
        )

    # ---------------------------------------------------------
    # 6. Read guest memory
    # ---------------------------------------------------------
    try:
        raw_message = bytes(
            memory.read(
                caller,
                pointer,
                pointer + length,
            )
        )
    except Exception as error:
        raise Trap(
            f"memory_read_failed: {error}"
        ) from error

    # ---------------------------------------------------------
    # 7. Decode UTF-8
    # ---------------------------------------------------------
    try:
        message = raw_message.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Trap(
            "invalid_utf8: host.log message must contain valid UTF-8"
        ) from error

    # ---------------------------------------------------------
    # 8. Perform the authorized operation
    # ---------------------------------------------------------
    print(f"[WASMBOX] {message}")

    return 0