# 09 — 90-day audit-log export runbook (TEMPLATE / OPS)

> **Status:** Runbook **LANDED** in-repo · live export sample from published env = **ops / residual-external** (OPS-1).  
> **Story:** STORY-14-05 · links [`01-audit-logging.md`](./01-audit-logging.md).  
> **Honesty:** Config default 90d ≠ proven retention · Not Type I certified · Not Production GO.

## Purpose

Produce a **dated export** (or statistical proof) that audit events exist across a ≥90-day window for an in-scope tenant / environment, suitable for auditor sampling.

## Design evidence already in pack

| Element | Pointer | Label |
|---------|---------|-------|
| Retention setting | `salesos/backend/app/config.py` → `audit_retention_days: int = 90` | Design |
| Middleware / service / API | [`01-audit-logging.md`](./01-audit-logging.md) | Design / light |
| Query API | `GET /api/v1/audit/logs` (`salesos/backend/app/modules/audit/router.py`) | Design |
| Stats API | `GET /api/v1/audit/stats?days=` (max 365) | Design |

## Prerequisites

- Operator with tenant-scoped auth for the **published** (or auditor-agreed) environment.  
- CSRF / session rules respected for browser clients; automation uses approved token path.  
- Do **not** weaken auth, CSRF, RBAC, or tenant isolation to obtain the sample.  
- Prefer **aggregate stats + redacted samples**; full dumps stay offline (may contain PII / IPs).

## Procedure

### A. Confirm retention config (design check)

1. Verify deployed settings expose `audit_retention_days = 90` (or ≥90) for the target env.  
2. Record config source (env / Railway / compose) and capture date — offline.

### B. Stats probe (≥90d window)

1. Authenticate as in-scope tenant admin / platform operator.  
2. Call:

   ```http
   GET /api/v1/audit/stats?days=90
   Authorization: Bearer <token>
   ```

3. Record HTTP status, `days` requested, and returned totals / breakdowns.  
4. If totals are zero on a mature env, escalate — may indicate retention purge, empty tenant, or logging gap (**do not invent success**).

### C. Bounded log export (sample)

1. Choose `date_from` / `date_to` spanning ≥90 days (ISO-8601).  
2. Page through:

   ```http
   GET /api/v1/audit/logs?date_from=<ISO>&date_to=<ISO>&page=1&size=200
   Authorization: Bearer <token>
   ```

3. Stop after auditor-agreed sample size **or** full offline archive to secured storage.  
4. Redact `ip_address` / `user_agent` / free-text `details` before any in-repo citation.  
5. Store checksum + row count + min/max `created_at` with the offline packet.

### D. Completeness notes (honest)

| Check | Result |
|-------|--------|
| Mutating methods audited (`POST`/`PUT`/`PATCH`/`DELETE`) | ☐ observed in sample |
| `403` responses audited | ☐ observed / ☐ none in window |
| Excluded paths (`/health`, `/metrics`, `/docs`, …) | ☐ confirmed absent (expected) |
| Reads intentionally not fully logged | ☐ acknowledged (do not overclaim) |
| SIEM / WORM ship | ☐ N/A — still **gap** per `04-gap-inventory.md` OPS-2 |

## Evidence packet fields (fill offline)

| Field | Value |
|-------|-------|
| Environment | ☐ published · ☐ staging · ☐ other: ________ |
| Tenant ID (redact in git) | |
| Export start / end (UTC) | |
| Stats response summary | |
| Row count exported | |
| Min / max `created_at` | |
| Artifact path + checksum | |
| Operator | |
| Date captured | |

## Attestation (signatures — residual until executed)

| Role | Name | Signature | Date (ISO) |
|------|------|-----------|------------|
| Operator / DevOps | | ☐ UNSIGNED | |
| Security | | ☐ UNSIGNED | |
| Program Director | | ☐ UNSIGNED | |

## Explicit non-claims

- This runbook alone does **not** prove 90-day retention on production.  
- Until a dated export exists offline, OPS-1 stays **not validated**.  
- Do **not** claim “SOC2 Type I certified” or Production GO from a dry-run.
