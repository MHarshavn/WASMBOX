import { Component, lazy, Suspense, useState, type ReactNode } from 'react';
const MonacoPython = lazy(() => import('./MonacoPython'));

class EditorBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}

export function SourceEditor({ source, onChange, readOnly = false }: {
  source: string; onChange: (value: string) => void; readOnly?: boolean;
}) {
  const [basic, setBasic] = useState(false);
  const fallback = <textarea className="basic-editor" aria-label="Python source" spellCheck={false}
    value={source} onChange={event => onChange(event.target.value)} readOnly={readOnly} />;
  return <section className="panel editor-panel" aria-label="Plugin editor">
    <div className="panel-heading"><span><span className="file-dot" /> main.py</span>
      <div className="editor-tools"><span className="muted">Python 3.x</span>
        <button className="text-button" onClick={() => setBasic(!basic)}>{basic ? 'Use Monaco' : 'Use basic editor'}</button>
      </div>
    </div>
    <div className="editor-surface">
      {basic ? fallback : <EditorBoundary fallback={<><p role="alert">Monaco could not load. You can continue in the basic editor.</p>{fallback}</>}>
        <Suspense fallback={<p className="editor-loading" role="status">Loading Python editor…</p>}>
          <MonacoPython source={source} onChange={onChange} readOnly={readOnly} />
        </Suspense>
      </EditorBoundary>}
    </div>
    <div className="editor-footer"><span>UTF-8 <span className="separator">/</span> 4 spaces</span><span>Execution happens on the backend</span></div>
  </section>;
}
