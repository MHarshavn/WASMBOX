import { useEffect, useState } from 'react';
import { defaultDraft, type RunDraft } from './api/types';
import { ExecutionMetrics } from './components/ExecutionMetrics';
import { ExecutionOutput } from './components/ExecutionOutput';
import { PluginLibrary } from './components/PluginLibrary';
import { RunSettings } from './components/RunSettings';
import { SourceEditor } from './components/SourceEditor';
import { WebhookPanel } from './components/WebhookPanel';
import { useExecution } from './hooks/useExecution';
import { usePluginLibrary, type SavedPlugin } from './utils/pluginStorage';

export default function App() {
  const [draft, setDraft] = useState<RunDraft>({ ...defaultDraft });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [baseline, setBaseline] = useState(JSON.stringify(defaultDraft));
  const [saveMessage, setSaveMessage] = useState('');
  const library = usePluginLibrary();
  const execution = useExecution();
  const dirty = JSON.stringify(draft) !== baseline;
  const patch = (changes: Partial<RunDraft>) => { setDraft(current => ({ ...current, ...changes })); setSaveMessage(''); };
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);
  const canReplace = () => !dirty || window.confirm('Discard unsaved editor changes?');
  const load = (plugin: SavedPlugin) => {
    if (!canReplace()) return;
    setDraft({ ...plugin.draft }); setSelectedId(plugin.id); setBaseline(JSON.stringify(plugin.draft)); setSaveMessage('Loaded local plugin.'); execution.reset();
  };
  const create = () => {
    if (!canReplace()) return;
    const fresh = { ...defaultDraft, name: 'untitled-plugin', source: '# Write your Python plugin here\n' };
    setDraft(fresh); setSelectedId(null); setBaseline(JSON.stringify(fresh)); setSaveMessage(''); execution.reset();
  };
  const save = () => {
    if (!draft.name.trim()) { setSaveMessage('Enter a plugin name before saving.'); return; }
    const id = library.save(draft, selectedId);
    if (id) { setSelectedId(id); setBaseline(JSON.stringify(draft)); setSaveMessage('Saved in this browser.'); }
  };
  return <div className="app-shell">
    <a className="skip-link" href="#workspace">Skip to editor</a>
    <header className="topbar"><a className="brand" href="./" aria-label="WASMBOX home"><span className="brand-mark">W</span>WASM<span>BOX</span></a>
      <span className="topbar-divider" /><span className="topbar-section">Developer portal</span>
      <span className="environment-badge">API WORKSPACE</span>
    </header>
    <div className="workspace-layout">
      <PluginLibrary plugins={library.plugins} selectedId={selectedId} onLoad={load} onNew={create} disabled={execution.busy} error={library.error}
        onDelete={id => { if (library.remove(id) && id === selectedId) { setSelectedId(null); setSaveMessage('Local copy deleted. Editor contents retained.'); } }} />
      <main id="workspace" className="workspace" tabIndex={-1}>
        <div className="workspace-intro"><div><p className="eyebrow">BUILD · RUN · INSPECT</p><h1>Plugin playground</h1><p>Turn your Python into a sandboxed workflow.</p></div>
          <span className="workspace-label">PYTHON / WEBASSEMBLY</span>
        </div>
        <div className="plugin-toolbar"><div className="plugin-name-field"><label htmlFor="plugin-name">Plugin name</label><input id="plugin-name" maxLength={120} value={draft.name} disabled={execution.busy} onChange={event => patch({ name: event.target.value })} />
          <span className="draft-state">{dirty ? 'Unsaved changes' : selectedId ? 'Saved locally' : 'Example draft'}</span></div>
          <div className="toolbar-actions"><button className="secondary-button" disabled={execution.busy} onClick={save}>Save plugin</button>
            {execution.busy ? <button className="secondary-button" onClick={execution.stop}>Stop waiting</button> :
              <button className="primary-button" onClick={() => void execution.run(draft)}><span aria-hidden="true">▶</span> Run plugin</button>}
          </div>
        </div>
        {saveMessage && <p className="save-message" role="status">{saveMessage}</p>}
        <div className="workbench"><div className="primary-column">
          <SourceEditor source={draft.source} onChange={source => patch({ source })} readOnly={execution.busy} />
          <ExecutionMetrics result={execution.result} status={execution.status} />
          <ExecutionOutput {...execution} />
        </div><div className="settings-column"><RunSettings draft={draft} onChange={patch} disabled={execution.busy} />
          <WebhookPanel busy={execution.busy} onTrigger={input => void execution.run({ ...draft, input }, 'webhook')} />
          <div className="integration-note"><strong>Backend connection</strong><p>Compile → execute → fetch result</p><code>{import.meta.env.VITE_API_BASE_URL || 'Same origin /api/v1'}</code><p>Sandbox enforcement and Python input handling are provided by the backend.</p></div>
        </div></div>
        <footer className="workspace-footer"><span>WASMBOX <span className="muted">/ Developer workspace</span></span><span>Source stays in the editor until you run or save it.</span></footer>
      </main>
    </div>
  </div>;
}
