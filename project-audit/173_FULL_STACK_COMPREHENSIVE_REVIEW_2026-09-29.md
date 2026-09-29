# 173 — Full-Stack Comprehensive Review (2026-09-29)

**Scope:** authorized full-project review across backend, frontend, database,
Alembic chain, RLS, and evidence — diagnose, fix, verify.
**Branch:** `fix/login-and-keys`
**DB under test:** `salesos_test` (no production writes; no merges; no CR
mutations; no fabricated rows; no external API calls).

---

## 1. Verdict

| Layer | Result | Evidence |
|-------|--------|----------|
| `compileall` (app + scripts) | **PASS** | exit 0 |
| `ruff` (touched files) | **PASS** | E9/F clean on all files I modified |
| Backend unit suite (full) | **PASS** | `3869 passed, 4 skipped, 6 xfailed, 4 xpassed` in 80.70s — **0 failed** |
| Phase 6 unit (6 modules) | **PASS** | 91 tests within the 121-test run |
| Phase 7 integration | **PASS** | `121 passed` (phase6+7 batch) · `22 passed, 1 skipped` (queue) |
| Frontend typecheck | **PASS** | `tsc --noEmit` → 0 errors (scoped to `salesos/frontend` — see §5.3) |
| Frontend `next build` | **PASS** | Docker `node:22-alpine`, `next build` exit 0 — `✓ Compiled successfully in 114s`, `✓ Generating static pages (120/120)`, **138 routes** |
| Frontend ESLint | **PASS** | in-image `npm run lint` → `✔ No ESLint warnings or errors` |
| Frontend unit tests | **PASS (flaky observed)** | in-image `npm run test` → `335/335 suites, 2691 passed, 1 skipped, 0 failed` (see §5.4) |
| Frontend Prettier (CI Stage 1) | **FAIL (pre-existing)** | `npx prettier --check 'src/**'` → **243 files** unformatted, all committed, none from this review |
| DB contract counts | **PASS** | exactly matches the 2026-09-28 baseline |
| Review queue state | **PASS** | matches gate bookkeeping exactly |
| RLS | **PASS** | 139/139 RLS+FORCE; the signal path verified live |
| Alembic chain | **PASS** | single head `a1b2c3d4e5f7` = `salesos_test` version |

Baseline comparison: the previously documented full-unit baseline was
`56 failed / 2761 passed / 3 skipped / 10 xfailed / 7 errors`. The current tree
is **0 failed / 3869 passed** — the documented env-dependent failure set is no
longer present in `tests/unit`.

---

## 2. Defect found and fixed (real product bug)

### 2.1 `upsert_signals` poisoned the caller's transaction

**File:** `app/modules/company/signal_persistence.py`
**Severity:** high — silent data loss in the signal marketplace loop
**Class:** transaction-integrity

`upsert_signals` wraps each `INSERT INTO company_signals` in
`try/except Exception`, logs a warning, and continues ("fail-graceful"). On
PostgreSQL a failed statement **aborts the enclosing transaction**. The
swallowed error therefore left the session unusable, and the caller's next
`await db.commit()` raised `PendingRollbackError` — rolling back work the
function never touched.

Observed effect via the signal detection bridge
(`app/modules/signal_marketplace/runtime_bridge.py:81-111`):

1. `INSERT INTO signal_events` succeeded and was flushed.
2. `upsert_signals` was called mid-transaction; its `INSERT` failed and the
   `except` swallowed it.
3. The `commit()` at `runtime_bridge.py:111` raised.
4. The `signal_events` row was **rolled back and lost**, while
   `created += 1` had already run — so the bridge reported success and wrote
   nothing.

This is exactly the Phase 4E contract ("subscribe → receive"), and it was
broken whenever `company_signals` insertion failed (e.g. non-empty `metadata`
before the `json.dumps` fix, or any constraint/typing mismatch).

