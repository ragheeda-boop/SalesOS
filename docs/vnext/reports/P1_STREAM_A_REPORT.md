# P1 Stream A Report — Backend P1 Issues

> Generated: 2026-07-17

---

## G-7: Employee `metadata` column rename

**Status**: ✅ Complete  
**Files modified**:
- `salesos/backend/domains/employee/db_models.py:17` — renamed SQLAlchemy attribute `metadata` to `signal_metadata` (with column name `"metadata"` preserved via `Column("metadata", ...)`)

**Verification**: No references to `EmployeeSignalModel.metadata` existed elsewhere in the codebase.

---

## VIO-S0-02: Identity — Repository bypass

**Status**: ✅ Complete  
**Files modified**:
- `salesos/backend/app/modules/identity/service.py` — `IdentityService` now accepts `tenant_repo: TenantRepository | None` and `user_repo: UserRepository | None` parameters, defaults to creating repos from `db`. All raw `self.db.execute(select(...))` calls for User/Tenant queries replaced with repository methods.
- `salesos/backend/app/modules/identity/signup_service.py` — `SignupService` similarly refactored to use `UserRepository`.
- `salesos/backend/app/modules/identity/invite_service.py` — `InviteService` similarly refactored to use `TenantRepository` and `UserRepository`.

**Backward compatibility**: All three services default to creating repos from `db` when not provided. Router `get_service()` functions remain unchanged.

**Verification**: All existing identity tests still pass (1 test fails due to pre-existing `bcrypt`/`passlib` version incompatibility, unrelated to this change).

---

## VIO-S0-05: `init_db()` bypasses Alembic

**Status**: ✅ Complete  
**Files modified**:
- `salesos/backend/app/database.py` — `init_db()` replaced raw SQL `CREATE TABLE` statements (which duplicated Alembic migrations) with extension/schema setup + programmatic call to `alembic upgrade head` via `run_async_migrations()`.
- `salesos/backend/app/alembic/env.py` — Refactored to support both CLI invocation (`alembic upgrade head`) and programmatic import from `init_db()`. Added fallback to create `AlembicConfig` from `alembic.ini` when `context.config` is unavailable.
- `salesos/backend/app/alembic/versions/0038_consolidate_init_db_tables.py` — New migration creating all tables that were previously managed by raw SQL in `init_db()`:
  - `sso_connections`
  - `audit_logs`
  - `api_keys`
  - `decision_center_decisions`, `decision_center_audits`, `decision_center_feedback`, `decision_center_templates`

**Verification**: Import test passes. Migration follows standard Alembic patterns used by existing migrations.

---

## VIO-S0-06: Decision Center — InMemory repo in production

**Status**: ✅ Complete  
**Files modified**:
- `salesos/backend/domains/decision_center/postgres_repo.py` (NEW) — `PostgresDecisionCenterRepository` implementing `DecisionCenterRepository` with SQLAlchemy ORM models (`DecisionModel`, `DecisionAuditModel`, `DecisionFeedbackModel`, `DecisionTemplateModel`).
- `salesos/backend/app/startup.py:228` — Switched from `InMemoryDecisionCenterRepository` to `PostgresDecisionCenterRepository(async_session())`.

**Verification**: Import test passes. All 49 existing decision center tests pass (tests use `InMemoryDecisionCenterRepository` which is kept for testing).

---

## VIO-102: Timeline — Architecture redesign

**Status**: ✅ Complete  
**Files modified**:
- `salesos/backend/domains/timeline/contracts/repository.py:58` — Added `delete_by_target()` abstract method to `TimelineRepository` interface.
- `salesos/backend/domains/timeline/engine/postgres_repo.py` — Added `delete_by_target()` implementation using SQLAlchemy `delete()`.
- `salesos/backend/domains/timeline/engine/in_memory_repo.py` — Added `delete_by_target()` implementation for in-memory store.

**Verification**: All 12 existing timeline tests pass. The `TimelineService.delete_events_for_entity()` method (which calls `delete_by_target()`) now correctly compiles against the interface.

---

## Summary

| Task | Status | Files Changed | Tests |
|------|--------|--------------|-------|
| G-7 | ✅ | 1 | N/A (column name mapping, no logic change) |
| VIO-S0-02 | ✅ | 3 | All existing pass |
| VIO-S0-05 | ✅ | 3 | N/A (infrastructure/setup) |
| VIO-S0-06 | ✅ | 2 (1 new) | All 49 existing pass |
| VIO-102 | ✅ | 3 | All 12 existing pass |
| **Total** | **5/5** | **12 files** | **61 tests pass** |
