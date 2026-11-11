import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import type { ExecutionStatus } from './api/types';

vi.mock('./components/SourceEditor', () => ({
  SourceEditor: ({
    source,
    onChange,
    readOnly,
  }: {
    source: string;
    onChange: (source: string) => void;
    readOnly: boolean;
  }) => (
    <textarea
      aria-label="Python source"
      value={source}
      onChange={(event) => onChange(event.target.value)}
      readOnly={readOnly}
    />
  ),
}));
function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
function backend(status: ExecutionStatus = 'SUCCESS', extra = {}) {
  const fetcher = vi.fn((url: string) => {
    if (url.endsWith('/compile'))
      return Promise.resolve(
        json({ status: 'COMPILED', plugin_id: 'p1', wasm_artifact: 'artifact' }),
      );
    if (url.endsWith('/execute'))
      return Promise.resolve(json({ execution_id: 'e1', status: 'RUNNING' }));
    return Promise.resolve(
      json({
        execution_id: 'e1',
        status,
        stdout: 'hello backend',
        stderr: '',
        execution_time_ms: 0.25,
        memory_used_mb: 8,
        ...extra,
      }),
    );
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}

describe('developer portal', () => {
  it('runs source through compile, execute and polling with denied-by-default capabilities', async () => {
    const fetcher = backend();
    const user = userEvent.setup();
    render(<App />);
    fireEvent.change(screen.getByLabelText('Python source'), {
      target: { value: 'print("hello backend")' },
    });
    await user.click(screen.getByRole('button', { name: /Run plugin/ }));
    await screen.findByText('hello backend');
    expect(screen.getByText('SUCCESS')).toBeInTheDocument();
    expect(screen.getByText('0.25 ms')).toBeInTheDocument();
    expect(screen.getByText('8 MB')).toBeInTheDocument();
    const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
    expect(JSON.parse(calls[0][1].body as string)).toEqual({
      plugin_name: 'company-data-parser',
      source_code: 'print("hello backend")',
      python_version: '3.x',
    });
    expect(JSON.parse(calls[1][1].body as string)).toEqual({
      plugin_id: 'p1',
      input: {},
      limits: { memory_mb: 10, timeout_ms: 50 },
      capabilities: [],
    });
  });
  it('shows compilation errors without attempting execution', async () => {
    const fetcher = vi.fn().mockResolvedValue(
      json({
        status: 'COMPILATION_FAILED',
        error: { code: 'COMPILATION_ERROR', message: 'SyntaxError: missing colon' },
      }),
    );
    vi.stubGlobal('fetch', fetcher);
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent('SyntaxError: missing colon');
    expect(screen.getByText('COMPILATION_FAILED')).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: /Run plugin/ })).toBeEnabled();
  });
  it.each([
    'EXECUTION_FAILED',
    'TIMEOUT',
    'MEMORY_LIMIT',
    'INSTRUCTION_LIMIT',
    'PERMISSION_DENIED',
    'SANDBOX_ERROR',
  ] as ExecutionStatus[])('shows %s and stderr immediately', async (status) => {
    backend(status, { stderr: 'Backend failure details', termination_reason: status });
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    expect(await screen.findByText('Backend failure details')).toBeInTheDocument();
    expect(screen.getByText(status, { selector: '.status-badge' })).toBeInTheDocument();
    expect(screen.getByText(`Termination reason: ${status}`)).toBeInTheDocument();
  });
  it('does not render returned markup as HTML', async () => {
    backend('SUCCESS', { stdout: '<img src=x onerror=alert(1)>' });
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    const output = await screen.findByText('<img src=x onerror=alert(1)>');
    expect(output.querySelector('img')).toBeNull();
  });
  it('shows missing metrics as unavailable and keeps zero measurements', async () => {
    backend('SUCCESS', { execution_time_ms: 0, memory_used_mb: null });
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    expect(await screen.findByText('0 ms')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
  });
  it('validates JSON before making any backend call', async () => {
    const fetcher = backend();
    render(<App />);
    fireEvent.change(screen.getByLabelText(/Plugin input/), { target: { value: '[]' } });
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    expect(screen.getByRole('alert')).toHaveTextContent('JSON object');
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('handles an unavailable backend and allows retry', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Offline')));
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach');
    backend();
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    expect(await screen.findByText('hello backend')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).toBeNull();
  });
  it('saves and loads exact source across remounts without calling the API', async () => {
    const fetcher = backend();
    const user = userEvent.setup();
    const first = render(<App />);
    fireEvent.change(screen.getByLabelText('Python source'), {
      target: { value: 'print("saved")' },
    });
    await user.click(screen.getByRole('button', { name: 'Save plugin' }));
    first.unmount();
    render(<App />);
    await user.click(screen.getByRole('button', { name: 'Load company-data-parser' }));
    expect(screen.getByLabelText('Python source')).toHaveValue('print("saved")');
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('protects unsaved changes when loading or starting a new plugin', async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText('Python source'), {
      target: { value: 'unsaved source' },
    });
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    await userEvent.click(screen.getByRole('button', { name: 'New plugin' }));
    expect(screen.getByLabelText('Python source')).toHaveValue('unsaved source');
  });
  it('deletes a saved copy after explicit confirmation while retaining source', async () => {
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: 'Save plugin' }));
    await userEvent.click(screen.getByRole('button', { name: 'Delete company-data-parser' }));
    expect(screen.getByText('Delete this local copy?')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /^Delete$/ }));
    expect(screen.queryByRole('button', { name: 'Delete company-data-parser' })).toBeNull();
    expect((screen.getByLabelText('Python source') as HTMLTextAreaElement).value).toContain(
      'import json',
    );
  });
  it('reports failed browser saves', async () => {
    render(<App />);
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('Quota');
    });
    await userEvent.click(screen.getByRole('button', { name: 'Save plugin' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Could not save');
  });
  it('sends simulated webhook payload with explicitly selected capabilities', async () => {
    const fetcher = backend();
    render(<App />);
    fireEvent.change(screen.getByLabelText(/Event payload/), {
      target: { value: '{"event":"invoice.paid"}' },
    });
    await userEvent.click(screen.getByLabelText('Allow host.log capability'));
    await userEvent.click(screen.getByRole('button', { name: /Send simulated webhook/ }));
    await screen.findByText('Simulated webhook execution finished.');
    const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
    expect(JSON.parse(calls[1][1].body as string)).toMatchObject({
      input: { event: 'invoice.paid' },
      capabilities: ['host.log'],
    });
    expect(screen.getByLabelText(/Plugin input/)).toHaveValue('{}');
  });
  it('rejects invalid simulated events without sending code', async () => {
    const fetcher = backend();
    render(<App />);
    fireEvent.change(screen.getByLabelText(/Event payload/), { target: { value: 'invalid' } });
    await userEvent.click(screen.getByRole('button', { name: /Send simulated webhook/ }));
    expect(screen.getByRole('alert')).toHaveTextContent('valid JSON');
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('prevents overlapping runs and cancels local waiting', async () => {
    const fetcher = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) =>
          init.signal?.addEventListener('abort', () =>
            reject(new DOMException('Abort', 'AbortError')),
          ),
        ),
    );
    vi.stubGlobal('fetch', fetcher);
    const view = render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Run plugin/ }));
    expect(screen.getByRole('button', { name: 'Save plugin' })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Send simulated webhook/ })).toBeDisabled();
    await userEvent.click(screen.getByRole('button', { name: 'Stop waiting' }));
    expect(screen.getByText(/does not terminate the sandbox/)).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.getByRole('button', { name: /Run plugin/ })).toBeEnabled());
    view.unmount();
  });
});
