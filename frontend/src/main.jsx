import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import Editor from "@monaco-editor/react";
import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const DEFAULT_SOURCE = "print('Hello from WASMBOX')";

function errorMessage(body, fallback) {
  return body?.error?.message ?? fallback;
}

function App() {
  const [source, setSource] = useState(DEFAULT_SOURCE);
  const [pluginName, setPluginName] = useState("hello-wasmbox");
  const [tenantId, setTenantId] = useState(localStorage.getItem("wasmbox-tenant") || "demo-tenant");
  const [pluginId, setPluginId] = useState("");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("IDLE");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const headers = useMemo(() => ({
    "Content-Type": "application/json",
    "X-Tenant-ID": tenantId,
  }), [tenantId]);

  useEffect(() => localStorage.setItem("wasmbox-tenant", tenantId), [tenantId]);

  async function request(path, options) {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    const body = await response.json().catch(() => null);
    if (!response.ok) throw new Error(errorMessage(body, `Request failed (${response.status})`));
    return body;
  }

  async function compile() {
    setBusy(true); setError(""); setResult(null); setStatus("COMPILING");
    try {
      const body = await request("/api/v1/plugins/compile", {
        method: "POST", headers,
        body: JSON.stringify({ plugin_name: pluginName, source_code: source, python_version: "3.x" }),
      });
      setPluginId(body.plugin_id);
      setStatus(body.status);
    } catch (cause) {
      setStatus("COMPILATION_FAILED"); setError(cause.message);
    } finally { setBusy(false); }
  }

  async function run() {
    if (!pluginId) {
      setError("Compile the current source successfully before running it.");
      return;
    }
    setBusy(true); setError(""); setResult(null); setStatus("RUNNING");
    try {
      const submitted = await request("/api/v1/plugins/execute", {
        method: "POST", headers,
        body: JSON.stringify({ plugin_id: pluginId, input: {}, limits: { memory_mb: 128, timeout_ms: 5000 }, capabilities: [] }),
      });
      setStatus(submitted.status);
      let body;
      for (let attempt = 0; attempt < 30; attempt += 1) {
        body = await request(`/api/v1/executions/${submitted.execution_id}`, { headers });
        if (body.status !== "RUNNING") break;
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      setResult(body); setStatus(body.status);
    } catch (cause) {
      setStatus("EXECUTION_FAILED"); setError(cause.message);
    } finally { setBusy(false); }
  }

  return <main className="shell">
    <header><div><p className="eyebrow">DEVELOPER PORTAL</p><h1>WASMBOX</h1></div><span className={`status ${status.toLowerCase()}`}>{status}</span></header>
    <section className="controls" aria-label="Plugin settings">
      <label>Plugin name<input value={pluginName} onChange={(event) => setPluginName(event.target.value)} /></label>
      <label>Tenant ID<input value={tenantId} onChange={(event) => setTenantId(event.target.value)} /></label>
      <div className="actions"><button onClick={compile} disabled={busy}>Compile</button><button className="primary" onClick={run} disabled={busy || !pluginId}>Run</button></div>
    </section>
    <section className="workspace">
      <div className="editor-pane"><div className="pane-title">plugin.py</div><Editor height="470px" defaultLanguage="python" value={source} onChange={(value) => setSource(value ?? "")} theme="vs-dark" options={{ minimap: { enabled: false }, fontSize: 14, padding: { top: 14 } }} /></div>
      <aside className="results-pane">
        <div className="pane-title">Execution</div>
        <dl><dt>Plugin ID</dt><dd>{pluginId || "—"}</dd><dt>Time</dt><dd>{result?.execution_time_ms == null ? "—" : `${result.execution_time_ms} ms`}</dd><dt>Memory</dt><dd>{result?.memory_used_mb == null ? "—" : `${result.memory_used_mb} MB RSS`}</dd><dt>Reason</dt><dd>{result?.termination_reason ?? "—"}</dd></dl>
        {error && <div className="error" role="alert">{error}</div>}
        <Output title="stdout" value={result?.stdout} /><Output title="stderr" value={result?.stderr} muted />
      </aside>
    </section>
    <p className="note">Current execution adapter: permission-limited Emscripten MicroPython prototype. It is not Wasmtime.</p>
  </main>;
}

function Output({ title, value, muted = false }) {
  return <section className="output"><h2>{title}</h2><pre className={muted ? "muted" : ""}>{value || "(empty)"}</pre></section>;
}

createRoot(document.getElementById("root")).render(<App />);
