"""Tests for the WASMBOX deny-by-default security policy."""

import pytest

from wasmbox.sandbox.policy import (
    Capability,
    default_policy,
    policy_with,
)


def test_default_policy_denies_all_capabilities():
    policy = default_policy()

    for capability in Capability:
        assert policy.allows(capability) is False


def test_authorized_capability_is_allowed():
    policy = policy_with(Capability.HOST_LOG)

    assert policy.allows(Capability.HOST_LOG) is True


def test_ungranted_capability_is_denied():
    policy = policy_with(Capability.HOST_LOG)

    assert policy.allows(Capability.FILESYSTEM_READ) is False
    assert policy.allows(Capability.NETWORK_CONNECT) is False


def test_require_raises_for_unauthorized_capability():
    policy = default_policy()

    with pytest.raises(PermissionError):
        policy.require(Capability.FILESYSTEM_READ)


def test_require_succeeds_for_authorized_capability():
    policy = policy_with(Capability.HOST_LOG)

    policy.require(Capability.HOST_LOG)