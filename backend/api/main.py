"""HTTP endpoints defined by docs/api/API_CONTRACTS.md."""

from __future__ import annotations

from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.compiler.micropython_compiler import MicroPythonCompiler
from backend.core.errors import WasmboxError
from backend.services.orchestrator import Orchestrator


class CompileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plugin_name: str = Field(min_length=1, max_length=100)
    source_code: str = Field(min_length=1, max_length=65_536)
    python_version: str = Field(min_length=1, max_length=32)


class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plugin_id: str = Field(min_length=1, max_length=100)
    input: dict[str, Any] = Field(default_factory=dict)
    limits: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)


def tenant_context(x_tenant_id: str | None = Header(default=None)) -> str:
    """Attach mandatory tenant context without changing request body contracts."""
    if not x_tenant_id or not x_tenant_id.strip() or len(x_tenant_id) > 100:
        raise WasmboxError("INVALID_REQUEST", "X-Tenant-ID header is required and must be at most 100 characters.")
    return x_tenant_id.strip()


def create_app(orchestrator: Orchestrator | None = None) -> FastAPI:
    app = FastAPI(title="WASMBOX API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Tenant-ID"],
    )
    app.state.orchestrator = orchestrator or Orchestrator(MicroPythonCompiler())

    @app.exception_handler(WasmboxError)
    async def wasmbox_error_handler(_, exc: WasmboxError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.as_dict()})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_, __: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_REQUEST", "message": "Request validation failed."}})

    @app.post("/api/v1/plugins/compile")
    async def compile_plugin(request: CompileRequest, x_tenant_id: str | None = Header(default=None)):
        tenant_id = tenant_context(x_tenant_id)
        plugin, error = app.state.orchestrator.compile_plugin(
            tenant_id=tenant_id, plugin_name=request.plugin_name,
            source_code=request.source_code, python_version=request.python_version,
        )
        if error:
            return JSONResponse(status_code=400, content={"status": "COMPILATION_FAILED", "error": error})
        # Stable contract field: this is an mpy artifact reference, not a plugin WASM claim.
        return {"status": "COMPILED", "plugin_id": plugin.plugin_id, "wasm_artifact": f"artifact:{plugin.plugin_id}"}

    @app.post("/api/v1/plugins/execute")
    async def execute_plugin(
        request: ExecuteRequest, background_tasks: BackgroundTasks,
        x_tenant_id: str | None = Header(default=None),
    ):
        tenant_id = tenant_context(x_tenant_id)
        execution = app.state.orchestrator.submit_execution(
            tenant_id=tenant_id, plugin_id=request.plugin_id, input_data=request.input,
            limits=request.limits, requested_capabilities=request.capabilities,
        )
        background_tasks.add_task(app.state.orchestrator.run_execution, execution.execution_id, tenant_id)
        return {"execution_id": execution.execution_id, "status": "RUNNING"}

    @app.get("/api/v1/executions/{execution_id}")
    async def get_execution(execution_id: str, x_tenant_id: str | None = Header(default=None)):
        tenant_id = tenant_context(x_tenant_id)
        return app.state.orchestrator.repository.get_execution(execution_id, tenant_id).as_api_response()

    @app.get("/metrics")
    async def get_metrics(x_tenant_id: str | None = Header(default=None)):
        """Expose real, in-memory record counts for the request tenant only."""
        tenant_id = tenant_context(x_tenant_id)
        return app.state.orchestrator.repository.metrics_for_tenant(tenant_id)

    return app


app = create_app()
