# Company Intelligence Command Center — Component Catalog

## Workspace Components

| Component | Props | Description |
|-----------|-------|-------------|
| `CompanyIntelligencePage` | companyId | Full page entry point |
| `CompanyIntelligenceHeader` | company, onPresetChange | Title, status, preset selector |
| `CompanyIntelligenceGrid` | children, isLoading | 6-column CSS grid |
| `CompanyIntelligenceWidgetShell` | widgetId, children | Error boundary + grid column |

## Widget Components

Each widget has: `*Container.tsx`, `*View.tsx`, `types.ts`, `__tests__/*.test.tsx`, `index.ts`

### 1. CompanyDNA (Reference Widget)
**Purpose**: Summarize 20 dimensions of the company visually.

| Visual Element | Data Source |
|----------------|-------------|
| Industry badge | Firmographic |
| Business model icon | Categorization |
| Company size gauge | Employee count |
| Growth pattern sparkline | Historical data |
| Buying behaviour score | Propensity model |
| Technology profile radar | Tech stack |
| Financial health gauge | Financial data |
| Government exposure meter | Government contracts |
| Expansion potential | Signals + plans |
| Digital presence score | Website + social |
| Hiring trend chart | Job postings |
| Procurement maturity | Procurement data |
| Relationship strength | Graph |
| Buying intent score | Intent model |
| Risk level | Risk assessment |
| Confidence score | Data quality |
| Data freshness | Update timestamps |
| Golden record status | Entity resolution |

### 2. AI Recommendation Engine
| Element | Description |
|---------|-------------|
| Recommended action | Primary CTA |
| Reasoning | Why this action |
| Confidence | Percentage |
| Expected revenue | Dollar amount |
| Expected impact | Qualitative |
| Estimated time | Timeline |
| Alternative actions | Secondary CTAs |
| Business risks | Risk factors |

### 3. Decision Makers
| Element | Description |
|---------|-------------|
| Person card | Name, role, department |
| Influence level | High/Medium/Low |
| Relationship status | Connected/Warm/Cold |
| Contact info | Email, phone |
| Last interaction | Date |
| Department | Organization |

### 4. Relationship Graph
| Element | Description |
|---------|-------------|
| Interactive graph | SVG/Canvas |
| Nodes | People, companies |
| Edges | Relationships |
| Filters | Type, strength |
| Search | Find in graph |

### 5. Smart Timeline
| Element | Description |
|---------|-------------|
| Event cards | Type, date, summary |
| Type filters | Filter by source |
| Infinite scroll | Load more |
| AI highlights | Important events |

### 6. Signals Feed
| Element | Description |
|---------|-------------|
| Signal row | Type, title, severity |
| Severity badge | Low/Medium/High/Critical |
| AI confidence | Percentage |
| Source | Attribution |
| Click action | Drill down |

### 7. Government Intelligence
| Element | Description |
|---------|-------------|
| License cards | Type, status, expiry |
| Tender list | Value, status |
| Compliance status | Compliant/Violation |
| Expiry warnings | Days remaining |

### 8. Document Intelligence
| Element | Description |
|---------|-------------|
| Document card | Title, type, date |
| AI summary | Auto-generated |
| Document timeline | Chronological |
| Confidence score | OCR/Extraction |

### 9. Buying Journey
| Element | Description |
|---------|-------------|
| Stage indicator | Current stage |
| Progress bar | % complete |
| Stage description | What happens here |
| Recommended action | Next step |
| Time in stage | Duration |

### 10. Golden Record Explorer
| Element | Description |
|---------|-------------|
| Entity list | Merged sources |
| Source badges | Which system |
| Confidence score | Match confidence |
| Duplicate warning | Potential dupes |
| Freshness indicator | Last updated |
| Conflict viewer | Field conflicts |
