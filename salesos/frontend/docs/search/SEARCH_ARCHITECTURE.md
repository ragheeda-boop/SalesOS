# Universal Search Platform — Architecture

> SalesOS Wave 1 · Phase B
> Last Updated: 2026-07-10

---

## Vision

The Universal Search Platform is the single discovery engine for the entire SalesOS ecosystem. Every future feature consumes this platform instead of creating its own search implementation.

It combines:
- **Google** — full-text search across all entities
- **Spotlight** — instant global command bar (Ctrl+K / ⌘+K)
- **Bloomberg Search** — structured financial & entity search with facets
- **Knowledge Graph** — relationship-aware search (suppliers of, similar to, connected to)
- **AI Answer** — natural language understanding + summarization + recommendations

---

## Search Types

| Type | Engine | Use Case | Latency Budget |
|------|--------|----------|---------------|
| Full Text | PostgreSQL tsvector + pgroonga | Companies, People, Documents | <200ms |
| Semantic | pgvector + embedding model | Natural language queries | <500ms |
| Structured | PostgreSQL indexed columns | Filters, facets, ranges | <100ms |
| Knowledge Graph | Neo4j + relationship traversal | Connected entities, paths | <300ms |
| Hybrid | Weighted combination | Multi-strategy results | <800ms |
| Saved | Redis + PostgreSQL | Recent searches, bookmarks | <50ms |
| AI Answer | LLM + RAG pipeline | Summarize, explain, recommend | <3s |

---

## Data Sources

| Source | Entities | Update Cadence | Access Pattern |
|--------|----------|---------------|---------------|
| PostgreSQL (main) | Companies, People, Deals, Opportunities, Employees | Real-time CDC | Full text + structured |
| Neo4j (graph) | Relationships, hierarchies, ownership | Real-time CDC | Graph traversal |
| Vector Store (pgvector) | Embeddings for all text entities | Async batch | Semantic similarity |
| Redis | Search history, saved searches, cache, suggestions | Real-time | Key-value |
| Elasticsearch (future) | Large-scale full text | Planned for V2 | Full text + aggregations |

---

## Ranking & Scoring

```
score = w1 * relevance
      + w2 * recency
      + w3 * authority
      + w4 * user_affinity
      + w5 * relationship_proximity
      + w6 * ai_confidence
```

| Factor | Weight | Source |
|--------|--------|--------|
| Text relevance | 0.35 | tsvector rank / embedding similarity |
| Recency | 0.15 | Updated timestamp decay |
| Authority | 0.15 | Entity importance score (page rank, signals) |
| User affinity | 0.10 | User's interaction history |
| Relationship proximity | 0.10 | Graph distance from user's context |
| AI confidence | 0.15 | LLM confidence for interpreted queries |

---

## Caching Strategy

| Layer | Cache | TTL | Invalidation |
|-------|-------|-----|-------------|
| Browser | Search history, recent queries | Session | On new search |
| React Query | Search results by query hash | 30s | On mutation |
| Redis | Popular queries, suggestions, embeddings | 5min | TTL expiry |
| API | Aggregated results | 10s | Entity update event |
| CDN | Static assets, search page | 1h | Deployment |

---

## Permissions Model

Every search result is filtered through:

1. **Entity-level permissions** — user must have `{entityType}:read`
2. **Field-level permissions** — sensitive fields masked or excluded
3. **Scope permissions** — tenant-scoped (multi-tenant)
4. **Relationship permissions** — can user see connected entities

Permission check is **not** a post-filter. The query itself is scoped:

```sql
SELECT ... FROM companies c
WHERE c.tenant_id = $tenant_id
  AND has_permission($user_id, 'company', c.id)
  AND search_condition
```

---

## Performance Budgets

| Operation | Budget | Measurement |
|-----------|--------|------------|
| Quick search (typeahead) | <100ms | p95 |
| Full search | <500ms | p95 |
| AI Answer | <3s | p95 |
| Command bar open | <50ms | p95 |
| Result render | <16ms | per frame |
| Page load (search page) | <1s | p75 |

---

## Scoring Explanation

Every result includes a `score` (0.0–1.0) and a breakdown per factor:

```json
{
  "id": "comp_123",
  "score": 0.87,
  "scoring": {
    "relevance": 0.92,
    "recency": 0.80,
    "authority": 0.75,
    "userAffinity": 0.60,
    "proximity": 0.85,
    "aiConfidence": 0.90
  }
}
```

Scores are **relative within a query**, not absolute. They indicate ranking order.

---

## Telemetry

| Event | Payload | Purpose |
|-------|---------|---------|
| `search.query` | query, type, filters, resultCount, durationMs | Usage analytics |
| `search.result_click` | resultId, entityType, position | Ranking effectiveness |
| `search.ai_answer` | query, tokens, latency, satisfaction | AI quality |
| `search.command_bar_open` | trigger (keyboard/click) | Adoption |
| `search.fallback` | query, fallbackReason | Coverage gaps |
| `search.error` | query, errorType, errorMessage | Reliability |

---

## Accessibility

| Requirement | Implementation |
|------------|---------------|
| Keyboard navigation | Arrow keys, Tab, Enter, Escape |
| Screen reader | ARIA roles, live regions, announcements |
| Focus management | Trap within overlay, return on close |
| Dark mode | CSS variables, `dark:` variants |
| RTL | Arabic-first, `dir="rtl"`, logical properties |
| Reduced motion | `motion-reduce` class, CSS `prefers-reduced-motion` |
| High contrast | WCAG AA color contrast |
| Touch | Minimum 44px touch targets |

---

## Future-Proof Design

The Search SDK is designed to be consumed by:
- **Dashboard** — global search bar in header
- **Company Intelligence** — search within company context
- **Employee Intelligence** — search within employee context
- **CRM** — search deals, contacts, opportunities
- **Executive Workspace** — strategic search across all entities
- **AI Copilot** — natural language search interface
- **MCP Integrations** — external tool search via Model Context Protocol

Each consumer receives a scoped `SearchProvider` with the same SDK surface.
