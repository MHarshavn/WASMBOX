"""Deny-by-default security policy for WASMBOX."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Capability(str, Enum):
    """Capabilities that may be granted to a plugin."""

    HOST_LOG = "host.log"
    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    NETWORK_CONNECT = "network.connect"


@dataclass(frozen=True)
class SecurityPolicy:
    """Immutable capability policy for one plugin execution.

    Capabilities are denied unless explicitly included in the granted set.
    """

    granted: frozenset[Capability] = frozenset()

    def allows(self, capability: Capability) -> bool:
        """Return True only when the capability was explicitly granted."""
        return capability in self.granted

    def require(self, capability: Capability) -> None:
        """Raise PermissionError when a capability is not authorized."""
        if not self.allows(capability):
            raise PermissionError(
                f"Capability denied: {capability.value}"
            )


def default_policy() -> SecurityPolicy:
    """Return the WASMBOX default deny-by-default policy."""
    return SecurityPolicy()

def policy_with(*capabilities: Capability) -> SecurityPolicy:
    """Create a policy containing only explicitly granted capabilities."""
    return SecurityPolicy(granted=frozenset(capabilities))