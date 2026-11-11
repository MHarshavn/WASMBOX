import type { RunDraft } from '../api/types';

export function RunSettings({
  draft,
  onChange,
  disabled,
}: {
  draft: RunDraft;
  onChange: (patch: Partial<RunDraft>) => void;
  disabled: boolean;
}) {
  return (
    <section className="panel settings-panel" aria-labelledby="settings-title">
      <div className="panel-heading">
        <h2 id="settings-title">Execution settings</h2>
        <span className="tag">REQUESTED LIMITS</span>
      </div>
      <fieldset disabled={disabled}>
        <label htmlFor="plugin-input">
          Plugin input <span className="muted">JSON object</span>
        </label>
        <textarea
          id="plugin-input"
          className="json-input"
          spellCheck={false}
          value={draft.input}
          onChange={(event) => onChange({ input: event.target.value })}
        />
        <div className="limits-grid">
          <label>
            Memory <span className="unit">MB</span>
            <input
              type="number"
              min="1"
              step="1"
              value={draft.memory}
              onChange={(event) => onChange({ memory: event.target.value })}
            />
          </label>
          <label>
            Timeout <span className="unit">ms</span>
            <input
              type="number"
              min="1"
              step="1"
              value={draft.timeout}
              onChange={(event) => onChange({ timeout: event.target.value })}
            />
          </label>
        </div>
        <label>
          Instruction limit <span className="muted">optional</span>
          <input
            type="number"
            min="1"
            step="1"
            placeholder="Backend default"
            value={draft.instructions}
            onChange={(event) => onChange({ instructions: event.target.value })}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={draft.hostLog}
            onChange={(event) => onChange({ hostLog: event.target.checked })}
          />{' '}
          Allow host.log capability
        </label>
        <p className="help">
          No host capabilities are requested by default. The backend validates and enforces all
          limits and permissions.
        </p>
      </fieldset>
    </section>
  );
}
