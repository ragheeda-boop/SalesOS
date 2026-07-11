import type { SearchHistoryEntry } from './types'

const STORAGE_KEY = 'salesos_search_history'
const MAX_ITEMS = 50

export function loadHistory(): SearchHistoryEntry[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function saveHistory(history: SearchHistoryEntry[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, MAX_ITEMS)))
  } catch { /* storage full */ }
}

export function addToHistory(history: SearchHistoryEntry[], text: string, resultCount?: number): SearchHistoryEntry[] {
  const entry: SearchHistoryEntry = { id: Date.now().toString(), text, timestamp: Date.now(), resultCount }
  return [entry, ...history.filter((h) => h.text !== text)].slice(0, MAX_ITEMS)
}

export function clearHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch { /* ignore */ }
}
