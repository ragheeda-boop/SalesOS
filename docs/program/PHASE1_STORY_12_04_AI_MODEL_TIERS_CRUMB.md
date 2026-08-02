# STORY-12-04 — Per-plan AI model tier (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False** (AI honesty).

## Landed

| Piece | Detail |
|-------|--------|
| Entitlements | `PlanEntitlements.ai_model_tier` `{default, allowed}` — extends 06-01 shape |
| Tier defaults | Starter=`economy` only; Growth=`standard` ceiling; Enterprise=`full` access |
| Catalog | economy→gpt-4o-mini · standard→haiku · full→gpt-4o (declarative) |
| Resolver | Legacy JSONB missing `ai_model_tier` backfills from plan tier |
| HTTP | `GET /api/v1/studio/ai-model-tiers` (+ `/catalog`, `/defaults`) |
| Tests | Starter vs Enterprise ceiling; legacy fill; copilot flag false |

## Document shape (additive)

```json
{
  "version": 1,
  "quotas": { "ai_tokens_monthly": 10000 },
  "ai_model_tier": {
    "default": "economy",
    "allowed": ["economy"]
  }
}
```

## Non-goals

- Enabling `feature_ai_copilot` / live LLM product paths
- AI-Lead Prompt Library / Policies / Memory (12-01..12-03)
- Studio Postgres / `for_each` / STORY-10-05 reopen
- Production GO / Partner Beta / R-02 invent
