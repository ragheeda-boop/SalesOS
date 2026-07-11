# Company Intelligence Command Center — Architecture

> SalesOS Wave 1 · Phase C
> Last Updated: 2026-07-10

---

## Vision

The Company Intelligence Command Center transforms Company 360 into a true operational intelligence workspace. A sales executive must understand an entire company in under 60 seconds.

This is NOT a profile page. This is NOT a collection of tabs. This is the **Commercial Intelligence Operating System** for one company.

Every section reduces uncertainty. Every widget increases decision quality. Every recommendation leads toward revenue.

---

## Workspace Responsibilities

| Responsibility | Description |
|---------------|-------------|
| Entity identity | Golden record of the company |
| Intelligence | Signals, news, government data, documents |
| Relationships | Decision makers, partners, suppliers, customers |
| AI Decisions | Recommended actions with confidence, revenue, risk |
| Timeline | Chronological intelligence stream |
| Buying Journey | Where they are and what to do next |

---

## Widget Architecture

All widgets follow the Container/View pattern via the Workspace SDK:

```
CompanyDNAWidget = createWidget({
  metadata: { id, title, permissions, featureFlag, ... }
  useData: () => useCompanyIntelligenceContext().widgets.companyDNA
  render: ({ data }) => <CompanyDNAView dna={data} />
})
```

| Widget | Data Source | Refresh | Priority |
|--------|-------------|---------|----------|
| Company DNA | Aggregated | 5min | Critical |
| AI Recommendation Engine | AI Pipeline | On demand | Critical |
| Decision Makers | CRM + Graph | 5min | High |
| Relationship Graph | Neo4j | 5min | High |
| Smart Timeline | All sources | 1min | High |
| Signals Feed | Signals | 1min | High |
| Government Intelligence | Government APIs | 1h | Medium |
| Document Intelligence | Document Store | 5min | Medium |
| Buying Journey | AI Pipeline | On demand | Medium |
| Golden Record | Entity Resolution | 1h | Low |

---

## Data Flow

```
External Sources (CRM, Government APIs, News, Social, Neo4j)
  → Company Intelligence Service (backend)
    → API POST /api/v1/companies/{id}/intelligence
      → CompanyIntelligenceProvider (React)
        → deriveCompanyIntelligenceWidgets(map)
          → WidgetMap
            → Widget (useData from context)
              → Container (createWidget)
                → View (pure component)
```

---

## Caching

| Layer | Cache | TTL | Strategy |
|-------|-------|-----|----------|
| Browser | Widget data | Session | Context |
| React Query | API responses | 30s | Stale-while-revalidate |
| API | Aggregated response | 10s | In-memory |
| Widget SDK | Individual widget | Per config | Status-based |

---

## Permissions

| Permission | Widgets |
|------------|---------|
| `company:dna:read` | Company DNA |
| `company:ai:recommendations` | AI Recommendation Engine |
| `company:decision-makers:read` | Decision Makers |
| `company:graph:read` | Relationship Graph |
| `company:timeline:read` | Smart Timeline |
| `company:signals:read` | Signals Feed |
| `company:government:read` | Government Intelligence |
| `company:documents:read` | Document Intelligence |
| `company:buying-journey:read` | Buying Journey |
| `company:golden-record:read` | Golden Record Explorer |

---

## Performance Budgets

| Operation | Budget |
|-----------|--------|
| Widget render (idle) | <50ms |
| Widget render (data) | <100ms |
| Full workspace load | <500ms |
| AI recommendation | <3s |
| Relationship graph render | <200ms |
| Timeline render | <150ms |

---

## Accessibility Strategy

| Requirement | Implementation |
|------------|---------------|
| Keyboard | Arrow keys, Tab, Enter, Escape per widget |
| Screen readers | ARIA roles, live regions, status announcements |
| Dark mode | `dark:` variants + CSS variables |
| RTL | Arabic-first, `dir="rtl"` throughout |
| Reduced motion | `motion-reduce:transition-none` |
| Focus management | Logical tab order per widget |

---

## Telemetry

| Event | Payload |
|-------|---------|
| `company.dna_view` | companyId, dimensionsLoaded |
| `company.ai_recommendation` | companyId, recommendationId, confidence |
| `company.timeline_scroll` | companyId, eventCount |
| `company.relationship_click` | companyId, targetEntityId, relationshipType |
| `company.signal_click` | companyId, signalId, severity |
| `company.widget_error` | companyId, widgetId, errorMessage |