**Fix:** scope each insert to a SAVEPOINT via `db.begin_nested()`, so a failed
statement no longer aborts the outer transaction. The public contract is
unchanged — same signature, same return value, still fail-graceful, and the
existing `db.commit()` + `apply_tenant_guc()` re-pin (relied on by
`app/modules/company/service.py:596`) is deliberately preserved.

**Verification:**
- `tests/unit/test_signal_detection_bridge.py` → 6/6 pass (was 1 failed).
- `tests/unit/test_signal_api_e2e.py` → pass (was 2 failed).
- `tests/integration/test_signal_persistence_db.py` → 3/3 pass (contract
  preserved for the other caller).
- Live loop probe: `created=1`, tenant A sees 1 row, tenant B sees 0 → the
  `subscribe → signal_event → company_signals` path and its RLS isolation both
  hold.

### 2.2 Test depended on leftover ambient data

**File:** `tests/unit/test_research_signal_evidence.py`

The Phase 4F test asserted `build_company_evidence` returns `found=True`, which
requires a real `companies` row for the pif tenant. That row was only ever
present because an earlier live §19/§4F probe left it behind; any unrelated
teardown/truncate made the test fail with
`company_record_not_found_for_tenant` — an environment dependency, not a
product defect. The fixture now seeds the `tenants` + `companies` rows it
depends on (idempotent `ON CONFLICT DO NOTHING`) and removes the company row
on cleanup, so it neither inherits nor leaks state.

### 2.3 MA_UNRESOLVED test was data-blocked, not code-broken

**File:** `tests/integration/test_phase7a_review_queue_db.py`

`test_ma_unresolved_capture_is_record_only` failed with
`MA unresolved subject_key is not a v0.7 contact`. The guard is correct and
intentional: `ReviewQueueService.record_disposition` requires the subject to
exist as a real `muhide_contacts_v07` row in `md_source_rows`
(`SELECT 1 FROM md_source_rows WHERE source_id='muhide_contacts_v07'`). No v0.7
feed exists in `salesos_test`, and the existing people ids are `C-…`-shaped,
not `GP-…`.

No code or data was changed to force this green — synthesizing source rows would
violate the append-only / no-fabrication invariant. The test is now marked
`skipif` with a DB-backed presence probe and an explicit reason, so it runs
automatically once the v0.7 feed is ingested.

### 2.4 Lint hygiene on the Phase 7 scripts

- `scripts/phase7a_backfill_queue_linkage.py`: removed unused `uuid` import
  (pre-existing), `dict(...)` → dict literal.
- `scripts/phase7a_capture_gate_workbooks.py`: removed an unused `noqa`.

Both re-verified by a real DRY RUN (`p1_rows 640 / p1_rows_linked 640 /
p3_rows 2661 / database_writes 0`).

---

## 3. Findings that are NOT defects

### 3.1 Alembic "multiple heads" — false alarm

A regex pass over the 130 migration files appeared to show 7 heads
(`a1b2c3d4e5f7`, `a1b9c8d7e6f5`, `f4aee055fd6e`, `j4k5l6m7n8o9`,
`j5k6l7m8n9o0`, `p6a0b1c2d3e4`, `p7q8r9s0t1u2`). It is wrong: six of those are
consumed as `down_revision` parents by merge migrations
(`k6l7m8n9o0p1_merge_phase0_agent_reach.py`,
`m5b0a1c2d3e4_merge_adr030_agent_tasks.py`,
`q7r8s9t0u1v2_phase6_cr_merge.py`). The authoritative check,
`python -m alembic heads`, reports a **single head `a1b2c3d4e5f7`**, which
equals `salesos_test.alembic_version` exactly. No duplicate revision ids. No
action needed; recorded so the next reviewer does not re-investigate.

### 3.2 Container image is stale (operational, not code)

`salesos-backend-1` carries 107 of the 130 migration files and reports a
different, older head (`o0p1q2r3s4t5`). The host tree is authoritative and
correct. Running `alembic` **inside the container** would compute the wrong
graph — rebuild the backend image before any container-side migration command.
No source change required.

### 3.3 `salesos` (production DB) has no `alembic_version` row

