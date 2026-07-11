# Company Intelligence Command Center — Blueprint

> Build Order: Documents → Application Layer → Workspace → Reference Widget → 9 Widgets → Tests

---

## 1. Screen Hierarchy

```
CompanyIntelligencePage
  └── CompanyIntelligenceProvider
       ├── CompanyIntelligenceHeader (company name, status, preset selector)
       └── CompanyIntelligenceGrid (6 columns)
            ├── [span 2] CompanyDNAWidget          ← Reference Widget
            ├── [span 4] AIRecommendationWidget     ← Decision Intelligence
            ├── [span 2] DecisionMakersWidget
            ├── [span 4] RelationshipGraphWidget
            ├── [span 6] SmartTimelineWidget
            ├── [span 3] SignalsFeedWidget
            ├── [span 3] GovernmentIntelligenceWidget
            ├── [span 3] DocumentIntelligenceWidget
            ├── [span 2] BuyingJourneyWidget
            └── [span 4] GoldenRecordWidget
```

---

## 2. Route Map

| Route | Component |
|-------|-----------|
| `/companies/{id}/intelligence` | `CompanyIntelligencePage` |
| `/companies/{id}/intelligence?widget={widgetId}` | Scrolled to widget |

---

## 3. Widget Grid Layout

```
┌─────────────────┬──────────────────────────────────────┐
│   Company DNA   │       AI Recommendation Engine        │
│   (span 2)      │       (span 4)                        │
├─────────────────┼──────────────────────────────────────┤
│ Decision Makers │       Relationship Graph              │
│ (span 2)        │       (span 4)                        │
├─────────────────────────────────────────────────────────┤
│                   Smart Timeline (span 6)                │
├─────────────────┬──────────────────────────────────────┤
│  Signals Feed   │     Government Intelligence           │
│  (span 3)       │     (span 3)                          │
├─────────────────┼──────────────────────────────────────┤
│ Document Intel  │     Golden Record Explorer            │
│ (span 3)        │     (span 3)                          │
├─────────────────┴──────────────────────────────────────┤
│ Buying Journey (span 2)   │   (reserved)                │
└────────────────────────────────────────────────────────┘
```

---

## 4. Widget IDs

```typescript
type CompanyWidgetId =
  | 'companyDNA'
  | 'aiRecommendation'
  | 'decisionMakers'
  | 'relationshipGraph'
  | 'smartTimeline'
  | 'signalsFeed'
  | 'governmentIntelligence'
  | 'documentIntelligence'
  | 'buyingJourney'
  | 'goldenRecord'
```

---

## 5. Shared Foundation Components

All widgets reuse:

| Component | Source | Purpose |
|-----------|--------|---------|
| `WorkspaceErrorBoundary` | `@salesos/workspace` | Error catching |
| `WorkspaceGrid` | `@salesos/workspace` | Layout grid |
| `WorkspaceLoading` | `@salesos/workspace` | Loading skeletons |
| `createWidget` | `@salesos/workspace` | Widget factory |
| `createWorkspaceProvider` | `@salesos/workspace` | Provider + context |
| `deriveStatus` | `@salesos/workspace` | Status derivation |
| `describeWidgetContract` | `@salesos/workspace/testing` | Contract tests |
| `createMockWidget` | `@salesos/workspace/testing` | Mock data |

---

## 6. Responsive Behavior

| Breakpoint | Columns | Widget Behavior |
|------------|---------|----------------|
| <768px | 1 | All widgets full width |
| 768-1024px | 2 | Compact layout |
| 1024-1280px | 4 | Standard grid |
| >1280px | 6 | Full grid |

---

## 7. RTL Behavior

- All components use logical CSS properties
- Arabic text throughout
- `dir="rtl"` on workspace container
- Flex row-reverse where needed for icons
