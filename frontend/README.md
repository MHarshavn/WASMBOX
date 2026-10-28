# WASMBOX developer portal — Issue #5

React + TypeScript + Monaco UI implementing the existing [API contract](../docs/api/API_CONTRACTS.md).
Plugin Python is sent to the backend; the browser never evaluates it.

## Start

Use Node.js 22.12+ (Node 24 recommended) and npm.

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, normally `http://127.0.0.1:5173`.
Start the team's backend separately on port 8000. There is no backend implementation
on the initial developer-portal branch. Without one, Run reports a connection error;
there is no fake-success mode in the shipped application.

Copy `.env.example` to `.env.local` if configuration is needed, then restart Vite:

| Variable            | Default                 | Meaning                                                                |
| ------------------- | ----------------------- | ---------------------------------------------------------------------- |
| `API_PROXY_TARGET`  | `http://127.0.0.1:8000` | Vite development proxy upstream for `/api`                             |
| `VITE_API_BASE_URL` | empty                   | Optional API origin, without `/api/v1`; e.g. `https://api.example.com` |

Prefer same-origin `/api` routing. Requests use `credentials: 'same-origin'` so
existing same-origin backend session cookies are included. Cross-origin deployments
must supply their own approved authentication/CORS integration; no login, tenant
header, bearer token, or tenant identity is invented here. `VITE_*` variables are
public build-time configuration and must never contain secrets.

## Developer workflow

1. Edit Python in Monaco. Assets and the editor worker are bundled locally, with no Monaco CDN dependency.
   If Monaco cannot load, select **Use basic editor** to continue with the same source.
2. Enter a plugin name and an input JSON object. Set positive integer memory/timeout
   limits and an optional instruction limit. The backend decides platform maximums.
3. Select **Run plugin**. The portal validates input, compiles the source, starts
   execution, and polls the execution result every 300 ms.
4. Inspect stdout/stderr, the canonical execution state, termination reason, and
   backend-provided execution time in milliseconds and memory in MB. Missing metrics
   show a dash; zero is a valid measurement. Output is rendered as text.
5. Use **Save plugin** to keep source, name, input and settings in this browser.
   Select a library entry to load it; subsequent saves update that entry. New plugin
   creates a separate draft. Deleting asks for confirmation and keeps editor contents.
6. Enter an event JSON object in **Webhook simulator** and send it. This compiles the
   current source and executes it with the event as `input`, without replacing the
   normal input field. No listener or externally callable webhook is registered.

Save/load uses `localStorage` under `wasmbox.portal.plugins.v1`, up to 100 plugins.
It is device/browser-profile storage, shared across accounts using that profile;
it is not tenant-scoped server persistence or encrypted secret storage. No save/load
endpoints exist in the agreed API. Storage errors preserve editor contents; invalid
stored data is not automatically overwritten. Back up or clear that key through
browser storage tools to recover corrupt local data. Unsaved edits trigger warnings
before switching drafts or leaving the page.

## Backend handoff

The contract is unchanged:

| Operation | Endpoint                                | Frontend behavior                                                                                            |
| --------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Compile   | `POST /api/v1/plugins/compile`          | Send `plugin_name`, `source_code`, `python_version: "3.x"`; require `COMPILED`, `plugin_id`, `wasm_artifact` |
| Execute   | `POST /api/v1/plugins/execute`          | Send returned `plugin_id`, JSON `input`, `limits`, and `capabilities`                                        |
| Result    | `GET /api/v1/executions/{execution_id}` | Poll pending states until a canonical success/failure state                                                  |

`capabilities` defaults to `[]`; the checkbox explicitly requests `host.log` only.
The backend must authorize the request and enforce capabilities, tenant isolation,
memory, instruction, and runtime limits. The portal is not the security boundary.
Input is passed unchanged as a JSON object; the Python-side input binding belongs
to the runtime contract and is not assumed by the starter example.

Structured errors work on both successful HTTP responses and non-2xx responses.
Connection, invalid response, authentication, compilation and runtime errors are
displayed without discarding source. Duplicate concurrent submissions are blocked.
Requests have a 15-second client deadline; result polling has a separate 60-second
deadline. **Stop waiting** aborts browser requests only. It does not terminate an
already-started backend execution. A previous state and execution ID may remain
visible after a connection failure; these are the last known state, not confirmation
that the backend has stopped. Check the execution ID before retrying after ambiguity.

## Verification

```bash
npm run format:check
npm test
npm run build
npx playwright install chromium
npm run test:e2e
npm audit
```

Vitest uses a lightweight source-editor substitute for fast UI tests. Playwright
loads the actual Monaco editor/worker in Chromium at desktop and mobile widths.
Browser tests intercept the three API endpoints with contract fixtures; they test
HTTP payloads and frontend behavior, not Python compilation or WASM isolation.
Screenshots and retained failure traces are written to ignored `test-results/`.
If the downloaded Chromium cannot launch on Windows, use an installed browser:
`$env:PLAYWRIGHT_CHANNEL='chrome'; npm run test:e2e` in PowerShell (or `msedge`
for installed Edge). This affects test browser selection only. CI uses bundled Chromium.
The build lazy-loads Monaco; Vite's large-chunk warning is expected for that editor.
DOMPurify is overridden to a patched compatible version because Monaco pins its
transitive sanitizer dependency. Recheck the override when updating Monaco.

| Acceptance criterion             | Automated coverage                                                                                                            |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Enter Python in Monaco           | Browser editing and exact saved-source reload                                                                                 |
| Compile/run through API          | Request-body assertions and compile → execute → poll tests                                                                    |
| stdout/stderr and failures       | Safe output rendering, compilation and all canonical runtime failures                                                         |
| Status, execution time, memory   | Success/failure, fractional/zero/missing metrics                                                                              |
| Save/load and simulated webhooks | Remount persistence, delete confirmation, event payload submission                                                            |
| Robust frontend behavior         | Invalid JSON/limits, HTTP/auth/network errors, malformed responses, cancellation, polling deadlines, storage quota/corruption |

Real end-to-end acceptance remains dependent on Issues #2–#4 and the orchestrator
integration. With that backend available, run a benign plugin, a syntax error, a
runtime error, a timeout, a memory-limit failure, and an input-consuming plugin.
Verify the real compiler/runtime supplies the documented output, metrics, and tenant
session behavior. Frontend fixtures do not prove sandbox security or sub-5ms latency.

## Production build

```bash
npm run build
npm run preview
```

Serve `dist/` through the deployment web server; `preview` is for local checks.
Route `/api` to the real backend in production (Vite's proxy is development-only).
Serve the local worker assets from the same origin. A starting CSP for this portal
is `default-src 'self'; script-src 'self'; worker-src 'self' blob:; style-src 'self'
'unsafe-inline'; font-src 'self' data:; connect-src 'self'`; adapt it for your
deployment and verify Monaco under the final policy. No new API route or backend
compiler/sandbox behavior is introduced by this frontend.
