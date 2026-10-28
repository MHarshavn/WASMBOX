import { expect, it, vi } from 'vitest';
import { defaultDraft } from '../api/types';
import { readPlugins, storageKey, writePlugins } from './pluginStorage';
const plugins = [{ id: 'p1', updatedAt: '2026-10-28T00:00:00Z', draft: defaultDraft }];
it('round trips source and settings without running anything', () => {
  expect(readPlugins()).toEqual([]); writePlugins(plugins); expect(readPlugins()).toEqual(plugins);
});
it.each(['{bad', '{}', '[{"id":"p"}]'])('preserves corrupt storage %s', raw => {
  localStorage.setItem(storageKey, raw); expect(() => readPlugins()).toThrow(/preserved/);
  expect(localStorage.getItem(storageKey)).toBe(raw);
});
it('reports browser quota errors without erasing saved data', () => {
  writePlugins(plugins);
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new DOMException('Quota', 'QuotaExceededError'); });
  expect(() => writePlugins([])).toThrow(/full or disabled/);
  expect(readPlugins()).toEqual(plugins);
});
