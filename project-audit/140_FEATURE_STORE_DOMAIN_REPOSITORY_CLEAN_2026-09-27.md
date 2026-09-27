# 140 — domains/feature_store/postgres_repo.py: fully clean, live and reachable; one plausible bug hypothesis empirically disproven

**Ephemeral, disposable Postgres container only (`sweep-pg14`, `pgvector/pgvector:pg16`, destroyed after use).** No `salesos_test` or production contact.

## 1. Scope — second file in the `domains/*/postgres_repo.py` sweep

Continuing report 139's new pass. `domains/feature_store/postgres_repo.py` (`PostgresFeatureStoreRepository`, `FeatureDefinitionModel`/`FeatureValueModel`) checked against `domains/feature_store/models.py`'s `FeatureDefinition`/`FeatureValue`/`FeatureType`/`EntityType` and `domains/feature_store/service.py`'s `FeatureStoreService`.

Note: this is a distinct, unrelated module from `runtime/feature_store/features.py` (the feature *computers* — `ExpansionScoreComputer`/`RevenueScoreComputer`/etc. — already fixed for real bugs in reports 67, 118, 159). `domains/feature_store/` is a separate generic key-value feature registry/store feeding the ScoringEngine and Decision Platform, confirmed by its own module docstring.

## 2. Field mapping — every method checked, all correct

`save_definition`/`get_definition`/`delete_definition`/`list_definitions` (against `FeatureDefinitionModel`) and `save_value`/`get_value`/`get_values_for_entity`/`batch_save_values`/`delete_value` (against `FeatureValueModel`) all map every field correctly in both directions, including the `feature_type.value`/`entity_type.value` enum-to-string conversions on write and the corresponding `FeatureType(...)`/`EntityType(...)` reconstructions on read. The `str` vs `EntityType` boundary at the abstract `FeatureStoreRepository` interface (`get_value`/`get_values_for_entity`/`delete_value` all declare `entity_type: str`) is honored consistently by every caller in `FeatureStoreService`.

## 3. A plausible bug hypothesis, checked and empirically disproven

`FeatureValue.is_expired` (the property `FeatureStoreService.get_feature`/`get_features`/`get_feature_snapshot` all rely on to purge stale values) computes `(datetime.now(timezone.utc) - self.computed_at).total_seconds()`. `decision_center`'s row-reconstruction helpers (report 139) all defensively guard against `row.<datetime_col>.tzinfo is None` before using a DB-sourced datetime in arithmetic — `PostgresFeatureStoreRepository.get_value()`/`get_values_for_entity()` do **not** have this guard, passing `computed_at=model.computed_at` straight through. If asyncpg/SQLAlchemy ever returned a naive datetime for this `DateTime(timezone=True)` column, `is_expired` would raise `TypeError: can't subtract offset-naive and offset-aware datetimes` on every read of a feature value.

**Checked empirically rather than assumed**, per this session's established discipline of reproducing before attributing: seeded a real `FeatureDefinitionModel`+`FeatureValueModel` row into a fresh, disposable Postgres container via the actual SQLAlchemy/asyncpg stack this codebase uses, re-fetched it in a separate session, and ran the exact `is_expired` arithmetic directly against the fetched row:

```
computed_at: datetime.datetime(2026, 9, 27, 7, 22, 26, 84164, tzinfo=datetime.timezone.utc) tzinfo: UTC
is_expired arithmetic OK, elapsed= 0.10943
```

The round-trip correctly preserves `tzinfo=UTC` — this SQLAlchemy/asyncpg combination returns aware datetimes for `DateTime(timezone=True)` columns bound with an aware Python value, so the hypothesized crash does **not** reproduce. **No bug — the hypothesis is disproven, not fixed.** (`decision_center`'s defensive guards may be addressing a different code path — e.g. a `server_default=func.now()`-populated column, which this file's `computed_at` is not — not investigated further since this file's own behavior is directly confirmed correct.)

## 4. Reachability — genuinely live, unlike report 139's finding

Unlike `decision_center` (report 139, correctly wired but zero downstream consumers), this module IS live and reachable end-to-end:

- `app/boot/startup.py:165-174`'s `_init_feature_store_domain()` constructs `app.state.feature_store_domain_service = FSDomainService(repository=FactoryBoundRepository(PostgresFeatureStoreRepository, async_session))` — same correctly-GUC-pinning wrapper checked in report 139 (`tenant_scoped_session` → `apply_tenant_guc` → auto-commit/rollback).
- `app/boot/routers.py:56,204` mounts `domains.feature_store.router.router` (confirmed via both the import and the actual `include_router(feature_store_domain_router, ...)` call).
- `domains/feature_store/router.py`'s 5 endpoints (`POST /feature-store/register`, `POST /feature-store/set`, `POST /feature-store/batch-set`, `GET /feature-store/{entity_type}/{entity_id}`, `GET /feature-store/{entity_type}/{entity_id}/{feature_key}`) all correctly read `request.app.state.feature_store_domain_service` and call through to the service methods checked above.

A separate `get_feature_store_service` FastAPI dependency factory also exists in `app/dependencies.py:154-161`, confirmed via repo-wide grep to have zero consumers anywhere (dead alternative wiring, distinct from the live router path above) — noted but not acted on, since the module is already proven reachable through the router.

## 5. Scope and safety

- No files changed — no bug found, no fix needed.
- One disposable, ephemeral Postgres container (`sweep-pg14`) used solely to empirically test the datetime-arithmetic hypothesis; destroyed immediately after (`docker rm -f`). No `salesos_test` or production contact.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. `domains/revenue/analytics/postgres_repo.py` remains skipped (already identified as a dead duplicate under DEC-130b, per report 128). Remaining candidates: `domains/workflow/postgres_repo.py`, `domains/timeline/engine/postgres_repo.py`, `domains/notifications/postgres_repo.py`, `domains/employee/postgres_repo.py`.
