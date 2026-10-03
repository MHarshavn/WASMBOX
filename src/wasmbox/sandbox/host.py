"""Narrowly scoped host functions for WASMBOX."""

from __future__ import annotations

from wasmbox.sandbox.policy import Capability, SecurityPolicy


def host_log(policy: SecurityPolicy, message: str) -> str:
    """Log a message only when the host.log capability is authorized."""

    policy.require(Capability.HOST_LOG)

    print(f"[WASMBOX] {message}")

    return "ok"