# Data Lineage Honesty Map — SalesOS

**Date:** 2026-08-06  
**Finding:** EAB-001-P1-LINEAGE-01  
**Validation:** light validated (path inventory / config Grep)  
**Claim:** **No end-to-end GA intelligence pipeline.** Do not market scrapers→search as a governed production lineage.

---

## Pipeline sketch (honest)

```text
packages/scrapers/{balady,najiz,rega,taqeem}/
        │
        ▼  BREAK — no single governed handoff into SalesOS runtime
Notion / identity import trees (`data/` — often gitignored / non-runtime)
        │
        ▼  BREAK — workspace may lack live `data/` + Notion credentials
salesos/backend/.../notion_sync
        │
        ▼  BREAK — not default post-import hop to ER
Entity Resolution (modules/entity_resolution + ADR-025)
        │
        ▼  BREAK — completeness / default wiring open
Knowledge Graph / Neo4j (runtime + ADR-028; SQL fallback paths exist)
        │
        ▼  BREAK — dual search surfaces; not proven E2E from scraper
Search (runtime/search_runtime + app/routers/search — duplicate risk)
```

---

## Hop table

| Hop | Code / path pointer | Status | Honesty note |
|-----|---------------------|--------|--------------|
| Scrapers → Notion / staging store | `packages/scrapers/*` | **BREAK** | Scrapers are adjacent packages; not a SalesOS GA runtime path by default ([AGENTS.md](../../../AGENTS.md)) |
| Notion / files → `notion_sync` | `salesos/backend/app/modules/notion_sync/` | **BREAK / partial** | Module exists; governed continuous sync not claimed GA |
| Sync → Entity Resolution | `modules/entity_resolution/` | **BREAK** | ER not default post-import hop (EAB DTM) |
| ER → Graph | KG runtime / Neo4j in compose | **Partial** | Neo4j in compose; completeness open |
| Graph → Search | search runtime + routers | **BREAK / partial** | Dual search registrations (EAB-001-P1-DUP-02); no E2E GA proof |
| Event bus between hops | `EVENT_BUS_TYPE` | **Degraded default** | Config default **`in_memory`** (`salesos/backend/app/config.py`); Kafka in compose ≠ bus in use |

---

## Event bus

| Setting | Default | Implication |
|---------|---------|-------------|
| `event_bus_type` / `EVENT_BUS_TYPE` | **`in_memory`** | Cross-service async lineage via Kafka is **not** the default GA path |
| Kafka containers in `salesos/docker-compose.yml` | Present (`confluentinc/cp-kafka:7.7.2`) | Infrastructure available; application default still in-memory |

---

## What must not be claimed

- End-to-end “scrapers → Notion → ER → graph → search” as **GA**
- Vision-complete Knowledge / lineage axes without BREAK markers closed
- That `data/` pipelines are the SalesOS production GA path by default

## Related

- [AI_HONESTY.md](./AI_HONESTY.md)
- EAB FINDINGS `EAB-001-P1-LINEAGE-01`
- ADR-025 / ADR-026 / ADR-028 under `salesos/backend/docs/adr/`
