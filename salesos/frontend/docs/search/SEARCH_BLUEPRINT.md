# Universal Search Platform — Blueprint

> SalesOS Wave 1 · Phase B
> Build Order: SDK → Foundation Components → Command Bar → Search Experience → AI Search

---

## 1. Directory Structure

```
packages/search/                          # Reusable Search SDK
  package.json
  src/
    index.ts                              # Public API
    types.ts                              # Core search types
    search-provider.tsx                    # SearchProvider + useSearchContext
    search-telemetry.ts                   # Search telemetry
    search-permissions.ts                 # Permission checking
    query-builder.ts                      # SearchQuery builder
    result-mapper.ts                      # DTO → SearchResult mapper
    search-highlight.tsx                  # Text highlighting utility
    search-suggestions.ts                 # Suggestion engine
    search-history.ts                     # History manager
    saved-searches.ts                     # Saved search manager
    search-filters.ts                     # Filter builder + facet engine
    search-shortcuts.ts                   # Keyboard shortcuts registry
    testing/
      index.ts                            # Test utilities
      mockSearchResults.ts                # Mock data factories
      SearchContract.tsx                  # Contract tests

src/features/search/                      # Search UI
  index.ts                                # Public API
  _providers/
    global-search-provider.tsx            # App-level search provider (Ctrl+K)
  _layout/
    search-layout.tsx                     # Full search page layout
  quick-overlay/
    QuickOverlay.tsx                      # Quick search overlay (Spotlight-style)
    QuickOverlayHeader.tsx
    QuickOverlayResults.tsx
  command-bar/
    CommandBar.tsx                        # Ctrl+K / ⌘+K global command bar
    CommandBarInput.tsx
    CommandBarResults.tsx
    CommandBarActions.tsx
    CommandBarKeyboard.tsx
  search-page/
    SearchPage.tsx                        # Full search results page
    SearchFilters.tsx                     # Filter sidebar/panel
    SearchResults.tsx                     # Results list
  ai-search/
    AIAnswer.tsx                          # AI answer card
    AIExplain.tsx                         # AI explanation
    AIRecommend.tsx                       # AI recommendations
  components/                              # Foundation components
    SearchBar.tsx
    SearchInput.tsx
    SearchResultCard.tsx
    SearchSection.tsx
    SearchGroup.tsx
    SearchFilters.tsx
    SearchBadge.tsx
    SearchHighlight.tsx
    SearchEmpty.tsx
    SearchLoading.tsx
    SearchError.tsx
    SearchSuggestion.tsx
    SearchHistory.tsx
    SearchFacet.tsx
    SearchPill.tsx
    SearchHeader.tsx
  __tests__/
    command-bar.test.tsx
    quick-overlay.test.tsx
    search-page.test.tsx
    ai-search.test.tsx
    foundation.test.tsx

src/application/search/                   # Application layer
  search.dto.ts                           # API DTOs
  search.query.ts                         # Query parameters
  search.api.ts                           # API functions
  search.hooks.ts                         # React Query hooks
```

---

## 2. Component Hierarchy

```
App
  └── GlobalSearchProvider
       ├── CommandBar (Ctrl+K)
       │    ├── CommandBarInput
       │    ├── CommandBarResults
       │    │    ├── SearchSection (Suggestions)
       │    │    ├── SearchSection (Recent)
       │    │    └── SearchSection (Results)
       │    └── CommandBarActions
       ├── SearchPage
       │    ├── SearchBar
       │    ├── SearchFilters
       │    ├── SearchResults
       │    │    ├── SearchResultCard (per result)
       │    │    ├── SearchLoading
       │    │    ├── SearchEmpty
       │    │    └── SearchError
       │    └── AIAnswer
       └── QuickOverlay
            ├── QuickOverlayHeader
            └── QuickOverlayResults
```

---

## 3. Data Flow

```
User types
  → SearchInput captures query
    → SearchQueryBuilder builds SearchQuery { text, types, filters, page, sort }
      → useSearch(query) React Query hook
        → API call: POST /api/v1/search
          → Backend: hybrid search (full text + semantic + graph)
            → Entity Permission filter
              → Score + Rank
                → Result Mapper
                  → SearchResult[]
        → Cache in React Query (keyed by query hash)
          → Component re-render
            → VirtualList (only visible results)
              → SearchResultCard render
```

