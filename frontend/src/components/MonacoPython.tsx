import Editor, { loader } from '@monaco-editor/react';
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
import 'monaco-editor/esm/vs/basic-languages/python/python.contribution';
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';

self.MonacoEnvironment = { getWorker: () => new EditorWorker() };
loader.config({ monaco });

export default function MonacoPython({ source, onChange, readOnly }: {
  source: string; onChange: (value: string) => void; readOnly: boolean;
}) {
  return <Editor
    height="100%" language="python" theme="vs-dark" value={source}
    onChange={(value) => onChange(value ?? '')}
    loading={<p className="editor-loading" role="status">Loading Python editor…</p>}
    options={{
      ariaLabel: 'Python source', readOnly, automaticLayout: true,
      minimap: { enabled: false }, fontSize: 14, lineHeight: 24,
      fontFamily: "'Cascadia Code', 'Consolas', monospace", padding: { top: 20 },
      scrollBeyondLastLine: false, tabSize: 4, insertSpaces: true,
      wordWrap: 'on', fixedOverflowWidgets: true,
    }}
  />;
}
