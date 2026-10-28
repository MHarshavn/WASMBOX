/** Public API shapes from docs/api/API_CONTRACTS.md. */
export const executionStates = [
  'CREATED',
  'COMPILING',
  'READY',
  'RUNNING',
  'SUCCESS',
  'COMPILATION_FAILED',
  'EXECUTION_FAILED',
  'TIMEOUT',
  'MEMORY_LIMIT',
  'INSTRUCTION_LIMIT',
  'PERMISSION_DENIED',
  'SANDBOX_ERROR',
] as const;
export type ExecutionStatus = (typeof executionStates)[number];
export const pendingStates: ReadonlySet<ExecutionStatus> = new Set([
  'CREATED',
  'COMPILING',
  'READY',
  'RUNNING',
]);
export const isTerminal = (status: ExecutionStatus) => !pendingStates.has(status);
export interface ResourceLimits {
  memory_mb: number;
  timeout_ms: number;
  instruction_limit?: number;
}
export interface CompileRequest {
  plugin_name: string;
  source_code: string;
  python_version: '3.x';
}
export interface CompiledPlugin {
  status: 'COMPILED';
  plugin_id: string;
  wasm_artifact: string;
}
export interface ExecuteRequest {
  plugin_id: string;
  input: Record<string, unknown>;
  limits: ResourceLimits;
  capabilities: string[];
}
export interface ExecutionResult {
  execution_id: string;
  status: ExecutionStatus;
  stdout?: string;
  stderr?: string;
  execution_time_ms?: number | null;
  memory_used_mb?: number | null;
  termination_reason?: string | null;
}
export interface RunDraft {
  name: string;
  source: string;
  input: string;
  memory: string;
  timeout: string;
  instructions: string;
  hostLog: boolean;
}
export const starterSource = `# Your code runs on the WASMBOX backend.
# Use print() to send output to the console.
import json

record = {"company": "Acme", "amount": 1250, "currency": "USD"}
print(json.dumps({"company": record["company"].upper(),
                  "total": record["amount"],
                  "currency": record["currency"]}))
`;
export const defaultDraft: RunDraft = {
  name: 'company-data-parser',
  source: starterSource,
  input: '{}',
  memory: '10',
  timeout: '50',
  instructions: '',
  hostLog: false,
};