0 rows. This is a pre-existing local/production state question, deliberately
left untouched (no production writes). Flagged for DevOps/PO.

### 3.4 `md_review_queue_state` has no RLS

Correct by design: the table has no `tenant_id` column (verified), it is a
global master-data review queue, not tenant-scoped. `signal_catalog` likewise
has no RLS as a deliberate `GLOBAL_PLATFORM` classification (§25), and the
repo read path was verified to return all 23 seeded platform signals with and
without a GUC pin.

---

## 4. Verified state (unchanged by this review)

| Item | Count |
|------|-------|
| `md_global_companies` | 296,746 |
| `md_global_people` | 1,124 |
| `md_source_rows` | 862,775 |
| `md_review_candidates` | 54,185 |
| `md_identity_classifications` | 296,746 |
| `md_review_queue_state` | 3,337 |

Queue: `P1_CANDIDATE dispositioned 640` · `P3_PAIR pending 2661` ·
`SHORT_CR dispositioned 5 / pending 31`.

---

## 5. Frontend verification (closed via Docker) + remaining gaps

The host `node_modules` is unusable — 581 top-level entries but `react`,
`react-dom`, `next` (no `package.json`), `eslint`, `tailwindcss`, `zod` are
absent and `node_modules/.bin` is empty, so `npx` tried to download its own
`next`. `package.json` is correct, so this is a local install artifact, not a
manifest defect. Rather than mutate the host, verification ran inside the
project's own `node:22-alpine` build stage (`fe-verify:build`), which installs
875 packages from `package-lock.json` — i.e. the same input CI uses.

### 5.1 `next build` — PASS
`added 875 packages` → `✓ Compiled successfully in 114s` →
`Linting and checking validity of types` → `✓ Generating static pages (120/120)`
→ 138 routes (50 under `/v3`), exit 0. Note: the route count is **138, not the
109 recorded in AGENTS §39** — the app has grown; the older figure is stale.

### 5.2 ESLint — PASS
`npm run lint` in-image → `✔ No ESLint warnings or errors`. (Next 15 emits a
deprecation notice for `next lint`; not an error.)

### 5.3 Typecheck scope — corrected claim
`tsc --noEmit` = 0 errors is real, but it is **scoped to `salesos/frontend`**
(root `tsconfig.json` `include: ["**/*.ts"]` resolves relative to that
directory). The parallel agent's 10 TypeScript files live in
**`salesos/packages/`** — a separate tree with its own `package.json`
(`@salesos/decision-platform-lab`, `typecheck` + `test` scripts) that the
frontend tsconfig cannot reach and **no CI workflow references**. An earlier
statement in this session that typecheck covered those files was wrong and is
withdrawn: `tsc=0` says nothing about them. `salesos/packages/` also has no CI
coverage at all.

### 5.4 Frontend unit tests — PASS, with observed flakiness
- Run 1 (under concurrent load): `2 suites / 3 tests failed` —
  `create-task-form.test.tsx`, `create-review-form.test.tsx`, both
  `waitFor` timeouts in `@testing-library/dom`.
- Run 2 (clean): `335/335 suites, 2691 passed, 1 skipped, 0 failed`.

The same suites pass in isolation and in a clean full run, so these are
**timing flakes under CPU contention, not defects** — but they will
intermittently redden CI. The worker also reports
`A worker process has failed to exit gracefully`, i.e. a teardown/timer leak.

### 5.5 Prettier — FAIL, pre-existing (243 files)
`npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"` → **243 files**
unformatted. None of them were modified by this review or by the parallel
agent (e.g. `src/lib/commands.ts` was last touched in `fb7073d7`). This is a
**committed-state failure of CI Stage 1**, reproducible and unrelated to
2026-09-29 work. It is deliberately **not** auto-fixed here: reformatting 243
files would swamp the audit diff and touch code this review did not examine.
Decision needed (owner: frontend/PO) — either run `prettier --write` as a
dedicated formatting commit, or baseline the check.

