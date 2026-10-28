import { useState } from 'react';

export const exampleWebhook = '{\n  "event": "order.created",\n  "data": { "order_id": "ORD-1042", "amount": 1250 }\n}';

export function WebhookPanel({ busy, onTrigger }: { busy: boolean; onTrigger: (payload: string) => void }) {
  const [payload, setPayload] = useState(exampleWebhook);
  return <section className="panel webhook-panel" aria-labelledby="webhook-title">
    <div className="panel-heading"><h2 id="webhook-title">Webhook simulator</h2><span className="tag">SIMULATED</span></div>
    <div className="panel-body">
      <p className="help">Send an event as the current plugin’s execution input. This uses the normal compile and execute APIs; no public webhook is registered.</p>
      <label htmlFor="webhook-payload">Event payload <span className="muted">JSON object</span></label>
      <textarea id="webhook-payload" className="json-input webhook-input" spellCheck={false} disabled={busy} value={payload} onChange={event => setPayload(event.target.value)} />
      <button className="secondary-button full-width" disabled={busy} onClick={() => onTrigger(payload)}>↗ Send simulated webhook</button>
    </div>
  </section>;
}
