import {
  executionStates,
  type CompiledPlugin,
  type CompileRequest,
  type ExecuteRequest,
  type ExecutionResult,
} from './types';

export class ApiError extends Error {
  constructor(
    message: string,
    public code = 'CONNECTION_ERROR',
    public httpStatus?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function nonempty(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0;
}

export function readExecution(value: unknown): ExecutionResult {
  if (
    !record(value) ||
    !nonempty(value.execution_id) ||
    !executionStates.includes(value.status as (typeof executionStates)[number])
  ) {
    throw new ApiError('Backend returned an invalid execution response.', 'INVALID_RESPONSE');
  }
  for (const key of ['stdout', 'stderr', 'termination_reason']) {
    if (value[key] !== undefined && value[key] !== null && typeof value[key] !== 'string') {
      throw new ApiError(`Backend returned invalid ${key}.`, 'INVALID_RESPONSE');
    }
  }
  for (const key of ['execution_time_ms', 'memory_used_mb']) {
    if (
      value[key] !== undefined &&
      value[key] !== null &&
      (typeof value[key] !== 'number' || !Number.isFinite(value[key]) || (value[key] as number) < 0)
    ) {
      throw new ApiError(`Backend returned invalid ${key}.`, 'INVALID_RESPONSE');
    }
  }
  return value as unknown as ExecutionResult;
}

export class PortalApi {
  private base: string;
  constructor(
    base = import.meta.env.VITE_API_BASE_URL || '',
    private requestTimeout = 15_000,
  ) {
    this.base = base.replace(/\/+$/, '');
  }

  private async request(
    path: string,
    method: 'GET' | 'POST',
    body: unknown,
    signal: AbortSignal,
  ): Promise<unknown> {
    const controller = new AbortController();
    const abort = () => controller.abort();
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) controller.abort();
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, this.requestTimeout);
    try {
      const response = await fetch(`${this.base}${path}`, {
        method,
        credentials: 'same-origin',
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'X-Tenant-ID': import.meta.env.VITE_TENANT_ID || 'demo-tenant',
          ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      let data: unknown;
      try {
        data = await response.json();
      } catch (error) {
        if (controller.signal.aborted) throw error;
        throw new ApiError(
          `Backend returned a non-JSON response (HTTP ${response.status}). Check the API address and proxy.`,
          'INVALID_RESPONSE',
          response.status,
        );
      }
      if (record(data) && record(data.error)) {
        throw new ApiError(
          typeof data.error.message === 'string'
            ? data.error.message
            : 'Backend rejected the request.',
          typeof data.error.code === 'string' ? data.error.code : 'API_ERROR',
          response.status,
        );
      }
      if (!response.ok) {
        const message =
          response.status === 401
            ? 'Sign in to your backend session before running plugins.'
            : response.status === 403
              ? 'Your backend session does not have access to this plugin.'
              : `Backend request failed (HTTP ${response.status}).`;
        throw new ApiError(message, 'HTTP_ERROR', response.status);
      }
      return data;
    } catch (error) {
      if (signal.aborted) throw new DOMException('Request cancelled', 'AbortError');
      if (timedOut)
        throw new ApiError(
          'The backend request timed out. Check execution status before retrying.',
          'REQUEST_TIMEOUT',
        );
      if (error instanceof ApiError) throw error;
      throw new ApiError(
        'Cannot reach the WASMBOX backend. Check that the API is running and the proxy or CORS configuration is correct.',
      );
    } finally {
      clearTimeout(timer);
      signal.removeEventListener('abort', abort);
    }
  }

  async compile(request: CompileRequest, signal: AbortSignal): Promise<CompiledPlugin> {
    const data = await this.request('/api/v1/plugins/compile', 'POST', request, signal);
    if (
      !record(data) ||
      data.status !== 'COMPILED' ||
      !nonempty(data.plugin_id) ||
      !nonempty(data.wasm_artifact)
    ) {
      throw new ApiError('Backend returned an invalid compilation response.', 'INVALID_RESPONSE');
    }
    return data as unknown as CompiledPlugin;
  }
  async execute(request: ExecuteRequest, signal: AbortSignal): Promise<ExecutionResult> {
    return readExecution(await this.request('/api/v1/plugins/execute', 'POST', request, signal));
  }
  async result(id: string, signal: AbortSignal): Promise<ExecutionResult> {
    const data = readExecution(
      await this.request(`/api/v1/executions/${encodeURIComponent(id)}`, 'GET', undefined, signal),
    );
    if (data.execution_id !== id)
      throw new ApiError('Backend returned a different execution ID.', 'INVALID_RESPONSE');
    return data;
  }
}
