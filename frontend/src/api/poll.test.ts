import { afterEach, expect, it, vi } from 'vitest';
import { pollExecution } from './poll';
import { executionStates, isTerminal, type ExecutionResult } from './types';
afterEach(() => vi.useRealTimers());
const initial: ExecutionResult = { execution_id: 'e1', status: 'RUNNING' };
it.each(executionStates.filter(isTerminal))('stops at terminal state %s', async (status) => {
  const read = vi.fn().mockResolvedValue({ ...initial, status });
  const update = vi.fn();
  const result = await pollExecution(read, initial, new AbortController().signal, update, {
    interval: 0,
  });
  expect(result.status).toBe(status);
  expect(read).toHaveBeenCalledTimes(1);
  expect(update).toHaveBeenCalledTimes(2);
});
it('does not poll an already completed result', async () => {
  const read = vi.fn();
  await pollExecution(
    read,
    { ...initial, status: 'SUCCESS' },
    new AbortController().signal,
    vi.fn(),
  );
  expect(read).not.toHaveBeenCalled();
});
it('times out even when a result request stalls', async () => {
  vi.useFakeTimers();
  const read = vi.fn(
    (_id, signal: AbortSignal) =>
      new Promise<ExecutionResult>((_resolve, reject) =>
        signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError'))),
      ),
  );
  const task = pollExecution(read, initial, new AbortController().signal, vi.fn(), {
    interval: 5,
    maxWait: 50,
  });
  const assertion = expect(task).rejects.toMatchObject({ code: 'POLL_TIMEOUT' });
  await vi.advanceTimersByTimeAsync(50);
  await assertion;
  expect(vi.getTimerCount()).toBe(0);
});
it('cancels the delay without another request', async () => {
  const controller = new AbortController();
  const read = vi.fn();
  const task = pollExecution(read, initial, controller.signal, vi.fn());
  const assertion = expect(task).rejects.toMatchObject({ name: 'AbortError' });
  controller.abort();
  await assertion;
  expect(read).not.toHaveBeenCalled();
});
