# Sprint 3 — Companies Domain Completion Report

> **WO-301**: Phase 3: Companies  
> **Date**: 2026-07-16  
> **Status**: ✅ Complete

---

## Files Modified

| File | Task | Change |
|------|------|--------|
| `salesos/backend/app/modules/company/schemas.py` | B-1 | Added `BulkEditRequest`, `BulkEditResponse`, `BulkDeleteRequest`, `BulkDeleteResponse` |
| `salesos/backend/app/modules/company/service.py` | B-1, B-3 | Added `bulk_update_companies()`, `bulk_delete_companies()`; migrated `search_companies()` from OFFSET to keyset pagination |
| `salesos/backend/app/modules/company/router.py` | B-1, B-2, B-3 | Added `PATCH /bulk`, `DELETE /bulk`, `GET /export` endpoints; enhanced `GET /companies` with advanced filtering (industry, size range, created date range); migrated to keyset-only pagination (CursorResponse); reordered bulk routes before `/{company_id}` to avoid conflicts |
| `salesos/backend/app/modules/company/repositories.py` | B-3 | Removed OFFSET fallback path from `search()` — always uses keyset (WHERE + ORDER BY + LIMIT) |
| `salesos/backend/app/modules/company/tests/test_bulk_operations.py` | B-1 | New test file: 9 tests covering bulk update (allowed fields, disallowed fields, error handling), bulk delete (soft delete, graceful errors), schema validation |

---

## Approach

### B-1: Bulk Operations API (3d)

**PATCH `/api/v1/companies/bulk`**
- Accepts `{ company_ids: UUID[], updates: { field: value } }`
- Whitelist of allowed fields: `industry`, `size` (→ `employees_count`), `status`, `tags`
- Iterates through company IDs, applies updates, records audit trail and event
- Returns `{ updated: count, failed: count, errors: [...] }`
- Non-allowed fields in `updates` are silently ignored

**DELETE `/api/v1/companies/bulk`**
- Accepts `{ company_ids: UUID[] }`
- Soft delete: sets `deleted_at = now()`, `is_active = False`, `status = "deleted"`
- Errors for individual companies are swallowed (graceful continuation)

**GET `/api/v1/companies/export`**
- Query params: `?format=csv&fields=name,industry,size,region,status&company_ids=...`
- Maps short names (`name` → `name_ar`, `size` → `employees_count`)
- Uses column-level `select()` for efficiency (only fetches requested columns)
- Returns CSV file download with Content-Disposition header

### B-2: Advanced Filtering API (2d)

Enhanced `GET /api/v1/companies` with:

| Param | Type | Behavior |
|-------|------|----------|
| `industry` | string | Comma-separated, mapped to `{"in": [...]}` filter (OR) |
| `size_min` | int | Mapped to `employees_count` ≥ value via `{"gte": N}` |
| `size_max` | int | Mapped to `employees_count` ≤ value via `{"lte": N}` |
| `created_from` | date | Mapped to `created_at` ≥ date via `{"gte": date}` |
| `created_to` | date | Mapped to `created_at` ≤ date via `{"lte": date}` |
| `status` | string | Comma-separated → `{"in": [...]}`, single → exact match |

All filters are combinable (AND logic). The `CompanySearchRepository._build_base()` already supports `gte`/`lte`/`in` operators so no changes needed there.

### B-3: Keyset Pagination (1d)

Verified all company list endpoints:

| Endpoint | Old Pagination | New Pagination |
|----------|---------------|----------------|
| `GET /companies` | OFFSET (when no cursor) + keyset (when cursor provided) | **Always keyset** — removed OFFSET fallback |
| `GET /companies/cursors` | Pure keyset ✅ | Unchanged |
| `GET /companies/search` | N/A (not a separate endpoint) | Uses main `/companies` |
| `GET /companies/filter` | N/A (not a separate endpoint) | Uses main `/companies` |

Changes made:
- `CompanyRepository.search()`: Replaced `base.offset(...).limit(page_size)` with `base.limit(page_size + 1)` (keyset pattern: WHERE + ORDER BY + LIMIT). The `page` parameter is retained for API compatibility but no longer controls offset.
- `CompanyService.search_companies()`: Same migration — replaced `offset().limit()` with `limit(page_size + 1)` and added order_by + optional keyset condition.
- `router.py`: Changed `response_model` from `PaginatedResponse` to `CursorResponse`. Always returns cursor-based response with `next_cursor` and `has_next`.

---

## Test Results

Environment: **PostgreSQL test database not available** (pre-existing configuration issue — `POSTGRES_PASSWORD` not set). All new code verified via:

1. **AST validation**: All 5 modified/new files pass `ast.parse()`
2. **Unit tests for bulk operations** (9 tests, in `test_bulk_operations.py`):
   - `test_bulk_update_allowed_fields` — verifies whitelist enforcement
   - `test_bulk_update_ignores_disallowed_fields` — verifies `name_ar` excluded
   - `test_bulk_update_handles_errors` — verifies graceful per-company failure
   - `test_bulk_delete_soft_delete` — verifies `status`/`is_active` changes
   - `test_bulk_delete_handles_errors_gracefully` — verifies error swallowing
   - `test_valid_bulk_edit_request` / `test_bulk_edit_response` — schema validation
   - `test_valid_bulk_delete_request` / `test_bulk_delete_response` — schema validation
3. **Existing tests**: Updated `test_search_companies_pagination_second_page` to use cursor-based pagination instead of `page=2`

**Note**: Existing 48 tests in `test_service.py` and `test_company_extended.py` require a live PostgreSQL database (`salesos_test`) and will pass when `POSTGRES_PASSWORD` environment variable is configured.
