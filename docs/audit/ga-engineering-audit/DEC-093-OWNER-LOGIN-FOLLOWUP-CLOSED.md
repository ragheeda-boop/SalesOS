# Progress — DEC-093 Owner login mint follow-up CLOSED

**Date:** 2026-08-06  
**Product:** SalesOS  
**Related:** [DEC-093](../../program/decisions/DEC-093-JWT-AUDIENCE-CONSUMPTION-CLOSED.md)  
**Production GA:** **NO-GO** (unchanged)  
**Commit:** none (this session)

---

## Verdict

DEC-093 **consumption** was already CLOSED. The open **Owner login / mint** follow-up is now **DONE** at the minimal safe path:

| Layer | What landed |
|-------|-------------|
| BE | `POST /api/v1/identity/owner/login` — password auth → active `admin` → owner-audience JWT mint + `owner_login` audit |
| FE | `/admin/login` + Owner Console gate link; middleware public; CSRF exempt |
| Docs | DEC-093 follow-up section, DECISION_LOG note, OPERATIONS_MANUAL §15, EPIC-07 crumb |

**Validation label:** **light validated** (source/route gate unit asserts **17 passed** in Docker; live OpenAPI + bad-creds **401** after backend restart). Live successful admin mint and browser pass **not** claimed.

## Residuals

- Owner refresh token-family rotation (re-login at access expiry)
- Adversarial HTTP TestClient against `/api/v1/admin/tenants` with DB fixtures
- Separate `owner.salesos.io` deploy (not claimed live)

## Honesty

Does not weaken tenant `salesos-api` / CSRF / RBAC. `feature_ai_copilot` untouched. **No Production GO.**
