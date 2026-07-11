# Search SDK Reference

> **SDK البحث — بحث هجين عبر جميع الكيانات**

Package: `@salesos/search` | Status: **Frozen** | Version: v1.0.0

---

## Installation

```bash
npm install @salesos/search
```

---

## Basic Usage

```typescript
import { SearchClient, SearchEntityType } from '@salesos/search'

const search = new SearchClient({
  baseUrl: 'https://api.salesos.sa',
  apiKey: 'sos_your_key',
  tenantId: 'tenant_xyz',
})

// Search companies
const results = await search.query({
  q: 'شركة المملكة للتقنية',
  types: [SearchEntityType.Company],
  limit: 10,
})

// Results
results.items.forEach(item => {
  console.log(item.name_ar, item.score)
})
```

---

## Scoped Search

```typescript
// Search within a specific company
const contacts = await search.withScope('company', 'comp_123').query({
  q: 'محمد',
  types: [SearchEntityType.Contact],
})

// Search within an opportunity
const activities = await search.withScope('opportunity', 'opp_456').query({
  q: 'meeting',
  types: [SearchEntityType.Activity],
})
```

---

## Entity Types

| Type | Description |
|------|-------------|
| `SearchEntityType.Company` | Companies with CR numbers |
| `SearchEntityType.Contact` | Company contacts |
| `SearchEntityType.Opportunity` | Pipeline opportunities |
| `SearchEntityType.Activity` | Activities and timeline events |
| `SearchEntityType.Document` | RAG-indexed documents |

---

## Search Options

```typescript
interface SearchQuery {
  q: string                          // Search query (Arabic or English)
  types?: SearchEntityType[]         // Entity types to search
  filters?: SearchFilter[]           // Field-level filters
  sort?: SearchSort                  // Sort configuration
  limit?: number                     // Max results (default: 20)
  offset?: number                    // Pagination offset
}
```

---

## Search SDK in Widgets

```typescript
import { useSearch } from '@salesos/search'

function CompanySearch() {
  const { results, loading, search } = useSearch()

  return (
    <div>
      <input onChange={e => search(e.target.value)} />
      {loading && <Skeleton />}
      {results?.items.map(company => (
        <CompanyCard key={company.id} company={company} />
      ))}
    </div>
  )
}
```

---

## Related

| Resource | Link |
|----------|------|
| Platform SDK | [Platform SDK](platform-sdk.md) |
