import type { SavedSearch, SearchQuery } from './types'

const STORAGE_KEY = 'salesos_saved_searches'

export function loadSavedSearches(): SavedSearch[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function saveSearch(name: string, query: SearchQuery): SavedSearch[] {
  const searches = loadSavedSearches()
  const existing = searches.findIndex((s) => s.name === name)
  const saved: SavedSearch = {
    id: existing >= 0 ? searches[existing].id : Date.now().toString(),
    name,
    query,
    createdAt: existing >= 0 ? searches[existing].createdAt : new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  const updated = existing >= 0
    ? [...searches.slice(0, existing), saved, ...searches.slice(existing + 1)]
    : [saved, ...searches]
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  } catch { /* ignore */ }
  return updated
}

export function deleteSavedSearch(id: string): SavedSearch[] {
  const searches = loadSavedSearches().filter((s) => s.id !== id)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(searches))
  } catch { /* ignore */ }
  return searches
}

export function runSavedSearch(saved: SavedSearch): SearchQuery {
  return { ...saved.query }
}
