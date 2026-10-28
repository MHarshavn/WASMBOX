import { useState } from 'react';
import type { ExecutionResult, ExecutionStatus } from '../api/types';

export function ExecutionOutput({ result, status, busy, error, notice }: {
  result: ExecutionResult | null; status: ExecutionStatus | null; busy: boolean; error: string; notice: string;
}) {
  const [stream, setStream] = useState<'stdout' | 'stderr'>('stdout');
  const hasError = Boolean(result?.stderr);
  return <section className="panel output-panel" aria-labelledby="output-title" aria-busy={busy}>
    <div className="panel-heading"><h2 id="output-title">Execution console</h2><span className="muted">{result ? `ID: ${result.execution_id}` : 'No execution yet'}</span></div>
    <div className="stream-switch" role="group" aria-label="Output stream">
      <button aria-pressed={stream === 'stdout'} onClick={() => setStream('stdout')}>stdout</button>
      <button aria-pressed={stream === 'stderr'} onClick={() => setStream('stderr')}>stderr {hasError && <span className="error-dot" aria-label="contains errors" />}</button>
    </div>
    {error && <div className="error-message" role="alert">{error}</div>}
    {notice && <p className="notice" role="status">{notice}</p>}
    {result?.termination_reason && <div className="error-message">Termination reason: {result.termination_reason}</div>}
    {/* Render stderr even when stdout is selected so failures are immediately visible. */}
    {hasError && stream === 'stdout' && <pre className="stderr-preview" aria-label="Error output">{result?.stderr}</pre>}
    <pre className={`console-output ${stream}`} aria-label={stream === 'stdout' ? 'Standard output' : 'Standard error'}>
      {result?.[stream] || (busy ? `Waiting for backend… ${status ?? ''}` : result ? `No ${stream} returned.` : 'Run a plugin to see its output here.')}
    </pre>
  </section>;
}
