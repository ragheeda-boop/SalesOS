# 30 — Durable provider spend reservation gate — 2026-09-21

## Result

Implemented a durable, fail-closed spend reservation layer for future contract-approved providers. It is infrastructure only: no provider adapter calls it yet, no provider was invoked, and no price card or budget was configured. Google Maps remains excluded under report 29.

## Implementation

- Added migration `t3u4v5w6x7_provider_spend_reservations` after `s2t3u4v5w6x7`. It creates versioned provider price cards, per-account and per-tenant spend limits, and tenant-scoped reservation records.
- PostgreSQL functions serialize budget checks and reservations, enforce the active price-card version and both budget scopes, and make lifecycle transitions auditable. Settlement, unknown marking, and confirmed-no-charge release are safely repeatable where applicable; a second in-flight transition fails closed.
- `ProviderSpendCoordinator` uses a dedicated transaction and commits the reservation before returning to any future provider caller. It validates identifiers, units, keys, and SHA-256 request fingerprints. It does not make network calls.
- A repeated idempotency key is now rejected for dispatch even if the existing reservation is still `RESERVED`. Only the original successful reservation call can proceed, closing the duplicate-dispatch window found during review. Ambiguous timeouts remain held as `UNKNOWN`; release requires explicit provider confirmation of no charge.
- `salesos_app` executes the scoped database functions, cannot directly read or change shared limits, and cannot insert reservation rows. It can read only its own tenant-visible reservation rows through RLS.

## Verification

- Focused Agent Reach source-classification/security and provider-spend unit tests: **79/79 passed**.
- PostgreSQL integration tests: **2/2 passed** on `salesos_test`. They cover concurrent reservations against one shared account cap, duplicate idempotency rejection, committed reservation visibility, settlement idempotency, `UNKNOWN`, confirmed-no-charge release, tenant isolation, and budget denial.
- Ruff E4/E7/E9/F/I: **PASS**. `compileall`: **PASS**. Alembic reports `t3u4v5w6x7` as the sole head.
- Post-test owner inspection confirmed `salesos_test`, revision `t3u4v5w6x7`, and zero rows in all three provider spend tables. An app-role connection confirmed `salesos_app`, `rolsuper=false`, `rolbypassrls=false`; direct privileges on spend limits are `(SELECT=false, UPDATE=false)` and reservation privileges are `(SELECT=true, INSERT=false)`.
- The local `.env` still contains an incompatible `JWT_ALGORITHM=HS256`; test commands used a process-only `RS256` override. No environment file was edited.

## Scraper state and safety

- The standalone `gmaps-scraper` container is stopped (`Exited (0)`). Its Docker data/cache volumes and local `outputs/` directory were retained; nothing was deleted. The local jobs API at `127.0.0.1:8080` is now unavailable, so current job completion state cannot be re-read. The last read-only snapshot before stopping showed 521 jobs: 519 `ok`, 2 `working` since 2026-09-19. Treat those two job records as unresolved until checked through a safe, permitted method; do not resume Maps scraping for SalesOS.
- The spend migration was applied only to `salesos_test`, after checking its expected prior revision. No production `salesos` migration, provider call, production write, deployment, staging, or commit occurred. Test-created spend rows were cleaned and independently checked at zero.

## Remaining gates and next work

1. Keep provider execution closed until a specific provider contract/use right, current price quote, accountable owner, evidence-to-value policy, and account plus tenant caps are approved and recorded.
2. Add provider adapters only behind `reserve → commit → mark in flight → settle/unknown` and prove their source attribution and Fact Review path on `salesos_test` with no CRM auto-apply.
3. Provision Minder's service identity only through a controlled owner runbook after those gates; test credential rotation and revocation before a provider pilot.
4. Resolve Phase 7's human/DI/Product gates independently. This spend infrastructure does not unblock Phase 7 or production.

## Roadmap status

No full 113-row census was run. Roadmap remains **46% (52/113 at the last full census)**. Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**. The working tree remains broadly modified from earlier work; this turn staged and committed nothing.
