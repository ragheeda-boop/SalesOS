---
EngineeringOS: v3
GeneratedAt: 2026-08-01T12:11:50Z
RepositoryCommit: c89025a
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Heuristic
Revalidation: Pending
---

# 15 â€” SECURITY MAP

> Security posture and evidence. **GA posture: production no-go (Security 48; `security-audit-report-latest.json` 51.6/100, 30 critical failures). Do not weaken without Human approval (AGENTS.md Â§4).**

## 1. Posture

| Metric | Value | Source |
|---|---|---|
| Security score | 48/100 (audit), 51.6/100 (latest report) | ga-engineering-audit / `security-audit-report-latest.json` |
| Critical failures | 30 | security report |
| Production readiness | 38/100 | ga-engineering-audit |
| Classification | **production no-go** | `GA_STATUS.md` |

## 2. Security controls present (as-built)

- **AuthN:** JWT RS256 (identity module, JWKS), refresh rotation. Family rotation: `0012_refresh_token_tables` in migration chain; enabled-state unverified (needs live `alembic current`).
- **AuthZ:** tenant isolation via RLS (55 policies / 47 Category-A tables) + guard dependencies.
- **CSRF:** token endpoint; security headers middleware (`app/boot/security_headers.py`).
- **Secrets hygiene:** `.gitignore` covers `cookies.txt`, `login.json`, `railway-status.json`, `.env*` (root + salesos); identity `_keys/` ðŸ”’.
- **Scanning:** gitleaks blocking in `security-scan.yml` (2026-07-30); SAST.
- **AI honesty:** `feature_ai_copilot=False` default (`app/config.py`); FE decision package = STUB.

## 3. Known critical findings (observe; NOT fixed)

| # | Finding | Location | Sev |
|---|---|---|---|
| 1 | SQL injection | `app/application/admin/data_quality.py` | CRITICAL |
| 2 | SQL injection | `app/modules/revenue_execution/service.py` | CRITICAL |
| 3 | GHCR 403 (CI-08) â€” artifact supply blocked | `ci.yml`/`deploy.yml` | BLOCKER |
| 4 | VPS/SSH deploy secrets missing (CI-09) | deploy workflows | BLOCKER |
| 5 | `deploy.yml` undeclared outputs (`slot`, `image_tag`) | `deploy.yml` | HIGH |
| 6 | e2e CI job has no services (DB/Redis) | `ci.yml` | HIGH |
| 7 | Gitleaks config previously untracked/gitignored | repo | HIGH (verify current) |
| 8 | `server/server.js` permissive CORS (mock) | FE server | MEDIUM |
| 9 | Event bus split-brain | compose vs k8s | MEDIUM |

## 4. Danger paths (never write)

`salesos/backend/.env`, `app/modules/identity/_keys/rsa_private.pem`/`rsa_public.pem`, `salesos/frontend/.env.local`, `salesos/.env`, `.env.production`, `.env.staging.local`, `salesos/infra/monitoring/prometheus-token`, `.env.production.template` (leave unless approved).

## 5. Governance rules (never weaken without approval)

- Do not disable security middleware "to unblock demos".
- Do not commit secrets; do not weaken auth/CSRF/RBAC/tenant isolation/audit logging/evidence gates.
- AI marketing honesty: do not market stubs as production AI.

## 6. When this file changes

- On control change, finding remediation, or posture change. Must be recorded with evidence (AGENTS.md Â§5 labels). Mirror `02`, `18`, `30`.
