# Pain Points (evidence-based)

Sources: [PAGE_MAP](../../audit/ga-engineering-audit/PAGE_MAP_SALESOS.md), [FULL-UI-CRAWL](../../audit/ga-engineering-audit/PROGRESS-WAVE13-FULL-UI-CRAWL.md), [DESIGN_STRATEGY](../../vnext/DESIGN_STRATEGY.md), [10-design-audit](../../audit/current-state/10-design-audit.md), [AI_HONESTY](../../audit/ga-engineering-audit/AI_HONESTY.md).

## P0 — Product / trust

| Pain | Evidence | Program response |
|------|----------|------------------|
| Design not Figma-certified; feels weak | PAGE_MAP: not all designed | Design Program v3 (this tree) |
| AI marketed vs stubs | AI_HONESTY | AI Experience + Preview gates |
| Analytics/workflows historically failing | Crawl 500/422/404 | Engines + honest empty/error states |
| Orphan Knowledge/Marketplace | PAGE_MAP orphaned-code | Nav Principles + IA |

## P1 — UX structure

| Pain | Evidence | Response |
|------|----------|----------|
| Flat sidebar sprawl | 25+ NAV_KEYS | L1–L5 nav; domains |
| Duplicate Contacts nav | PAGE_MAP | Deduplicate in shell |
| `nav.nba` without `/nba` | planned-missing | Object + screen |
| Landing `/` stub | implemented-stub | Auth + marketing later phases |
| `no_h1` on 17 routes | Crawl | Shell PageHeader pattern |

## P2 — Visual system

| Pain | Evidence | Response |
|------|----------|----------|
| Login shadcn vs MUHIDE token mismatch | DESIGN_STRATEGY | DS V3 foundations |
| Muted text contrast ~2.9:1 | Design audit | A11y doc + token fix |
| Chart blue vs brand orange | Design audit | Chart tokens in DS |
| Inconsistent density | UX audit | Data Grid + spacing scale |

## P3 — Ops / local

| Pain | Evidence | Response |
|------|----------|----------|
| CORS localhost vs 127.0.0.1 | Crawl | FE guidelines |
| Virtual staging auth compound failures | Wave12 virtual | Multi-workspace + env docs |
