# DEC-123 — DB-05 Slice 4: ENABLE RLS on deferred-8 tenant tables

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion 7.5 = **READY FOR REVIEW** (Architecture PENDING · Validation PENDING). Only Execution Orchestrator may mark VERIFIED/CLOSED.  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.5**  
> **Authority:** DEC-110 deferred-8 pin · DEC-113 CREATE · DEC-044 policy template · DEC-085 `set_config` · DEC-107 swarm READY · ARB review protocol (Cursor ≠ CLOSED)  
> **Out of scope this land:** DROP companies dead columns (7.4 STOP) · full `alembic check` (7.6) · production / Railway migrate · Prisma · DEC-085 edits · folding into ALL_TENANT_TABLES (47 intact) · Criterion CLOSED/VERIFIED claims

---

## 1. Decision

Ship **additive** Alembic `d1a8c35e7f09` (down `c9f4a21b6e08`) enabling FORCE RLS + `tenant_isolation_*` on all eight DEC-110 deferred tables.

| Pin | Value |
|---|---|
| Alembic head | **`d1a8c35e7f09`** (single head) |
| Tables | `admin_licenses`, `admin_invoices`, `admin_transactions`, `admin_ai_costs`, `admin_jobs`, `webhook_endpoints`, `scoring_scorecards`, `revenue_analytics_snapshots` |
| Policy template | `generate_policy_sql` (same as Category A) |
| Live `tenant_isolation_%` count | **59 → 67** |
| DEC-085 | **Intact** |
| ALL_TENANT_TABLES | **47 intact** (deferred-8 in `DB05_DEFERRED_8_TENANT_TABLES` only) |

Nullable `tenant_id` (`admin_ai_costs`, `admin_jobs`): fail-closed equality only — **no** `OR IS NULL`.

---

## 2. Validation

| Check | Result |
|---|---|
| Docker `alembic upgrade head` (local compose) | PASS — `c9f4a21b6e08` → `d1a8c35e7f09` |
| Live `pg_policies` count | **67** (`tenant_isolation_%`); all 8 deferred tables present |
| Unit + deferred-8 adversarial + B6/B7 POLICY_COUNT | **15 passed** (narrow Docker pytest) |
| Production / Railway migrate | **Not run** |
| Label | **build validated** (narrow Docker pytest + local upgrade) |

**Production GO not claimed. CI GREEN not met. R-14 GO not claimed.**

---

## 3. Records

- Phase 0 criterion **7.5** → **READY FOR REVIEW** (Cursor COMPLETE). Assigned next: Claude Code (architecture only).
- DB-05 residual = 7.4 companies DEC · 7.6 `alembic check`
- `DECISION_LOG.md` DEC-123
- **Not claimed:** Criterion CLOSED · VERIFIED · Production GO · CI GREEN · Railway migrate

---

## 4. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | Migration log | Docker `alembic upgrade head`: `c9f4a21b6e08` → `d1a8c35e7f09` |
| EV-002 | pytest output | 15 passed (Slice 4 + B6/B7); 25 passed (core RLS POLICY_COUNT) |
| EV-003 | Policy count | `pg_policies` `tenant_isolation_%` = **67**; all 8 deferred tables listed |
| EV-004 | Alembic head | `d1a8c35e7f09` |
| EV-005 | Screenshots | N/A (backend DDL/tests) |
| EV-006 | CI artifacts | Not yet — local Docker only; CI field run PENDING (OpenCode) |

---

## 5. Rollback

| Step | Action |
|------|--------|
| 1 | `alembic downgrade c9f4a21b6e08` (drops 8 policies; DISABLE/NO FORCE RLS) |
| 2 | Restore POLICY_COUNT expectation **59** in adversarial suites |
| 3 | Revert land commit(s) containing `d1a8c35e7f09` + test/POLICY_COUNT edits |
| Expected impact | Deferred-8 lose RLS; Category A 47 + B1–B7 12 policies remain; no data DROP |

---

## 6. Risk

| Surface | Level | Note |
|---------|-------|------|
| Database | HIGH | RLS FORCE on 8 tables; wrong GUC → zero rows / write denial |
| Application | LOW | Same `set_config` path (DEC-085); no API shape change |
| Runtime | LOW | Local compose only this land; prod/Railway not migrated |