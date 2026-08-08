import { useCallback, useSyncExternalStore } from "react";

export interface StateRuntimeOptions {
  name?: string;
  debug?: boolean;
}

type Listener = (value?: unknown) => void;

const BLOCKED_KEYS = new Set(["__proto__", "constructor", "prototype"]);

function assertSafeKey(key: string): void {
  if (!key || BLOCKED_KEYS.has(key)) {
    throw new Error(`StateRuntime: blocked path key "${key}"`);
  }
}

function assertSafePath(path: string): string[] {
  const keys = path.split(".");
  for (const key of keys) {
    assertSafeKey(key);
  }
  return keys;
}

function emptyObject(): Record<string, unknown> {
  return Object.create(null) as Record<string, unknown>;
}

/** Safe nest: blocked keys + hasOwnProperty; avoids obj=obj[key] pollution loop. */
function ensureChild(parent: Record<string, unknown>, key: string): Record<string, unknown> {
  assertSafeKey(key);
  const next = Object.prototype.hasOwnProperty.call(parent, key) ? parent[key] : undefined;
  if (next === null || typeof next !== "object" || Array.isArray(next)) {
    const created = emptyObject();
    parent[key] = created;
    return created;
  }
  return next as Record<string, unknown>;
}

function readChild(
  parent: Record<string, unknown>,
  key: string
): Record<string, unknown> | undefined {
  assertSafeKey(key);
  if (!Object.prototype.hasOwnProperty.call(parent, key)) return undefined;
  const next = parent[key];
  if (next === null || typeof next !== "object" || Array.isArray(next)) return undefined;
  return next as Record<string, unknown>;
}

export class StateRuntime {
  private store: Record<string, unknown> = emptyObject();
  private listeners = new Map<string, Set<Listener>>();
  private name: string;
  private debug: boolean;

  constructor(options?: StateRuntimeOptions) {
    this.name = options?.name || "default";
    this.debug = options?.debug || false;
  }

  private notify(path: string, value?: unknown) {
    const deps = this.listeners.get(path);
    if (deps) deps.forEach((fn) => fn(value));
    const parts = path.split(".");
    while (parts.length > 1) {
      parts.pop();
      const parent = this.listeners.get(parts.join("."));
      if (parent) parent.forEach((fn) => fn(value));
    }
  }

  get<T = unknown>(path: string): T | undefined {
    return this.resolve(path) as T | undefined;
  }

  set<T = unknown>(path: string, value: T): void {
    this.log(`set ${path} =`, value);
    const keys = assertSafePath(path);
    let current: Record<string, unknown> = this.store;
    for (let i = 0; i < keys.length - 1; i++) {
      current = ensureChild(current, keys[i]);
    }
    const leaf = keys[keys.length - 1];
    assertSafeKey(leaf);
    current[leaf] = value;
    this.notify(path, value);
  }

  update<T = unknown>(path: string, updater: (prev: T | undefined) => T): void {
    const current = this.get<T>(path);
    this.set(path, updater(current));
  }

  subscribe(path: string, listener: Listener): () => void {
    assertSafePath(path);
    if (!this.listeners.has(path)) {
      this.listeners.set(path, new Set());
    }
    this.listeners.get(path)!.add(listener);
    return () => {
      this.listeners.get(path)?.delete(listener);
    };
  }

  clear(path?: string): void {
    if (path) {
      const keys = assertSafePath(path);
      let current: Record<string, unknown> = this.store;
      for (let i = 0; i < keys.length - 1; i++) {
        const next = readChild(current, keys[i]);
        if (!next) return;
        current = next;
      }
      const leaf = keys[keys.length - 1];
      assertSafeKey(leaf);
      delete current[leaf];
      this.notify(path);
    } else {
      this.store = emptyObject();
      this.listeners.forEach((listeners) => listeners.forEach((fn) => fn()));
    }
  }

  getAll(): Record<string, unknown> {
    return { ...this.store };
  }

  private resolve(path: string): unknown {
    const keys = assertSafePath(path);
    return keys.reduce<unknown>((acc, key) => {
      if (acc && typeof acc === "object" && Object.prototype.hasOwnProperty.call(acc, key)) {
        return (acc as Record<string, unknown>)[key];
      }
      return undefined;
    }, this.store);
  }

  private log(...args: unknown[]) {
    if (this.debug) console.log(`[StateRuntime:${this.name}]`, ...args);
  }
}

/** Function hook — must not live on the class (rules-of-hooks). Same get/subscribe snapshot as former `StateRuntime.useStore(path)`. */
export function useStore<T = unknown>(runtime: StateRuntime, path: string): T | undefined {
  const getSnapshot = useCallback(() => runtime.get<T>(path), [runtime, path]);
  const subscribe = useCallback(
    (onStoreChange: () => void) => runtime.subscribe(path, onStoreChange),
    [runtime, path]
  );
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
