# Phase 1 — BE support for STORY-14-04 / STORY-14-05 (Security)

> **Status:** BE READINESS NOTE (docs tip) — Security owns pentest + SOC2 evidence assembly  
> **Base tip:** near `4754b8b`  
> **Honesty:** Not Production GO. `feature_ai_copilot` remains **False**. Do not weaken auth/CSRF/RBAC/RLS.

---

## 1. Ownership

| Story | Owner | Acceptance | BE role |
|-------|--------|------------|---------|
| **STORY-14-04** External / internal pentest | Security (+ firm) | Zero unresolved **criticals** ([Sprint-24](./SPRINT_PLAN/Sprint-24.md)) | Harden findings; provide evidence hooks; do not run external pentest |
| **STORY-14-05** SOC2 Type I evidence | Security, Program Director | Audit logging / access review / change mgmt evidence assembled ([Sprint-25](./SPRINT_PLAN/Sprint-25.md)) | Point to runtime hooks; Type I audit itself is post-GA |

---

## 2. BE spot-check (tip ~`4754b8b`) — residual harden shipped

Wave 2 Security P0s ([PROGRESS-WAVE2-SEC.md](../audit/ga-engineering-audit/PROGRESS-WAVE2-SEC.md)) remain in code:

| Area | Status | Evidence |
|------|--------|----------|
| Decision Center IDOR | **FIXED** | `get_decision(id, tenant_id)` + `DecisionModel.tenant_id == tenant_id` |
| Webhook SSRF | **FIXED** (staging pentest residual OPEN) | `url_safety.py`; DEC-125 |
| CSRF (no API-key skip) | **FIXED** | `CsrfEnforcementMiddleware` |
| Contact/company get-by-UUID IDOR | **HARDENED** (post-spot-check tip) | App-layer `tenant_id` on get/update/delete; company cache key includes tenant |
| Audit attribution | **HARDENED** | Prefer JWT `tenant_id` over client `x-tenant-id` |
| Webhook InMemory default | **HARDENED** | Refuse outside `SALESOS_TESTING=true` |
| AI copilot | Default **False** | `feature_ai_copilot: bool = False` |

**Residual (Security-owned):** staging SSRF pentest OPEN.

---

## 3. Evidence hooks — pointers for Security

### 3.1 Audit logging (14-05)

| Hook | Path |
|------|------|
| Request audit middleware | `salesos/backend/app/modules/audit/middleware.py` |
| Wired in stack | `salesos/backend/app/boot/middleware.py` (`AuditMiddleware`) |
| Domain audit trail helper | identity `AuditTrail` / module audit services under `salesos/backend/app/modules/audit/` |
| Excluded paths config | `settings.audit_excluded_paths` in `app/config.py` |

### 3.2 Security headers

| Hook | Path |
|------|------|
| CSP / HSTS / X-Frame / nosniff | `SecurityHeadersMiddleware` in `salesos/backend/app/common/middleware.py` |
| Stack order | `app/boot/middleware.py` |

### 3.3 Rate limits

| Hook | Path |
|------|------|
| Per-IP sliding window (Redis → memory fallback) | `RateLimitMiddleware` in `app/common/middleware.py` |
| Tiers | `settings.rate_limit_*` (health / identity / search / auth / anonymous) |
| Health surface | `/health` / ready checks expose rate_limiter active flag (`app/main.py`) |

### 3.4 Auth / CSRF / tenant isolation

| Hook | Path |
|------|------|
| CSRF enforcement | `CsrfEnforcementMiddleware` |
| JWT + tenant ContextVar | `TenantContextMiddleware` + `get_current_tenant_id` |
| RLS GUC | `get_db()` → `set_config('app.tenant_id', …)` |
| Suspended-tenant write guard | `SuspendedTenantWriteGuardMiddleware` |
| Entitlement / quota | `EntitlementEnforcementMiddleware` |

### 3.4.1 FE-SEC-02 / FE-SEC-03 cookie + logout contract (BE)

| Surface | Contract |
|---------|----------|
| Refresh cookie | `refresh_token` · HttpOnly · Secure · SameSite=Strict · Path=`/api/v1/identity` — set on login/register/refresh; cleared on logout/logout-all |
| Access cookie (opt-in) | `salesos_access` · HttpOnly · Secure · SameSite=Strict · Path=`/` — set only when `feature_httponly_access_cookie=True` (default **False**); body JWT always retained for Bearer |
| Logout default | `POST /api/v1/identity/logout` — decode refresh (body or cookie); **require** `payload["sub"] ==` authenticated `user_id`; then `blacklist_token` + `revoke_by_refresh_jti` (family compromise + device sessions); clear refresh + access cookies |
| CSRF / RBAC | Unchanged — logout remains Bearer-authenticated + CSRF-enforced |

`feature_ai_copilot` remains **False**. Not Production GO.

### 3.5 Pentest prep pack (Security)

| Artifact | Path |
|----------|------|
| Pack index (STORY-14-04) | `salesos/docs/pentest/README.md` |
| External pentest brief | `salesos/docs/pentest/PENTEST_BRIEF.md` |
| Threat model / test plan | `salesos/docs/pentest/THREAT_MODEL.md`, `INTERNAL_TEST_PLAN.md` |
| Findings tracker | `salesos/docs/pentest/FINDINGS_TRACKER.md` |
| Vendor handoff | `salesos/docs/pentest/VENDOR_HANDOFF_CHECKLIST.md` |
| Results template | `salesos/docs/pentest/PENTEST_RESULTS_TEMPLATE.md` |
| Vendors | `salesos/docs/pentest/PENTEST_VENDORS.md` |
| Disclosure policy | `salesos/docs/pentest/VULNERABILITY_DISCLOSURE_POLICY.md` |
| Evidence dir | `docs/program/evidence/story-14-04/` |
| Story crumb | `docs/program/PHASE1_STORY_14_04_PENTEST_CRUMB.md` (**CLOSED in-repo / IN_REPO_READY**) |
| Staging SSRF runbook | `docs/audit/ga-engineering-audit/runbooks/staging-ssrf-pentest.md` |
| Wave 2 close-out | `docs/audit/ga-engineering-audit/PROGRESS-WAVE2-SEC.md` |

---

## 4. BE standby posture

- Resume on: Board-assigned pentest finding (critical/high) with BE ownership, or Watchdog RED residual we own.
- Will **not** claim: Production GO · zero pentest criticals · SOC2 Type I complete · 2h soak.

## 5. Validation

| Label | Note |
|-------|------|
| **not validated** (this tip) | Docs-only readiness; no new code path exercised |
| Prior Wave 2 | **light validated** (targeted unit tests historically) |
