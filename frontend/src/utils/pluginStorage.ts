import { useState } from 'react';
import type { RunDraft } from '../api/types';

export const storageKey = 'wasmbox.portal.plugins.v1';
export interface SavedPlugin {
  id: string;
  updatedAt: string;
  draft: RunDraft;
}
const stringFields = ['name', 'source', 'input', 'memory', 'timeout', 'instructions'] as const;

export function readPlugins(): SavedPlugin[] {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return [];
    const data: unknown = JSON.parse(raw);
    if (
      !Array.isArray(data) ||
      data.length > 100 ||
      !data.every(
        (plugin) =>
          plugin &&
          typeof plugin.id === 'string' &&
          typeof plugin.updatedAt === 'string' &&
          Number.isFinite(Date.parse(plugin.updatedAt)) &&
          plugin.draft &&
          stringFields.every((key) => typeof plugin.draft[key] === 'string') &&
          typeof plugin.draft.hostLog === 'boolean',
      ) ||
      new Set(data.map((plugin) => plugin.id)).size !== data.length
    )
      throw new Error('Invalid saved data');
    return data;
  } catch {
    throw new Error(
      'Could not read saved plugins. Browser storage may be disabled or contain invalid data. Existing data has been preserved.',
    );
  }
}

export function writePlugins(plugins: SavedPlugin[]) {
  if (plugins.length > 100)
    throw new Error('The local library holds up to 100 plugins. Delete an unused plugin first.');
  try {
    localStorage.setItem(storageKey, JSON.stringify(plugins));
  } catch {
    throw new Error(
      'Could not save plugins. Browser storage may be full or disabled. Your editor contents are still available.',
    );
  }
}

export function usePluginLibrary() {
  const [initial] = useState(() => {
    try {
      return { plugins: readPlugins(), error: '' };
    } catch (error) {
      return { plugins: [] as SavedPlugin[], error: (error as Error).message };
    }
  });
  const [plugins, setPlugins] = useState(initial.plugins);
  const [error, setError] = useState(initial.error);
  const commit = (next: SavedPlugin[]) => {
    if (initial.error) {
      setError(initial.error);
      return false;
    }
    try {
      writePlugins(next);
      setPlugins(next);
      setError('');
      return true;
    } catch (problem) {
      setError((problem as Error).message);
      return false;
    }
  };
  return {
    plugins,
    error,
    save(draft: RunDraft, id: string | null): string | null {
      const saved: SavedPlugin = {
        id: id ?? crypto.randomUUID(),
        updatedAt: new Date().toISOString(),
        draft: { ...draft },
      };
      return commit([saved, ...plugins.filter((plugin) => plugin.id !== saved.id)])
        ? saved.id
        : null;
    },
    remove(id: string) {
      return commit(plugins.filter((plugin) => plugin.id !== id));
    },
  };
}
