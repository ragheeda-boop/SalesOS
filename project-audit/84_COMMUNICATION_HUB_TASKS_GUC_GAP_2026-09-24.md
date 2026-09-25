# 84 — Communication Hub Celery tasks: per-account GUC fix, plus a documented (not fixed) cross-tenant RLS gap (2026-09-24)

## Summary

`app/modules/communication_hub/tasks.py` defines `hub_gmail_sync_all`/
`hub_calendar_sync_all` — Celery tasks that enumerate every active Google
account across all tenants and sync each one's email/calendar. Per the
module's own docstring, these are "code-ready but not executed until a
worker service is added (honest degraded)" — no Celery worker is currently
provisioned. Investigating this file (continuing the session-wide sweep
into `app/modules/communication_hub/*.py`) found two RLS-related gaps of
different severity and scope.

### Fixed: missing per-account GUC pin

Each task opens a fresh session per account
(`async with async_session() as db:`) and passes it directly to
`GmailSyncService`/`CalendarSyncService`, whose `sync()` immediately calls
`GoogleAccountRepository.get_by_user()`. `google_accounts` has RLS + FORCE
RLS; the session was never pinned to `app.tenant_id`, so `get_by_user()`
would find nothing regardless of how many real, matching accounts exist —
`sync()` would raise `GmailSyncError`/`CalendarSyncError` ("No active
Google account connected") on every real call. Fixed by pinning
`apply_tenant_guc(db, str(account.tenant_id))` before constructing the
sync service for that specific account.

### Documented, NOT fixed: cross-tenant enumeration is itself RLS-blocked

The *earlier* step in both tasks —
`GoogleAccountRepository(db).list_active()`, which enumerates active
accounts across *all* tenants to discover what to sync — runs on the same
restricted, unpinned session. `google_accounts`' RLS policy enforces a
single-tenant view per session; there is no "list across all tenants"
carve-out for the restricted `salesos_app` role. This means
`list_active()` returns **zero rows today, regardless of GUC state**,
making the per-account fix above currently unreachable in practice (the
loop body never executes, because the enumeration that feeds it always
comes back empty).

Fixing this properly requires a session that genuinely bypasses RLS for
this legitimate system-level enumeration — e.g. routing it through
`owner_engine` (already used in this codebase for exactly this class of
admin/bootstrap operation) via a new sessionmaker, or an equivalent
mechanism. That is an infrastructure/architecture decision (which
connection a background job should use to read across tenants, and how
that's kept separate from tenant-facing request traffic), not a narrow
bug fix — matching this session's established practice (reports 59/60/104)
of documenting a finding that needs a deliberate decision rather than
unilaterally adding new shared-connection infrastructure. **Not
implemented in this session.**

## Fix

**`app/modules/communication_hub/tasks.py`**:
- `_hub_gmail_sync_all()` and `_hub_calendar_sync_all()`: added
  `await apply_tenant_guc(db, str(account.tenant_id))` immediately after
  opening each per-account session, before constructing
  `GmailSyncService`/`CalendarSyncService`. Added inline comments pointing
  to this report for the separate, unfixed `list_active()` gap.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**: `tests/integration/test_communication_hub_tasks_guc_db.py`
(1 test): reproduces the exact first call `sync()` makes
(`GoogleAccountRepository.get_by_user()`) on both an unpinned session
(matches the pre-fix behavior — asserts the account is genuinely
invisible) and a session pinned via `apply_tenant_guc()` for that
account's specific tenant (matches the fixed behavior — asserts the
account is found). Full end-to-end exercise of `GmailSyncService.sync()`
itself was not attempted: it also requires live OAuth tokens and an
external Gmail API call, out of scope for this fix's verification.

**Combined session regression** (all integration tests from reports
68/70–84 run together in the same container): **51/51 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

These Celery tasks are explicitly disclosed as not currently executed in
production (no worker provisioned) — this fix closes a bug that would
otherwise surface the moment a worker is added, without changing any
currently reachable behavior; the remaining `list_active()` gap means the
full feature would still not work end-to-end until that separate decision
is made. No production or `salesos_test` write; only a disposable,
ephemeral Postgres container was used, destroyed after verification.
Phase 7 remains BLOCKED; production remains **NOT APPROVED**.
