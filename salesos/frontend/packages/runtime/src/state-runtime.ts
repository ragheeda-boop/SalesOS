import { useState, useCallback, useSyncExternalStore } from 'react'

export interface StateRuntimeOptions {
  name?: string
  debug?: boolean
}

type Listener = () => void

export class StateRuntime {
  private store: Record<string, unknown> = {}
  private listeners = new Map<string, Set<Listener>>()
  private name: string
  private debug: boolean

  constructor(options?: StateRuntimeOptions) {
    this.name = options?.name || 'default'
    this.debug = options?.debug || false
  }

  private notify(path: string) {
    const deps = this.listeners.get(path)
    if (deps) deps.forEach((fn) => fn())
    const parts = path.split('.')
    while (parts.length > 1) {
      parts.pop()
      const parent = this.listeners.get(parts.join('.'))
      if (parent) parent.forEach((fn) => fn())
    }
  }

  get<T = unknown>(path: string): T | undefined {
    return this.resolve(path) as T | undefined
  }

  set<T = unknown>(path: string, value: T): void {
    this.log(`set ${path} =`, value)
    const keys = path.split('.')
    let current: Record<string, unknown> = this.store
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in current) || typeof current[keys[i]] !== 'object') {
        current[keys[i]] = {}
      }
      current = current[keys[i]] as Record<string, unknown>
    }
    current[keys[keys.length - 1]] = value
    this.notify(path)
  }

  update<T = unknown>(path: string, updater: (prev: T | undefined) => T): void {
    const current = this.get<T>(path)
    this.set(path, updater(current))
  }

  subscribe(path: string, listener: Listener): () => void {
    if (!this.listeners.has(path)) {
      this.listeners.set(path, new Set())
    }
    this.listeners.get(path)!.add(listener)
    return () => {
      this.listeners.get(path)?.delete(listener)
    }
  }

  useStore<T = unknown>(path: string): T | undefined {
    const getSnapshot = useCallback(() => this.get<T>(path), [path])
    const subscribe = useCallback(
      (onStoreChange: () => void) => this.subscribe(path, onStoreChange),
      [path]
    )
    return useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
  }

  clear(path?: string): void {
    if (path) {
      const keys = path.split('.')
      let current: Record<string, unknown> = this.store
      for (let i = 0; i < keys.length - 1; i++) {
        if (!(keys[i] in current)) return
        current = current[keys[i]] as Record<string, unknown>
      }
      delete current[keys[keys.length - 1]]
      this.notify(path)
    } else {
      this.store = {}
      this.listeners.forEach((listeners) => listeners.forEach((fn) => fn()))
    }
  }

  getAll(): Record<string, unknown> {
    return { ...this.store }
  }

  private resolve(path: string): unknown {
    return path.split('.').reduce<unknown>((acc, key) => {
      if (acc && typeof acc === 'object' && key in acc) {
        return (acc as Record<string, unknown>)[key]
      }
      return undefined
    }, this.store)
  }

  private log(...args: unknown[]) {
    if (this.debug) console.log(`[StateRuntime:${this.name}]`, ...args)
  }
}
