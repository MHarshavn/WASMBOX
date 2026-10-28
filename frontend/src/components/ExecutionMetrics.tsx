import type { ExecutionResult, ExecutionStatus } from '../api/types';

function metric(value: number | null | undefined, unit: string) {
  return value == null ? '—' : `${value.toLocaleString(undefined, { maximumFractionDigits: 4 })} ${unit}`;
}

export function StatusBadge({ status }: { status: ExecutionStatus | null }) {
  const tone = !status ? 'idle' : status === 'SUCCESS' ? 'success' :
    ['CREATED', 'COMPILING', 'READY', 'RUNNING'].includes(status) ? 'pending' : 'failure';
  return <span className={`status-badge ${tone}`} role="status"><span className="status-dot" />{status ?? 'NOT RUN'}</span>;
}

export function ExecutionMetrics({ result, status }: { result: ExecutionResult | null; status: ExecutionStatus | null }) {
  return <section className="metrics" aria-label="Execution metrics">
    <div className="metric"><span>Execution status</span><StatusBadge status={status} /></div>
    <div className="metric"><span>Execution time</span><strong>{metric(result?.execution_time_ms, 'ms')}</strong></div>
    <div className="metric"><span>Memory used</span><strong>{metric(result?.memory_used_mb, 'MB')}</strong></div>
    <p className="help metrics-note">Metrics come from the backend. A dash means no measurement was returned.</p>
  </section>;
}
