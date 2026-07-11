import type { SearchSuggestion, SearchHistoryEntry } from './types'

export interface SuggestionEngine {
  getSuggestions(prefix: string, history: SearchHistoryEntry[]): SearchSuggestion[]
}

export function createSuggestionEngine(): SuggestionEngine {
  return {
    getSuggestions(prefix: string, history: SearchHistoryEntry[]): SearchSuggestion[] {
      if (!prefix || prefix.trim().length < 1) return []

      const lower = prefix.toLowerCase()
      const results: SearchSuggestion[] = []

      for (const entry of history) {
        if (entry.text.toLowerCase().includes(lower)) {
          results.push({
            text: entry.text,
            type: 'recent',
            score: Math.min(1, entry.timestamp / (Date.now() + 1)),
          })
        }
      }

      return results.slice(0, 5)
    },
  }
}
