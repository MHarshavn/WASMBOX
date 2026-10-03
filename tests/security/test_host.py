"""Security tests for WASMBOX host functions."""

import pytest

from wasmbox.sandbox.errors import CapabilityDeniedError
from wasmbox.sandbox.host import host_log
from wasmbox.sandbox.policy import Capability, default_policy, policy_with


def test_host_log_succeeds_with_capability(capsys):
    """host.log must succeed when explicitly authorized."""

    policy = policy_with(Capability.HOST_LOG)

    result = host_log(policy, "hello")

    captured = capsys.readouterr()

    assert result == "ok"
    assert "[WASMBOX] hello" in captured.out


def test_host_log_rejects_without_capability():
    """host.log must be rejected when not authorized."""

    policy = default_policy()

    with pytest.raises(CapabilityDeniedError) as exc_info:
        host_log(policy, "blocked")

    error = exc_info.value

    assert error.code == "capability_denied"
    assert error.capability == Capability.HOST_LOG.value