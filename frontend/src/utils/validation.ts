import type { ResourceLimits, RunDraft } from '../api/types';

export function parseInput(text: string): Record<string, unknown> {
  let value: unknown;
  try { value = JSON.parse(text); }
  catch { throw new Error('Input must be valid JSON.'); }
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('Input must be a JSON object, such as {"event": "order.created"}.');
  }
  return value as Record<string, unknown>;
}

function positiveInteger(value: string, label: string): number {
  const number = Number(value);
  if (!value.trim() || !Number.isSafeInteger(number) || number <= 0) {
    throw new Error(`${label} must be a positive whole number.`);
  }
  return number;
}

export function validateDraft(draft: RunDraft): { input: Record<string, unknown>; limits: ResourceLimits } {
  if (!draft.name.trim()) throw new Error('Give your plugin a name.');
  if (draft.name.trim().length > 120) throw new Error('Plugin name must be 120 characters or fewer.');
  if (!draft.source.trim()) throw new Error('Enter Python source before running your plugin.');
  const limits: ResourceLimits = {
    memory_mb: positiveInteger(draft.memory, 'Memory limit'),
    timeout_ms: positiveInteger(draft.timeout, 'Timeout'),
  };
  if (draft.instructions.trim()) limits.instruction_limit = positiveInteger(draft.instructions, 'Instruction limit');
  return { input: parseInput(draft.input), limits };
}
