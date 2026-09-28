# 170 — `app/modules/marketplace_listings`: any authenticated user of any tenant could create, delete, or falsely certify/publish platform-wide catalog listings; fixed

**Read-only in scope of production/salesos_test.** Pure unit-level fix (in-process `TestClient`, no database); no database container needed.

## 1. Scope

Pivoting to `app/modules/*` per the loop's own next-step instruction (the `domains/` sweep closed in report 169). `app/modules/marketplace_listings` (1,283 lines) — a separate module from `domains/marketplace` (report 166's finding), representing a browsable catalog of connectors/apps/prompt-packs/playbooks rather than per-deployment plugin installation.

## 2. The bug — same severe class as report 166's `domains/marketplace` finding

`app/modules/marketplace_listings/store.py`'s own docstring: *"Owner-platform catalog scope (not tenant RLS tables)"* — `MemMarketplaceListingStore` (`_STORE`, module-level singleton) is a single, process-wide, in-memory catalog shared by every tenant, confirmed mounted at boot (`app/boot/routers.py:245-251`).

Every endpoint in the router was gated by the same `_AUTH = [Depends(verify_token)]` (mere authentication, no role check). For the **read** endpoints (`list_listings`, `get_listing`, `listings_meta`, `certify_pipeline_meta`) this is a reasonable, intentional design — any authenticated user browsing a shared marketplace catalog is analogous to any logged-in user browsing an app store's public listings, and `install_listing`/`list_catalog_installs` are already correctly tenant-scoped (via `Depends(get_current_tenant_id)`, a tenant recording its own install receipt, not a catalog mutation).

But the same bare `_AUTH` gate also covered every endpoint that **mutates the shared catalog**: `upsert_listing` (create/update any listing), `delete_listing`, `submit_listing`, `certify_listing`, `publish_listing_route`, `seed_first_party_listings`, `seed_publish_pack_listings`. Any authenticated user of any role, any tenant, could create a fake listing, delete a legitimate first-party one (e.g. the seeded `connector-odoo`), or falsely mark any listing as `"certified"`/`"published"` — visible to and trusted by every other tenant on the deployment.

## 3. Fix — same established precedent as report 166

Added `_ADMIN_AUTH = [Depends(require_role_dep("admin"))]` and applied it to exactly the 7 catalog-mutating endpoints listed above, leaving the 6 read/tenant-scoped endpoints (`listings_meta`, `certify_pipeline_meta`, `list_catalog_installs`, `install_listing`, `list_listings`, `get_listing`) unchanged at `_AUTH` — deliberately preserving the intended "any authenticated user can browse the shared catalog" experience while closing the mutation gap. Matches DEC-159 (report 115) and report 166's already-ratified fix for the identical shape of gap; the same open question from report 166 applies here too (whether "admin" should mean the caller's own tenant's admin or a true platform-wide owner) — left undecided as a genuine product question, not resolved unilaterally.

## 4. Verification — genuine red→green, a cleaner reproduction than report 166's

New `tests/unit/test_marketplace_listings_admin_gate.py` (4 tests): a non-admin (`"user"`) role and a `"manager"` role are both rejected with 403 on all 7 mutating endpoints; a non-admin can still browse the catalog (`list_listings`/`meta` return 200, confirming the fix didn't over-correct); an admin can genuinely create and delete a listing end-to-end.

Scoped `git stash push -- salesos/backend/app/modules/marketplace_listings/router.py` (reverting only the fix): unlike report 166's reproduction (which hit `verify_token`'s real-JWT requirement, since only `get_current_user_role` was overridden), this test harness overrides **both** `verify_token` and `get_current_user_role`, so the reverted code's actual vulnerability was reproduced directly and precisely: `POST /marketplace/listings` with role `"user"` returned **200 OK**, genuinely creating a listing — the exact severe defect this report describes, not merely an inference from a different error code. `git stash pop` restored the fix; all 4 tests re-confirmed PASS.

## 5. Regression

Combined with the existing `tests/unit/test_story_13_01_marketplace_listing.py` (pure model/store-level tests, unaffected): 10/10 PASS. Ruff (`--select E4,E7,E9,F,I`) caught one import-sort issue in the new test file (auto-fixed via `--fix`, a mechanical reordering with no functional change); 0 findings after. `python -m py_compile` and `git diff --check`: clean.

## 6. Scope and safety

- Two files touched: `salesos/backend/app/modules/marketplace_listings/router.py` (fix + explanatory comment), `salesos/backend/tests/unit/test_marketplace_listings_admin_gate.py` (new).
- No database or container needed — the fix and its verification are both pure in-process HTTP-level checks.
- No production/`salesos_test` write. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization. Per the loop's own instruction, this is the first finding in the newly-started `app/modules/*` sweep (following the `domains/` sweep's closure in report 169). Given the sheer number of `app/modules/*` subdirectories (40+), prioritizing files with real DB/persistence logic over pure Pydantic-schema modules, as instructed.
