# 101 — ORM ↔ schema drift check, and both audits as regression tests (2026-09-25)

## Purpose

Decision B9.2 (report 99). Report 98's sweep covers static SQL strings. This
report adds the complementary check for SQLAlchemy ORM models, and turns
both checks into tests, so this class of defect cannot return silently.

## Delivered

| file | purpose |
|---|---|
| `scripts/audit_orm_schema_drift.py` | Imports the app, which registers every model, then collects every in-process `MetaData`. Compares each table and column with `information_schema` of a migrated database: missing tables, missing columns, and type-family mismatches. Read-only. `pg_catalog` / `information_schema` reflection metadata is excluded. |
| `tests/integration/test_schema_contract_db.py` | Runs the SQL sweep (report 98) and the ORM drift check against the database named by `SCHEMA_CONTRACT_DSN`, and **skips when it is unset**, so it can never touch `salesos_test` or a shared DB by accident. Tolerated exceptions are an explicit allowlist, each entry citing its report. |

## Findings on the migrated disposable DB

| measure | value |
|---|---|
| ORM tables checked | 161 (application models; 211 tables exist, the rest are used by raw SQL only) |
| ORM columns checked | 1,644 |
| **Missing columns** | **0** |
| Type-family mismatches | 1, fixed (below) |
| Missing tables | 1, documented (below) |

1. **`runtime/knowledge_graph_runtime/repository/sql_repository.py`** declared
   `companies.capital` as `String`. The column is `double precision`, and the
   canonical model `Company.capital` is `Float`. The table is only ever
   read, never written or filtered on `capital`, so there was no runtime
   effect. **Fixed** to `Float` for correctness.
2. **`event_outbox`** has a table definition in `sdk/events/outbox.py` but no
   migration. It is created on demand with `create_all()` inside
   `KafkaEventBus._publish_outbox`. That path is **dormant**: it needs both
   `kafka_outbox_enabled` and `set_outbox_relay()`, and nothing in the app
   calls `set_outbox_relay`.
   - **Not changed.** If the outbox is ever enabled, it should get a
     migration and an RLS decision rather than `create_all()`, since the
     restricted application role should not need DDL rights.
   - Allowlisted with this justification.

## Verification

- Both tests pass against the disposable DB migrated to head: 2/2.
- **Negative proof:** re-introducing two already-fixed defects in the
  container copy made both tests fail with the exact finding:
  - `er_router` unmerge cast → `uuid = character varying`;
  - `capital` → `orm=string db=double precision`.
  Restored → 2/2 pass.

## Allowlist (must shrink)

The SQL allowlist contains:
- report 98's false positive;
- the `nba_feedback` legacy method, to be removed by decision B4;
- the two `grounding.py` sources, to be replaced by decision B5.

Implementing B4 and B5 must remove those three entries (tracked in the
next report).

## How to run

The test only runs when `SCHEMA_CONTRACT_DSN` points at a disposable
database migrated to head:

```
SCHEMA_CONTRACT_DSN=postgresql://… pytest tests/integration/test_schema_contract_db.py
```

## Deliberate non-claims

- **Not wired into CI.** CI configuration was not changed. Adding a CI job
  that creates a disposable Postgres, runs `alembic upgrade head` and sets
  `SCHEMA_CONTRACT_DSN` is the recommended next step, and needs an owner
  decision about CI runtime.
- **Coverage limits:**
  - ORM relationships, constraints and nullability are not compared.
  - The type check is by family (e.g. varchar vs text are equivalent).
  - f-string SQL is still not covered.
- Only the disposable container was used. Production is **NOT APPROVED**.
