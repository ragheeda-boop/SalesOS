# STORY-11-07 — Website Intelligence (AI-Lead / CAP-101)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> CI uses `FixtureWebsiteAnalyzer` + governed prompt-registry key `gtm.website_intelligence.v1`.  
> Live crawl / live LLM / Claygent-Clay per-row vendor / RAG GO — **not claimed**.  
> `feature_ai_copilot` default remains **False**. FE Decision package remains **STUB**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `WebsiteIntelligenceSnapshot` / `WebsiteSignal` (OBJ-355) |
| Prompt path | Governed CAP-023-shaped key `gtm.website_intelligence.v1` (platform LLM spend path) |
| Analyzer | `FixtureWebsiteAnalyzer` catalog + hostname/snippet derive |
| HTTP | `POST/GET /api/v1/gtm/website-intelligence` + `/meta` + `/{id}` |
| Tests | Catalog hit, derive path, governed-prompt guard, tenant isolation, flag False |

## Acceptance

Reuses existing LLM spend path (Prompt Registry-shaped) — no separate per-row vendor tool — covered in CI via fixture.

## Unblocks

- **FE-S11-07** Website Intelligence UI under `/gtm/website-intelligence`

## Non-goals

- Live website crawl / scraping network
- Live OpenAI/Claude inference or enabling `feature_ai_copilot`
- Claygent / Clay vendor integration
- RAG GO / Production GO
- STORY-11-08 AI Outreach (next)
