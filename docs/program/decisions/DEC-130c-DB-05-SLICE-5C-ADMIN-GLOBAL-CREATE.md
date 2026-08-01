# DEC-130c — DB-05 Slice 5c: additive CREATE for global admin trio

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **7.6 remains OPEN** (clean check **not** met) · Package = **READY FOR REVIEW** (Architecture / Validation: CREATE honesty + evidence only; do **not** CLOSE 7.6)  
> **Date:** 2026-08-01  
> **Board:** Backend Platform / Database (SalesOS / AQLIYA)  
> **Story / risk:** DB-05 / R-20 / Phase 0 Exit Criterion **7.6**  
> **Authority:** DEC-130 Slice 5a plan · DEC-130b Slice 5b · DEC-113 Slice 1 pattern · DEC-085 `set_config` · DEC-107 swarm READY  
> **Out of scope this land:** DROP · ENABLE RLS · index/type/null batches (5d) · companies residual columns (5e) · orphan KEEP DROPs (5f+) · production / Railway migrate · Prisma · DEC-085 edits · Production GO / CI GREEN · Criterion VERIFIED/CLOSED

---

## 1. Decision

Ship **Slice 5c** = additive Alembic **CREATE TABLE** for the three global admin tables that ORM already declares but Postgres lacked (`add_table`×3 residual from DEC-130 / DEC-130b). **No RLS** (no `tenant_id`). **No DROP.** Criterion **7.6 stays OPEN**.

| Pin | Value |
|---|---|
| Alembic head (local compose) | **`e2b9d46f8a10`** (down **`d1a8c35e7f09`**) |
| `alembic check` | **FAILED** (exit **255**) — expected (residual noise remains) |
| `Detected added table` | **3 → 0** (admin trio cleared) |
| Tables | `admin_plans`, `admin_feature_flags`, `admin_health_snapshots` |
| DEC-085 | **Intact** (not touched) |
| Criterion 7.6 | **OPEN** — phased residual (next **5d**) |

### Alternatives considered

| Option | Result |
|---|---|
| (a) Metadata-only / skip CREATE | **Rejected** — live DB had **0** of 3 tables; ORM↔DB CREATE gap is real |
| (b) ENABLE RLS on the trio | **Rejected** — global / platform tables; DEC-130 plan says no RLS |
| (c) Additive idempotent CREATE matching ORM | **Approved** |

---

## 2. Scope

### ORM sources (`app/modules/admin/db_models.py`)

| Table | Model |
|---|---|
| `admin_plans` | `PlanModel` |
| `admin_feature_flags` | `FeatureFlagModel` (includes `rollout_percentage`, `is_ci_test` from Phase 16) |
| `admin_health_snapshots` | `HealthSnapshotModel` + index `ix_admin_health_ts` |

### Migration

- Revision: `e2b9d46f8a10_db05_slice5c_create_admin_global_trio.py`
- Pattern: same idempotent `_table_exists` guard as DEC-113 Slice 1 (`a7c3e91f0b05`)
- Downgrade: DROP the three tables only (local/compose; not production this land)

### Live truth (pre-upgrade)

```text
SELECT tablename FROM pg_tables WHERE … IN (admin_plans, admin_feature_flags, admin_health_snapshots)
→ 0 rows
```

---

## 3. Live evidence (Docker compose, 2026-08-01)

```text
docker compose exec -T backend alembic upgrade head   → e2b9d46f8a10
docker compose exec -T backend alembic current        → e2b9d46f8a10 (head)
docker compose exec -T backend alembic check          → FAILED exit 255
```

| Class | Before (5b) | After (5c) | Notes |
|---|---:|---:|---|
| `Detected added table` | **3** | **0** | admin trio CREATE landed |
| `Detected removed table` | **15** | **15** | orphan KEEP residual (5f+) |
| Index / type / null noise | present | present | Slice **5d** |
| Companies KEEP-adjacent columns | present | present | Slice **5e** |
| DEC-085 `set_config` | intact | intact | untouched |

---

## 4. Validation

| Check | Result |
|---|---|
| Docker `alembic current` / `heads` | `e2b9d46f8a10` |
| Docker `alembic check` | **FAILED** (exit 255) — expected |
| `add_table` delta | **3 → 0** |
| Production / Railway migrate | **Not run** |
| DEC-085 | Untouched |
| Label | **light validated** (Docker upgrade + alembic check counts) |

**Production GO not claimed. CI GREEN not met. Criterion 7.6 not CLOSED.**

---

## 5. Records

- Phase 0 criterion **7.6** → **OPEN** (phased; Slice 5c COMPLETE / READY FOR REVIEW)
- Board DB-05 → Slice 5c COMPLETE; residual = 7.6 clean check (5d+)
- `DECISION_LOG.md` DEC-130c
- R-20 next-action → Slice **5d** index / type / nullable batches
- **Not claimed:** Production GO · CI GREEN · `alembic check` clean · 7.6 VERIFIED/CLOSED

---

## 6. Architecture next?

Architecture Reviewer: confirm (1) additive CREATE for the three global admin tables matches ORM and live absence, (2) no RLS is correct (no `tenant_id`), (3) down-revision pin `d1a8c35e7f09` → `e2b9d46f8a10` is sound, (4) Slice **5d** index/type/nullable is the correct next Backend land. Validation: corroborate `add_table` **3→0** + head pin + FAILED check — do **not** treat as 7.6 close evidence.
