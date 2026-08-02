# Phase 1 — STORY-06-03 Quota enforcement (Stream A)

> **Honesty:** Not Production GO. DEC-085 / auth / CSRF / RBAC untouched. BE-only.  
> No Stripe secrets invented. Usage granularity remains hourly rollup (Sprint-06 debt note).

## Landed

| Piece | Detail |
|-------|--------|
| Pure eval | `quota_enforcement.py` — limits from `Plan.entitlements.quotas` (+ DOM-021 connector cap) |
| Path gates | `quota_gates.py` — seats (invite), ai_tokens, connectors, storage_mb |
| Usage | `UsageMeterService.quota_usage_snapshot` — UTC-month counters + latest gauges |
| Metric | `connectors` SET gauge added beside existing meter keys |
| Middleware | Extends `EntitlementEnforcementMiddleware` after domain allow |
| Responses | `error=quota_exceeded`; seats/connectors/storage **403**; ai_tokens **429** |
| Flag | `Settings.quota_enforcement_enabled` (default **True**, not a secret) |

## Acceptance (light)

| Dimension | Source | Over-quota |
|-----------|--------|------------|
| seats | UsageMeter gauge `seats` | 403 on `POST /api/v1/identity/invite` |
| ai_tokens | Monthly sum `ai_tokens` | 429 on `/api/v1/rag\|ai\|copilot` |
| connectors | Gauge `connectors` vs plan/DOM-021 | 403 on mutating `/api/v1/integrations` |
| storage_mb | Gauge `storage_mb` | 403 on gated commercial paths |

## Non-goals

- STORY-06-04 adversarial matrix → **LANDED** ([PHASE1_STORY_06_04_ENTITLEMENT_BYPASS_SUITE_CRUMB.md](PHASE1_STORY_06_04_ENTITLEMENT_BYPASS_SUITE_CRUMB.md))
- Real-time (sub-hour) metering
- Production GO / Stripe metered push
