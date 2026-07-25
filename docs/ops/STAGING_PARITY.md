# Staging-Parity Gaps

> **Status:** Production no-go (W11.1)  
> **Audit source:** `docs/audit/ga-engineering-audit/`  
> **Last updated:** 2026-07-25

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

## Validation Status

| Check | Status |
|-------|--------|
| `.env.staging.example` parity | ❌ 92 vs 174 lines |
| SMTP config present | ❌ |
| SSO config present | ❌ |
| Sentry DSN present | ❌ |
| Rate limiting vars present | ❌ |
| CORS origins present | ❌ |
| Celery broker present | ❌ |
| Audit retention present | ❌ |
| Feature flags match prod | ❌ |
| Kafka version match | ❌ (separate task) |

**Overall staging-parity status:** ❌ Production no-go — staging is not a reliable
pre-production gate until the gaps above are closed.
