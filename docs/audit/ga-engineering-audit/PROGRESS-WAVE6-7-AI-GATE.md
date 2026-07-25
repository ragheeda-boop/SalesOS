# Progress — Wave 6–7 AI marketing / honesty gate

**Date:** 2026-07-22  
**Agent scope:** Close AI marketing/honesty blocker as far as code/docs allow  
**Commit:** Not requested — **not committed**  
**Production GO / AI GA:** **Not claimed** (audit remains **production no-go**)

---

## Goal

Stop GA-facing UI/API from presenting copilot / Decision stubs as production AI while `feature_ai_copilot=False`.

---

## What was gated / relabeled

| Surface | Change | Evidence |
|---------|--------|----------|
| Copilot product API | `require_ai_copilot_enabled` → **403** on query / search-companies / feedback when flag False | `salesos/backend/app/routers/copilot.py` |
| Copilot status | `GET /api/v1/copilot/status` → `{ feature_ai_copilot, classification, ga_ready: false }` | same file |
| Dashboard nav | `/copilot` hidden unless flag (or `NEXT_PUBLIC_FEATURE_AI_COPILOT=true`) | `layout.tsx` + `useAiCopilotEnabled` |
| Header Bot + panel | Not rendered when disabled | `layout.tsx` |
| `/copilot` page | Disabled empty state **or** Preview badge when enabled | `copilot/page.tsx` |
| `/ai` page | Preview badge + honesty hint | `ai/page.tsx` |
| DecisionProvider | Calls `/api/v1/decision/*` instead of FE stub `decisionEngine` | `DecisionProvider.tsx` |
| i18n | Softened copilot subtitle; added `ai.experimental_badge` / `copilot.disabled_ga` | `en.json` / `ar.json` |
| Docs | This note + `AI_HONESTY.md` + `GA_STATUS.md` blocker line | audit folder |

**Unchanged (intentionally):** Auth / CSRF / RBAC / tenant isolation. Decision Center `/decisions` remains (HTTP API — not the stub package).

---

## Remaining human / product decisions

1. **CTO/Product PRC sentence** — “SalesOS GA only; AI not marketed as GA” — still **unsigned** (PROD-W6-003).  
2. Whether `/ai` and `/rag` stay in GA nav long-term vs admin-only (currently labeled Preview / experimental).  
3. When (if ever) to set `feature_ai_copilot=True` in staging/prod after soak + evidence.  
4. Whether launch notes / sales decks still contain “AI-native” language outside this repo (marketing ops).  
5. Full browser / e2e re-smoke of gated `/copilot` — **not run** this pass (low-load).

---

## Files touched

### Created
- `salesos/frontend/src/lib/hooks/useAiCopilotEnabled.ts`
- `salesos/frontend/src/components/ai/ExperimentalAiBadge.tsx`
- `docs/audit/ga-engineering-audit/PROGRESS-WAVE6-7-AI-GATE.md` (this file)

### Updated
- `salesos/backend/app/routers/copilot.py`
- `salesos/frontend/src/app/(dashboard)/layout.tsx`
- `salesos/frontend/src/app/(dashboard)/copilot/page.tsx`
- `salesos/frontend/src/app/(dashboard)/ai/page.tsx`
- `salesos/frontend/src/features/revenue-execution/_providers/DecisionProvider.tsx`
- `salesos/frontend/src/features/revenue-execution/_providers/__tests__/DecisionProvider.test.tsx`
- `salesos/frontend/src/lib/i18n/en.json`, `ar.json`
- `docs/audit/ga-engineering-audit/AI_HONESTY.md`
- `docs/audit/ga-engineering-audit/GA_STATUS.md`
- `docs/audit/ga-engineering-audit/README.md` (link)
- `docs/audit/ga-engineering-audit/PROGRESS-WAVE6-7-DOCS.md` (cross-link)

---

## Validation

| Check | Result |
|-------|--------|
| Heavy build / lint / full test suite | **Not run** (low-load; not approved) |
| Spot read of gated router + FE hooks | Yes |
| Browser / Playwright re-smoke | **not validated** |
| Classification | Still **production no-go**; AI marketing blocker **mitigated in code/docs**, human PRC open |

**Validation label:** **light validated** (code/docs review only)
