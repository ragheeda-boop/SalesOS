# 01 — Audit logging evidence (STORY-14-05)

> **Intent:** Index controls + tip/CI pointers for “audit logging completeness.”  
> **Label:** **light validated** (code/docs pointers exist) · live retention drill / export sample = **not validated** / may be **residual-external** ops.  
> **Not:** Type I auditor opinion.

## Control summary

| Element | In-repo reality | Evidence class |
|---------|-----------------|----------------|
| Mutating API audit middleware | Present | Design / implementation evidence |
| Audit model + service + router | Present | Design / implementation evidence |
| Configured retention default (90d) | Present in settings | Design evidence (config) |
| Live 90d retention proof on prod | Not claimed here | Gap — ops / residual-external |
| Employee 360 domain audit logger | Present | Design / implementation evidence |

## Code pointers (BE support tip `d0070fa`)

| Hook | Path |
|------|------|
| Request audit middleware | `salesos/backend/app/modules/audit/middleware.py` |
| Wired in stack | `salesos/backend/app/boot/middleware.py` (`AuditMiddleware`) |
| Service / repository | `salesos/backend/app/modules/audit/service.py` |
| Model | `salesos/backend/app/modules/audit/models.py` |
| API surface | `salesos/backend/app/modules/audit/router.py` |
| Unit tests | `salesos/backend/tests/unit/test_audit.py` |
| Retention setting | `salesos/backend/app/config.py` → `audit_retention_days: int = 90` |
| Excluded paths | `settings.audit_excluded_paths` (`/health`, `/metrics`, `/docs`, …) |
| Employee domain audit | `salesos/backend/domains/employee/audit.py` (+ retention tests) |

### Middleware behavior (honest)

`AuditMiddleware` records state-changing `/api/v1/` methods (`POST`/`PUT`/`PATCH`/`DELETE`) and **403** responses. Operator-precedence quirk historically noted in `docs/audit/11-security-architecture.md` (403 always audited). Do not overclaim “every read is logged.”

## Related security controls (supporting, not audit-log itself)

| Control | Path | Note |
|---------|------|------|
| Security headers | `SecurityHeadersMiddleware` in `salesos/backend/app/common/middleware.py` | CSP/HSTS/X-Frame |
| Rate limits | `RateLimitMiddleware` same file | Redis → memory fallback |
| CSRF | `CsrfEnforcementMiddleware` | No API-key skip (Wave 2) |
| Tenant RLS GUC | `salesos/backend/app/database.py` (`set_config('app.tenant_id')`) | DEC-085 |
| AI honesty | `feature_ai_copilot: bool = False` in `app/config.py` | Not a logging control; scope honesty |

## Policy / runbook pointers

| Doc | Path | Role |
|-----|------|------|
| Incident response | `salesos/docs/INCIDENT_RESPONSE_PLAN.md` | IR / logging use in incidents |
| Production runbook | `salesos/docs/production_runbook.md` | Ops |
| Operations manual | `docs/program/OPERATIONS_MANUAL.md` | Program ops |
| AI honesty | `docs/audit/ga-engineering-audit/AI_HONESTY.md` | Scope of AI claims |

## Tip-line / CI corroboration (change + pipeline)

Reuse DevOps pack — do not duplicate URLs as “audit completeness proof”:

- [`PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md`](../../program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md)
- Tip `4754b8b`: CI SUCCESS + Security Scan SUCCESS (pipeline hygiene, not log-content attestation)

## Gaps (see also `04-gap-inventory.md`)

1. **Ops sample:** export of audit rows covering ≥90-day window from the published env — **not validated**.  
2. **Completeness matrix:** which business events are intentional exceptions vs defects — needs Program Director sign-off with Security.  
3. **Immutable / WORM store:** not evidenced as append-only external SIEM — **gap**.
