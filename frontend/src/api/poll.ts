import { ApiError } from './client';
import { isTerminal, type ExecutionResult } from './types';

function pause(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException('Polling cancelled', 'AbortError'));
    };
    const timer = setTimeout(() => {
      signal.removeEventListener('abort', abort);
      resolve();
    }, ms);
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
  });
}

/** A browser deadline stops waiting; only the backend can terminate the sandbox. */
export async function pollExecution(
  read: (id: string, signal: AbortSignal) => Promise<ExecutionResult>,
  initial: ExecutionResult,
  signal: AbortSignal,
  onUpdate: (result: ExecutionResult) => void,
  { interval = 300, maxWait = 60_000 } = {},
): Promise<ExecutionResult> {
  if (signal.aborted) throw new DOMException('Polling cancelled', 'AbortError');
  if (isTerminal(initial.status)) {
    onUpdate(initial);
    return initial;
  }
  const controller = new AbortController();
  const abort = () => controller.abort();
  signal.addEventListener('abort', abort, { once: true });
  let expired = false;
  const timer = setTimeout(() => {
    expired = true;
    controller.abort();
  }, maxWait);
  try {
    let result = initial;
    onUpdate(result);
    while (!isTerminal(result.status)) {
      await pause(interval, controller.signal);
      result = await read(initial.execution_id, controller.signal);
      if (result.execution_id !== initial.execution_id)
        throw new ApiError('Execution ID changed while polling.', 'INVALID_RESPONSE');
      onUpdate(result);
    }
    return result;
  } catch (error) {
    if (expired && !signal.aborted)
      throw new ApiError(
        'Stopped waiting after 60 seconds. The backend execution may still be active; check its ID before retrying.',
        'POLL_TIMEOUT',
      );
    throw error;
  } finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', abort);
  }
}