---

## 4. SearchResult Contract

```typescript
interface SearchResult {
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

type SearchEntityType =
  | 'company' | 'person' | 'signal' | 'license' | 'government_record'
  | 'timeline_event' | 'document' | 'opportunity' | 'employee'
  | 'ai_answer' | 'knowledge_graph'

interface SearchHighlight {
  field: string
  text: string
  snippets: string[]       // Matching fragments with <mark> tags
}

interface SearchBadge {
  label: string
  variant: 'info' | 'success' | 'warning' | 'danger' | 'neutral'
}

interface SearchAction {
  id: string
  label: string
  icon?: string
  handler: string          // Action ID for command bar
}

interface SearchRelationship {
  id: string
  type: string
  label: string
  direction: 'inbound' | 'outbound' | 'bidirectional'
}
```

---

## 5. SearchQuery Contract

```typescript
interface SearchQuery {
  text: string                              // The raw query text
  types?: SearchEntityType[]                // Filter by entity types
  filters?: SearchFilter[]                  // Structured filters
  page?: number
  pageSize?: number
  sort?: 'relevance' | 'recency' | 'name'
  scope?: {
    entityType?: string                     // Scoped search (e.g., inside company)
    entityId?: string
  }
  naturalLanguage?: boolean                 // Enable NL interpretation
}

interface SearchFilter {
  field: string
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'between' | 'contains'
  value: unknown
}
```

---

## 6. SearchResponse Contract

```typescript
interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  pageSize: number
  facets: SearchFacet[]
  aiAnswer?: AIAnswer
  suggestedQueries?: string[]
  queryInterpretation?: {
    original: string
    interpreted: string
    entities: SearchEntity[]
    intent: 'search' | 'navigate' | 'question' | 'command'
    confidence: number
  }
  timing: {
    total: number
    fullText: number
    semantic: number
    graph: number
    ai: number
    permissions: number
  }
}

interface SearchFacet {
  field: string
  label: string
  values: { value: string; count: number }[]
}

interface AIAnswer {
  summary: string
  explanation?: string
  recommendations?: string[]
  risks?: string[]
  sources: { id: string; title: string; score: number }[]
  confidence: number
  tokens: number
}
```

---

## 7. Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Open command bar | `Ctrl+K` / `⌘+K` | Global |
| Close overlay | `Escape` | Command bar, Quick overlay |
| Navigate results | `↑` `↓` | When results visible |
| Select result | `Enter` | When result focused |
| Open preview | `Ctrl+Enter` | When result focused |
| Clear search | `Escape` | When input has text |
| Focus search | `/` | Global |
| Switch facet | `Tab` / `Shift+Tab` | Within filters |
| AI answer | `Ctrl+Shift+A` | When on search page |

---

## 8. Build Order

| Phase | What | Depends On |
|-------|------|-----------|
| 1 | Search SDK types + providers | Workspace SDK |
| 2 | Query builder + result mapper | Phase 1 |
| 3 | Telemetry + permissions | Phase 1 |
| 4 | Foundation components | Phase 1–3 |
| 5 | Command Bar | Phase 4 |
| 6 | Quick Search Overlay | Phase 4 |
| 7 | Search Page | Phase 4–6 |
| 8 | AI Search | Phase 7 |
| 9 | Full test suite | Phase 1–8 |
| 10 | Quality pass (virtualization, perf) | Phase 9 |

---

## 9. Workspace SDK Reuse

| Workspace SDK Feature | Search Usage |
|-----------------------|-------------|
| `createWidget` | Search result widgets |
| `WorkspaceErrorBoundary` | Error boundaries for search sections |
| `WorkspaceGrid` | Search layout grid |
| `widgetTelemetry` | Search telemetry events |
| `checkPermissions` | Search result permissions |
| `isFeatureEnabled` | Search feature flags |
| `deriveStatus` | Result loading state |
