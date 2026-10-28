import { afterEach, describe, expect, it, vi } from 'vitest';
import { PortalApi, readExecution } from './client';
import { executionStates } from './types';

const signal = () => new AbortController().signal;
function reply(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}
afterEach(() => vi.useRealTimers());
describe('API contract client', () => {
  it('posts compile and execute bodies and encodes result IDs', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(reply({ status: 'COMPILED', plugin_id: 'p1', wasm_artifact: 'artifact' }))
      .mockResolvedValueOnce(reply({ execution_id: 'e/1', status: 'RUNNING' }))
      .mockResolvedValueOnce(reply({ execution_id: 'e/1', status: 'SUCCESS', stdout: 'ok', execution_time_ms: 0, memory_used_mb: 0 }));
    vi.stubGlobal('fetch', fetcher);
    const api = new PortalApi('https://api.example.test/');
    const compile = { plugin_name: 'parser', source_code: 'print(1)', python_version: '3.x' as const };
    await api.compile(compile, signal());
    const execute = { plugin_id: 'p1', input: { count: 1 }, limits: { memory_mb: 10, timeout_ms: 50 }, capabilities: [] };
    await api.execute(execute, signal());
    expect(await api.result('e/1', signal())).toMatchObject({ execution_time_ms: 0, memory_used_mb: 0 });
    expect(fetcher.mock.calls[0][0]).toBe('https://api.example.test/api/v1/plugins/compile');
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual(compile);
    expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual(execute);
    expect(fetcher.mock.calls[2][0]).toBe('https://api.example.test/api/v1/executions/e%2F1');
    expect(fetcher.mock.calls[0][1].credentials).toBe('same-origin');
  });
  it.each([200, 422])('surfaces structured compilation failures on HTTP %s', async status => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ status: 'COMPILATION_FAILED', error: { code: 'COMPILATION_ERROR', message: 'SyntaxError at line 2' } }, status)));
    await expect(new PortalApi().compile({ plugin_name: 'p', source_code: 'bad', python_version: '3.x' }, signal()))
      .rejects.toMatchObject({ code: 'COMPILATION_ERROR', message: 'SyntaxError at line 2' });
  });
  it.each(executionStates)('recognizes canonical state %s', status => {
    expect(readExecution({ execution_id: 'e1', status }).status).toBe(status);
  });
  it.each([
    { execution_id: 'e', status: 'DONE' }, { status: 'SUCCESS' },
    { execution_id: 'e', status: 'SUCCESS', memory_used_mb: -1 },
    { execution_id: 'e', status: 'SUCCESS', execution_time_ms: '5' },
    { execution_id: 'e', status: 'SUCCESS', stderr: {} },
  ])('rejects malformed execution data', data => { expect(() => readExecution(data)).toThrow(/invalid/i); });
  it('rejects a mismatched execution ID', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ execution_id: 'other', status: 'SUCCESS' })));
    await expect(new PortalApi().result('e1', signal())).rejects.toMatchObject({ code: 'INVALID_RESPONSE' });
  });
  it('handles proxy HTML responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>Not found</html>', { status: 404 })));
    await expect(new PortalApi().result('e1', signal())).rejects.toThrow(/non-JSON/);
  });
  it('handles a disconnected backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(new PortalApi().result('e1', signal())).rejects.toThrow(/Cannot reach/);
  });
  it.each([401, 403, 500])('handles HTTP %s', async status => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({}, status)));
    await expect(new PortalApi().result('e1', signal())).rejects.toMatchObject({ httpStatus: status });
  });
  it('bounds stalled requests and preserves caller cancellation', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('fetch', vi.fn((_url, init: RequestInit) => new Promise((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    })));
    const task = new PortalApi('', 100).result('e1', signal());
    const assertion = expect(task).rejects.toMatchObject({ code: 'REQUEST_TIMEOUT' });
    await vi.advanceTimersByTimeAsync(100); await assertion;
    const controller = new AbortController();
    const cancelled = new PortalApi().result('e1', controller.signal);
    const cancellation = expect(cancelled).rejects.toMatchObject({ name: 'AbortError' });
    controller.abort(); await cancellation;
  });
});