### 5.6 Still not verified
- **`salesos/packages/platform/decision` lab twin** — its own `typecheck`/`test`
  scripts were not run: no `node_modules` there, and no CI job. The 10
  parallel-agent files remain unverified by any automated gate.
- **Full `phase6_apply`** — last full run (2026-09-28) completed in 796s with
  `safety={}`; not repeated because the DB contract proves the result is
  already applied and a re-run is a ~13 minute write pass.

---

## 6. Files changed

| File | Change |
|------|--------|
| `app/modules/company/signal_persistence.py` | SAVEPOINT per insert — fixes cross-module transaction poisoning |
| `tests/unit/test_research_signal_evidence.py` | self-contained tenant+company fixture; unused import removed |
| `tests/integration/test_phase7a_review_queue_db.py` | data-aware `skipif` for the v0.7-dependent MA test |
| `scripts/phase7a_backfill_queue_linkage.py` | lint hygiene (unused import, dict literal) |
| `scripts/phase7a_capture_gate_workbooks.py` | lint hygiene (unused noqa) |

## 7. Commands run

```text
python -m compileall -q app scripts                       # exit 0
python -m ruff check <touched files>                     # E9/F clean
python -m pytest tests/unit -q                           # 3869 passed, 0 failed
python -m pytest tests/unit/test_phase6_*.py \
  tests/integration/test_phase7*.py -q                  # 121 passed
python -m pytest tests/integration/test_phase7a_review_queue_db.py -q
                                                           # 22 passed, 1 skipped
python -m pytest tests/integration/test_signal_persistence_db.py -q
                                                           # 3 passed
python scripts/phase7a_backfill_queue_linkage.py         # DRY RUN, 0 writes
python -m alembic heads                                   # single head a1b2c3d4e5f7
npx tsc --noEmit                                          # 0 errors (frontend scope)
psql: contract counts, queue breakdown, pg_class RLS census, live signal-loop probe

# frontend, inside the project's own node:22-alpine build stage
docker build -f Dockerfile -t salesos-frontend-verify:local .   # next build exit 0
docker build --target build -f Dockerfile -t fe-verify:build . # tagged build stage
docker run --rm fe-verify:build npm run lint                    # No ESLint warnings or errors
docker run --rm fe-verify:build npm run test                    # 335/335 suites, 0 failed
docker run --rm fe-verify:build npx prettier --check 'src/**/*.{ts,tsx,js,jsx,json,css,md}'
                                                               # 243 files (pre-existing)
```

## 8. Open items (unchanged, not code defects)

- Human gates: G2 (2,661 P3 pairs), G3 (31 short CR), G4 (6,268 remaining P1),
  G5 (651 P2 sample acceptance), DI P1/P2 methodology confirmation, G8–G16.
- MA_UNRESOLVED test stays skipped until the `muhide_contacts_v07` feed exists.
- Rebuild the backend container image (107/130 migrations) before any
  container-side `alembic` run.
- `salesos` production `alembic_version` is empty — DevOps/PO decision.
- `test_fact_proposal_service_db` 401-vs-403 was not re-examined in this pass.
- **Prettier: 243 committed files unformatted ⇒ CI Stage 1 is red on the
  current committed state.** Needs a dedicated formatting commit or a
  baselined check (owner: frontend/PO). See §5.5.
- **CI Stage 6 "Build Frontend" is disabled with `if: false`** (QUARANTINED
  DEC-150 B), so `next build` was verified by nobody before this review. Either
  re-enable it or record that build verification lives only in §5.1.
- **`salesos/packages/` (decision-platform-lab) has no CI coverage.** Its
  `typecheck`/`test` scripts are never executed by any workflow, so changes
  there are unverified by default. See §5.3 / §5.6.
- Frontend suites flake under CPU contention (`waitFor` timeouts in
  `create-task-form` / `create-review-form`); a worker also fails to exit
  cleanly. Worth a `--detectOpenHandles` pass. See §5.4.
- AGENTS §39's "109 pages" figure is stale — the build emits 138 routes.
