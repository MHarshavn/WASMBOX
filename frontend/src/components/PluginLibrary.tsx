import { useState } from 'react';
import type { SavedPlugin } from '../utils/pluginStorage';

export function PluginLibrary({ plugins, selectedId, onLoad, onNew, onDelete, disabled, error }: {
  plugins: SavedPlugin[]; selectedId: string | null; onLoad: (plugin: SavedPlugin) => void;
  onNew: () => void; onDelete: (id: string) => void; disabled: boolean; error: string;
}) {
  const [confirmId, setConfirmId] = useState<string | null>(null);
  return <aside className="library" aria-labelledby="library-title">
    <div className="library-heading"><h2 id="library-title">Your plugins <span>{plugins.length}</span></h2>
      <button className="icon-button" aria-label="New plugin" disabled={disabled} onClick={onNew}>+</button>
    </div>
    <p className="eyebrow library-label">LOCAL WORKSPACE</p>
    {error && <p className="error-message" role="alert">{error}</p>}
    {plugins.length === 0 && <p className="library-empty">Your saved plugins will appear here. Start with the example, or create a new plugin.</p>}
    <ul className="plugin-list">{plugins.map(plugin => <li key={plugin.id} className={plugin.id === selectedId ? 'selected' : ''}>
      <button className="plugin-entry" aria-label={`Load ${plugin.draft.name}`} disabled={disabled} aria-current={plugin.id === selectedId ? 'true' : undefined} onClick={() => onLoad(plugin)}>
        <span className="python-icon">py</span><span className="plugin-summary"><strong>{plugin.draft.name}</strong><small>{new Date(plugin.updatedAt).toLocaleString()}</small></span>
      </button>
      {confirmId === plugin.id ? <div className="delete-confirm"><span>Delete this local copy?</span>
        <button disabled={disabled} onClick={() => { onDelete(plugin.id); setConfirmId(null); }}>Delete</button>
        <button onClick={() => setConfirmId(null)}>Keep</button>
      </div> : <button className="delete-button" aria-label={`Delete ${plugin.draft.name}`} disabled={disabled} onClick={() => setConfirmId(plugin.id)}>×</button>}
    </li>)}</ul>
    <div className="library-note"><span className="note-icon">◈</span><strong>Saved on this browser</strong><p>Local copies stay on this device and are shared by anyone using this browser profile. Avoid storing secrets.</p></div>
  </aside>;
}
