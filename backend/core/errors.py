"""Structured domain errors used at the API boundary."""


class WasmboxError(Exception):
    """An error that is safe to return to an API caller."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class PluginNotFound(WasmboxError):
    def __init__(self, plugin_id: str) -> None:
        super().__init__("PLUGIN_NOT_FOUND", f"Plugin '{plugin_id}' was not found.", 404)


class ExecutionNotFound(WasmboxError):
    def __init__(self, execution_id: str) -> None:
        super().__init__("PLUGIN_NOT_FOUND", f"Execution '{execution_id}' was not found.", 404)


class TenantAccessDenied(WasmboxError):
    def __init__(self) -> None:
        super().__init__("TENANT_ACCESS_DENIED", "Tenant cannot access this resource.", 403)


class PermissionDenied(WasmboxError):
    def __init__(self, message: str = "Capability not granted.") -> None:
        super().__init__("PERMISSION_DENIED", message, 403)
