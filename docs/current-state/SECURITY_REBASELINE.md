# SECURITY REBASELINE — 2026-08-24

**Scope:** Fresh repository-level security assessment  
**Method:** Code-level audit of security-critical files  
**Previous score:** 48/100 (stale, from original audit)  
**New assessment:** Per-domain PASS/FAIL  

---

## Security Dashboard

| Domain | Status | Risk | Key Finding |
|--------|:------:|:----:|-------------|
| Authentication | **PASS** | LOW | bcrypt, RS256-only, brute-force lockout |
| Authorization | **PASS** | LOW | RBAC consistently enforced (100+ routes) |
| Tenant Isolation/RLS | **PASS** | LOW | Fail-closed GUC, 83+ tables covered |
| CSRF | **PASS** | LOW | Double-submit, test-guard, no API-key bypass |
| SSRF | **PASS** | LOW | 5-layer: HTTPS-only, DNS check, IP block, pin transport |
| PII | **PASS** | LOW | Saudi-specific scrubbing, prompt injection guard |
| Secrets | **PASS** | LOW | Env-only, boot-validated, gitleaks |
| API Security | **PASS** | LOW | Identity-aware rate limits, security headers |
| RLS Gaps | **FAIL** | **MED-HIGH** | 3 Phase 3/4 tables missing RLS |
| Dependencies | **PASS** | LOW | Recent, CVE-floored |

**Overall: 9/10 PASS, 1 FAIL (RLS gaps on 3 new tables)**

---

## Detailed Findings

### 1. Authentication — PASS

- **Password hashing:** bcrypt via `passlib[bcrypt]` — `service.py:40`
- **Brute-force lockout:** 5 failures → 15-min lockout — `service.py:703-760`, `models.py:80-81`
- **JWT RS256-only:** `config.py:128-138` — validator rejects non-RS256
- **Owner audience separation:** `owner_auth.py:18-34` — separate `verify_owner_token`
- **Login probe via BYPASSRLS:** `database.py:461-498` — uses `owner_engine` for pre-auth tenant lookup
- **Unknown:** Password complexity enforcement (may rely on frontend only)

### 2. Authorization — PASS

- **RBAC enforcement:** `dependencies.py:104-118` — `require_permission_dep()` used across 100+ routes
- **Role hierarchy:** admin=3 > manager=2 > user=1 > api=1 > auditor=0
- **Owner Platform isolation:** `owner_auth.py:70-77` — separate role on `salesos-owner-platform` audience

### 3. Tenant Isolation/RLS — PASS

- **DEC-085 GUC pinning:** `database.py:90-101` — `set_config('app.tenant_id', ..., true)`, never SET LOCAL
- **Hard guard:** `database.py:257-260` — "HARD STOP — DEC-085 / R-26"
- **Dual engine:** `database.py:52-72` — `engine` (salesos_app, non-superuser) vs `owner_engine` (BYPASSRLS)
- **RLS library:** `app/alembic/lib/rls.py` — fail-closed `current_setting('app.tenant_id', true)`
- **Category A:** 51+ tenant tables with direct `tenant_id` RLS
- **Category B:** 14 parent-FK join tables
- **Deferred-8:** 8 tables added later
- **FORCE ROW LEVEL SECURITY:** Applied to all policies

### 4. CSRF — PASS

- **Double-submit cookie:** `middleware.py:505-594` — `X-CSRF-Token` header vs `csrf_token` cookie
- **State-changing only:** POST/PUT/PATCH/DELETE enforced; GET/HEAD/OPTIONS skip
- **Public paths exempted:** register, login, forgot-password, Stripe webhook
- **Test-only bypass guarded:** `SALESOS_TESTING=true` + ERROR log if ENV=production
- **API key does NOT bypass:** `middleware.py:509-511`

### 5. SSRF — PASS

- **HTTPS-only:** `url_safety.py:84-85`
- **Blocked hostnames:** localhost, metadata endpoints (GCP/Azure/AWS) — `url_safety.py:24-35`
- **DNS resolution check:** `url_safety.py:109-122`
- **Private IP blocking:** `url_safety.py:38-46` — `is_private`, `is_loopback`, `is_link_local`, `is_reserved`, `is_multicast`, `is_unspecified`
- **IP-pinned transport:** `url_safety.py:132-202` — prevents DNS rebinding

### 6. PII — PASS

- **Input sanitization:** `guardrails.py:45-53` — strips special tokens, escape sequences
- **PII scrubbing for RAG:** `guardrails.py:56-100` — `[EMAIL]`, `[PHONE]`, `[NATIONAL_ID]`, `[IBAN]`, `[CARD]`, `[NAME]`
- **Saudi-specific:** phone (+966), national ID/Iqama, IBAN — `guardrails.py:64-70`
- **Prompt injection protection:** `guardrails.py:26-42` — 15 harmful patterns
- **Policy gate at LLM boundary:** `policy_gate.py:39-44` — data classification → max model tier

### 7. Secrets — PASS

- **.env in .gitignore:** `.gitignore:29-31`
- **Secret key validation:** `config.py:31-38` — must be ≥32 chars
- **Production password enforced:** `config.py:106-112` — refuses to boot if empty
- **Gitleaks configured:** `.gitleaks.toml`

### 8. API Security — PASS

- **Rate limiting:** `middleware.py:172-213` — identity-aware, tiered (health=120, identity=10, search=30, auth=100, anon=20)
- **Security headers:** `middleware.py:346-400` — CSP, HSTS, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
- **Body size limit:** 10MB — `middleware.py:14-76`

### 9. RLS Gaps — FAIL

| Table | Migration | Has tenant_id | Has RLS | Risk |
|-------|-----------|:-------------:|:-------:|:----:|
| `approval_requests` | `f6a7b8c9d0e1` | YES | **NO** | MED-HIGH |
| `llm_cost_entries` | `f8b3d4e5f6a7` | YES | **NO** | MEDIUM |
| `tenant_llm_budgets` | `f8b3d4e5f6a7` | YES | **NO** | MEDIUM |

**Impact:** `approval_requests` stores HITL decisions — cross-tenant read possible. `llm_cost_entries`/`tenant_llm_budgets` expose cost data cross-tenant.

### 10. Dependencies — PASS

All dependencies recently pinned with known CVE floors addressed:
- `cryptography >=50.0.0` (CVE-2026-69247 patched)
- `python-multipart >=0.0.27` (DoS patched)
- `strawberry-graphql >=0.315.7` (multiple CVEs patched)

---

## Remediation Required

| Priority | Table | Fix |
|----------|-------|-----|
| **P0** | `approval_requests` | Add RLS migration: `ENABLE ROW LEVEL SECURITY` + `tenant_isolation` policy |
| **P0** | `llm_cost_entries` | Add to `ALL_TENANT_TABLES` in `rls.py` + dedicated migration |
| **P0** | `tenant_llm_budgets` | Same — `tenant_id` is PK but needs RLS for row-level isolation |
| P1 | `password` | Add password complexity validation in `create_user` |

---

## Score Reconciliation

The old score of 48/100 was from the original STAR audit and covered dimensions like deployment, monitoring, and operational readiness — not just code security. The fresh code-level security audit shows 9/10 domains PASS. However, an overall security score should not be assigned until:
1. The 3 RLS gaps are fixed
2. An external pentest is performed
3. Operational security (monitoring, incident response, backup) is re-assessed

**Current recommendation:** Do NOT assign a numeric score. Use per-domain PASS/FAIL until external validation is available.
