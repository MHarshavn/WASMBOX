import { describe, expect, it } from 'vitest';
import { defaultDraft } from '../api/types';
import { parseInput, validateDraft } from './validation';

describe('execution validation', () => {
  it('keeps input and limits in the contract shape', () => {
    expect(validateDraft({ ...defaultDraft, input: '{"count":3}', instructions: '1000' })).toEqual({
      input: { count: 3 },
      limits: { memory_mb: 10, timeout_ms: 50, instruction_limit: 1000 },
    });
    expect(validateDraft(defaultDraft).limits).not.toHaveProperty('instruction_limit');
  });
  it.each(['[]', 'null', 'true', '"hello"', '2', '{invalid}'])(
    'rejects invalid input %s',
    (value) => {
      expect(() => parseInput(value)).toThrow(/JSON/);
    },
  );
  it.each(['0', '-1', '0.5', '', 'NaN', 'Infinity', '9007199254740992'])(
    'rejects invalid limits %s',
    (value) => {
      expect(() => validateDraft({ ...defaultDraft, memory: value })).toThrow(
        /positive whole number/,
      );
    },
  );
  it('rejects empty source, missing name, and oversized names', () => {
    expect(() => validateDraft({ ...defaultDraft, source: '  ' })).toThrow(/Python source/);
    expect(() => validateDraft({ ...defaultDraft, name: ' ' })).toThrow(/name/);
    expect(() => validateDraft({ ...defaultDraft, name: 'a'.repeat(121) })).toThrow(/120/);
  });
});
