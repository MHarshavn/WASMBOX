"""Security policy tests for WASMBOX."""

import pytest

from wasmbox.sandbox.errors import CapabilityDeniedError
from wasmbox.sandbox.policy import (
    Capability,
    default_policy,
    policy_with,
)


def test_default_policy_denies_all_capabilities():
    """The default policy must deny every capability."""

    policy = default_policy()

    assert policy.allows(Capability.HOST_LOG) is False
    assert policy.allows(Capability.FILESYSTEM_READ) is False
    assert policy.allows(Capability.FILESYSTEM_WRITE) is False
    assert policy.allows(Capability.NETWORK_CONNECT) is False


def test_authorized_capability_is_allowed():
    """An explicitly granted capability must be allowed."""

    policy = policy_with(Capability.HOST_LOG)

    assert policy.allows(Capability.HOST_LOG) is True


def test_ungranted_capability_is_denied():
    """A capability not present in the policy must be denied."""

    policy = policy_with(Capability.HOST_LOG)

    assert policy.allows(Capability.NETWORK_CONNECT) is False


def test_require_raises_for_unauthorized_capability():
    """require must reject an unauthorized capability."""

    policy = default_policy()

    with pytest.raises(PermissionError):
        policy.require(Capability.FILESYSTEM_READ)


def test_require_succeeds_for_authorized_capability():
    """require must succeed for an authorized capability."""

    policy = policy_with(Capability.FILESYSTEM_READ)

    policy.require(Capability.FILESYSTEM_READ)


def test_capability_denied_error_is_structured():
    """Capability denial must expose structured security information."""

    policy = default_policy()

    with pytest.raises(CapabilityDeniedError) as exc_info:
        policy.require(Capability.NETWORK_CONNECT)

    error = exc_info.value

    assert error.code == "capability_denied"
    assert error.capability == "network.connect"
    assert error.message == "Capability denied: network.connect"