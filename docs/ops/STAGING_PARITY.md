# Staging-Parity Gaps

> **Status:** VERIFICATION IN PROGRESS (A-09 partially addressed 2026-08-08)
> **Audit source:** `docs/audit/ga-engineering-audit/`
> **Last updated:** 2026-08-08 (env parity + DEBUG fix applied; operator verification pending)

## Summary

The staging environment (`.env.staging.example`, 92 lines) is significantly smaller than the
production environment (`.env.production`, 174 lines). The gaps listed below must be closed
before staging can serve as a reliable pre-production gate.

---

## Environment Variable Gaps (Staging Missing)

| Category | Variable(s) | Impact if Missing |
|----------|-------------|-------------------|
| **SMTP / Email** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Cannot verify email delivery (password reset, invites, notifications) before prod |
| **SSO / OIDC** | `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_ISSUER`, `OIDC_REDIRECT_URI` | Cannot test SSO login flow before prod |
| **Error Tracking** | `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE` | No error aggregation or performance tracing in staging |
| **Rate Limiting** | `RATE_LIMIT_WINDOW`, `RATE_LIMIT_MAX_REQUESTS`, `RATE_LIMIT_BURST` | Rate-limiting behaviour untested; can only validate in production |
| **CORS Origins** | `CORS_ORIGINS` (full list of allowed frontend domains) | Cross-origin misconfiguration only caught after prod deploy |
| **Celery / Task Queue** | `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Async task pipelines (data ingestion, enrichment, exports) not exercised in staging |
| **Audit Retention** | `AUDIT_RETENTION_DAYS`, `AUDIT_LOG_LEVEL` | Audit log pruning and storage sizing not validated |

---

## Feature Flag Gaps

Staging has more feature flags enabled than production, which means staging tests
features that will be turned **off** after deployment. This is a false-positive risk.

| Flag | Staging | Production | Risk |
|------|---------|------------|------|
| `FEATURE_SEARCH` | `true` | `false` | Search path not tested in prod config |
| `FEATURE_GRAPH` | `true` | `false` | Knowledge Graph not tested in prod config |
| `FEATURE_ENTITY` | `true` | `false` | Entity resolution not tested in prod config |
| `FEATURE_DECISION` | `true` | `false` | Decision engine not tested in prod config |
| `FEATURE_AI_COPILOT` | `true` | `false` | AI copilot not tested in prod config |

**Recommendation:** Either enable all flags in production or align staging to match
production's conservative flag set. Testing with flags that differ from prod creates
a staging environment that does not represent the production configuration.

---

## Infrastructure Gaps

| Gap | Detail | Status |
|-----|--------|--------|
| **Kafka version** | Dev `7.0.0` vs prod `7.7.2` | Fixed in separate task |
| **Node count** | Staging: single-node docker-compose; Prod: multi-node K8s | Architectural limitation (acceptable) |
| **SSL termination** | Staging: none / self-signed; Prod: managed TLS via ingress | Acceptable if smoke tests account for it |
| **Database replicas** | Staging: single PostgreSQL; Prod: primary + read-replica | Cannot test read/write split behaviour |

---

## Remediation Plan

1. **Create `.env.staging.example` with 174-line parity** — mirror every production env
   var with staging-appropriate values (mailpit instead of SMTP, Vault dev mode, etc.).
2. **Align feature flags** — set staging flags to match production (all `false`) or
   create a dedicated "full-feature-test" config that runs weekly.
3. **Add staging CI smoke test** that verifies every env var from production is present
   and has a non-default value.
4. **Kafka version upgrade** — tracked separately in W11 infrastructure task.

---

## Validation Status (2026-08-08 refresh)

| Check | Before | After | Evidence |
|-------|:------:|:-----:|----------|
| `.env.staging` parity | 58 lines | **~135 lines** | SMTP, SSO, Sentry, RateLimit, Celery, CORS, Audit, Feature flags, Stripe, Google, Meili sections added |
| `.env.staging.example` parity | 106 lines | **~170 lines** | All prod env categories mirrored |
| CHANGEME passwords | 4/8 | **still 4/8** | Waiting on operator to generate real tokens |
| `SALESOS_DEBUG` | `true` | **`false`** | `docker-compose.staging.yml` line 219 fixed |
| Feature flags match prod | mismatched | **aligned** | All flags set to `false` in `.env.staging` |
| SMTP config present | ❌ | ✅ | Vars in `.env.staging`, needs Mailpit/real SMTP |
| SSO config present | ❌ | ✅ | Vars in `.env.staging`, needs test OAuth app |
| Sentry DSN present | ❌ | ✅ | DSN field present, still empty (optional) |
| Rate limiting vars present | ❌ | ✅ | Defaults set |
| CORS origins present | ❌ | ✅ | Defaults set |
| Celery broker present | ❌ | ✅ | Redis broker configured |
| Audit retention present | ❌ | ✅ | 90-day retention, INFO level |
| Startup smoke test | ❌ | ⏳ | Awaiting `docker compose up` by operator |
| Deploy workflow | ❌ | ✅ | `deploy-staging.yml` exists (manual dispatch) |

**Overall staging-parity status:** ⚠️ Env files now at production parity; CHANGEME passwords + operator startup pending. See [STAGING_VERIFICATION_2026-08-08.md](STAGING_VERIFICATION_2026-08-08.md) for step-by-step verification checklist.
