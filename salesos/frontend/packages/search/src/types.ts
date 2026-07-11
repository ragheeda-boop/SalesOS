export type SearchEntityType =
  | 'company' | 'person' | 'signal' | 'license' | 'government_record'
  | 'timeline_event' | 'document' | 'opportunity' | 'employee'
  | 'ai_answer' | 'knowledge_graph'

export type SearchIntent = 'search' | 'navigate' | 'question' | 'command'
export type SortOption = 'relevance' | 'recency' | 'name'

export interface SearchHighlight {
  field: string
  text: string
  snippets: string[]
}

export interface SearchBadge {
  label: string
  variant: 'info' | 'success' | 'warning' | 'danger' | 'neutral'
}

export interface SearchAction {
  id: string
  label: string
  icon?: string
  handler: string
}

export interface SearchRelationship {
  id: string
  type: string
  label: string
  direction: 'inbound' | 'outbound' | 'bidirectional'
}

export interface SearchResult {
  id: string
  entityType: SearchEntityType
  title: string
  subtitle: string
  description?: string
  score: number
  confidence: number
  highlights: SearchHighlight[]
  badges: SearchBadge[]
  actions: SearchAction[]
  source: string
  updatedAt: string
  thumbnail?: string
  relationships?: SearchRelationship[]
}

export interface SearchFilter {
  field: string
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'between' | 'contains'
  value: unknown
}

export interface SearchQuery {
  text: string
  types?: SearchEntityType[]
  filters?: SearchFilter[]
  page?: number
  pageSize?: number
  sort?: SortOption
  scope?: { entityType?: string; entityId?: string }
  naturalLanguage?: boolean
}

export interface SearchFacet {
  field: string
  label: string
  values: { value: string; count: number }[]
}

export interface QueryInterpretation {
  original: string
  interpreted: string
  entities: { type: string; value: string }[]
  intent: SearchIntent
  confidence: number
}

export interface AIAnswer {
  summary: string
  explanation?: string
  recommendations?: string[]
  risks?: string[]
  sources: { id: string; title: string; score: number }[]
  confidence: number
  tokens: number
}

export interface SearchTiming {
  total: number
  fullText: number
  semantic: number
  graph: number
  ai: number
  permissions: number
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  pageSize: number
  facets: SearchFacet[]
  aiAnswer?: AIAnswer
  suggestedQueries?: string[]
  queryInterpretation?: QueryInterpretation
  timing: SearchTiming
}

export interface SearchSuggestion {
  text: string
  type: 'query' | 'entity' | 'recent'
  entityType?: SearchEntityType
  entityId?: string
  score: number
}

export interface SearchHistoryEntry {
  id: string
  text: string
  timestamp: number
  resultCount?: number
}

export interface SavedSearch {
  id: string
  name: string
  query: SearchQuery
  createdAt: string
  updatedAt: string
}

export interface SearchContextValue {
  query: SearchQuery
  results: SearchResult[]
  total: number
  facets: SearchFacet[]
  aiAnswer: AIAnswer | null
  isLoading: boolean
  isError: boolean
  error: Error | null
  suggestions: SearchSuggestion[]
  history: SearchHistoryEntry[]
  setQuery: (query: Partial<SearchQuery>) => void
  search: (text: string) => void
  clearSearch: () => void
  refetch: () => void
}
