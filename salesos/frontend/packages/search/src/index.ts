export { SearchProvider, useSearchContext } from './search-provider'
export { searchTelemetry, createTelemetryTimer } from './search-telemetry'
export type { SearchTelemetryEventType, SearchTelemetryEvent } from './search-telemetry'
export { setSearchPermissionChecker, canSearch, canViewResult, filterResultsByPermission } from './search-permissions'
export type { SearchPermissionChecker } from './search-permissions'
export { SearchQueryBuilder, queryToKey, isQueryEmpty, isQueryShort } from './query-builder'
export { mapSearchResult, mapSearchResults, groupResultsByType } from './result-mapper'
export type { RawSearchResult } from './result-mapper'
export { SearchHighlight, extractSnippets } from './search-highlight'
export { createSuggestionEngine } from './search-suggestions'
export type { SuggestionEngine } from './search-suggestions'
export { loadHistory, saveHistory, addToHistory, clearHistory } from './search-history'
export { loadSavedSearches, saveSearch, deleteSavedSearch, runSavedSearch } from './saved-searches'
export { buildFilterQuery, parseFilterString, applyFacet, removeFacet, toggleFacet } from './search-filters'
export { getDefaultShortcuts, matchShortcut } from './search-shortcuts'
export type { SearchShortcutAction, ShortcutBinding } from './search-shortcuts'
export type {
  SearchEntityType, SearchIntent, SortOption,
  SearchHighlight as SearchHighlightType,
  SearchBadge, SearchAction, SearchRelationship,
  SearchResult, SearchFilter, SearchQuery,
  SearchFacet, QueryInterpretation, AIAnswer, SearchTiming,
  SearchResponse, SearchSuggestion, SearchHistoryEntry, SavedSearch,
  SearchContextValue,
} from './types'
