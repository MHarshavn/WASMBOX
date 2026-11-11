import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, PortalApi } from '../api/client';
import { pollExecution } from '../api/poll';
import {
  executionStates,
  type ExecutionResult,
  type ExecutionStatus,
  type RunDraft,
} from '../api/types';
import { validateDraft } from '../utils/validation';

const api = new PortalApi();
export function useExecution(client = api) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<ExecutionStatus | null>(null);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const active = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      active.current?.abort();
      active.current = null;
    },
    [],
  );

  const run = useCallback(
    async (draft: RunDraft, trigger: 'manual' | 'webhook' = 'manual') => {
      // Lock synchronously: rapid clicks cannot create overlapping executions.
      if (active.current) return;
      let validated: ReturnType<typeof validateDraft>;
      setError('');
      setNotice('');
      setResult(null);
      setStatus(null);
      try {
        validated = validateDraft(draft);
      } catch (problem) {
        setError((problem as Error).message);
        return;
      }
      const controller = new AbortController();
      active.current = controller;
      setBusy(true);
      setStatus('COMPILING');
      try {
        const compiled = await client.compile(
          { plugin_name: draft.name.trim(), source_code: draft.source, python_version: '3.x' },
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setStatus('READY');
        const initial = await client.execute(
          {
            plugin_id: compiled.plugin_id,
            input: validated.input,
            limits: validated.limits,
            capabilities: draft.hostLog ? ['host.log'] : [],
          },
          controller.signal,
        );
        if (controller.signal.aborted) return;
        await pollExecution(
          (id, signal) => client.result(id, signal),
          initial,
          controller.signal,
          (update) => {
            if (!controller.signal.aborted) {
              setStatus(update.status);
              setResult(update);
            }
          },
        );
        if (!controller.signal.aborted && trigger === 'webhook')
          setNotice('Simulated webhook execution finished.');
      } catch (problem) {
        if (controller.signal.aborted) return;
        const fault =
          problem instanceof Error ? problem : new Error('An unexpected execution error occurred.');
        setError(fault.message);
        if (fault instanceof ApiError) {
          const failure = fault.code === 'COMPILATION_ERROR' ? 'COMPILATION_FAILED' : fault.code;
          if (executionStates.includes(failure as ExecutionStatus))
            setStatus(failure as ExecutionStatus);
        }
      } finally {
        if (active.current === controller) {
          active.current = null;
          setBusy(false);
        }
      }
    },
    [client],
  );

  const stop = useCallback(() => {
    active.current?.abort();
    active.current = null;
    setBusy(false);
    setNotice(
      'Stopped waiting locally. The backend may still be executing; this does not terminate the sandbox.',
    );
  }, []);
  const reset = useCallback(() => {
    if (!active.current) {
      setResult(null);
      setStatus(null);
      setError('');
      setNotice('');
    }
  }, []);
  return { busy, status, result, error, notice, run, stop, reset };
}
