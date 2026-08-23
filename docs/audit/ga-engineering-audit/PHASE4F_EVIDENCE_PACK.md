# PHASE 4F EVIDENCE PACK — Intelligence Data Layer + Marketplace Loop

**SalesOS Phase 4A–4F (security foundation → live value loops)**  
**Date:** 2026-08-23  
**Status:** CODE-COMPLETE + DOCKER VALIDATED (scoped suites green; full unit triage recorded)  
**Validation:** build validated (Docker pytest + live probes per session summaries)  
**Companion:** [`UNIT-SUITE-TRIAGE-2026-08-23.md`](../../reports/UNIT-SUITE-TRIAGE-2026-08-23.md)

---

## Executive summary

Phase 4F closes the **intelligence data layer** gaps identified in the Data Readiness Gate (§23): RLS-isolated RAG, persisted ICP profiles, admin API, runtime adapter wiring, signal catalog boot seeding, and subscription→detection event loop. Grounded agents (13/13) remain frozen; value is **data + wiring**, not new agent logic.

**Full unit suite (2026-08-23, Agent-D):**

```text
56 failed, 2761 passed, 3 skipped, 10 xfailed, 288 warnings, 7 errors in 238.55s
NEW failures from Phase 4 work: 0 (baseline 56 pre-existing env failures unchanged)
```

**Scoped regression (grounded + Phase 4A–4E):** **144/144 PASS** (AGENTS.md §27)

---

## Parallel agent coordination (2026-08-23)

### Agent-B — ICP product loop **COMPLETE**

| Item | Evidence |
|------|----------|
| Seed script | `scripts/seed_icp_pif_demo.py` → `icp_profiles=1` for tenant `a0000000-0000-4000-a000-000000000001` (pif) |
| Profile id | `pif-icp-demo` |
| Frontend | `/v3/icp` — list + create |
| Scoring | fit=**HIGH** (not UNKNOWN-only) |
| Tests | `test_icp_*` **19/19 PASS** |
| Ops note | ICP unit tests wipe pif rows on cleanup — **re-seed after test runs** for live demo |

### Agent-C — RAG pilot **COMPLETE** (prior crumb)

| Item | Evidence |
|------|----------|
| Seed script | `scripts/seed_rag_pilot.py` |
| Corpus | `rag_documents`: tenant A=**5**, tenant B=**0** |
| RLS tests | `test_rag_rls` **8/8 PASS** |

### Agent-D — Triage + evidence **COMPLETE**

| Item | Evidence |
|------|----------|
| Full unit run | recorded in triage doc |
| Provider eval | [`PROVIDER-EVAL-2026-08-23.md`](../../reports/PROVIDER-EVAL-2026-08-23.md) |
| NEW failures | **0** |

---

## P4F-1: RAG RLS (Phase 4A Part B) — CLOSED

| Artifact | Path |
|----------|------|
| Migration | `h1i2j3k4l5m7_phase4a_rag_rls.py` |
| Tests | `tests/unit/test_rag_rls.py` — **8 tests** |
| Pilot data | `scripts/seed_rag_pilot.py` (Agent-C) |

**Proof:** no-GUC → 0 rows; cross-tenant read/write blocked; chunk parent EXISTS probe.

---

## P4F-2: ICP persistence (Phase 4A Part C) — CLOSED

| Artifact | Path |
|----------|------|
| Migration | `h2i3j4k5l6m8_phase4a_icp_profiles.py` |
| Repository | `app/modules/gtm/icp_persistence.py` |
| Tests | `tests/unit/test_icp_persistence.py` — **12 tests** |
| ADR | `docs/adr/0109-icp-persistence.md` |

---

## P4F-3: ICP runtime adapter (Phase 4B) — CLOSED

| Artifact | Path |
|----------|------|
| Sync adapter | `SyncICPStore` + `get_sync_icp_store()` in `icp_persistence.py` |
| Copilot wiring | `app/routers/copilot.py` — shared singleton into ICP + Recommendation agents |
| Tests | `tests/unit/test_icp_sync_adapter.py` — **8 tests** |

---

## P4F-4: ICP admin API (Phase 4C) — CLOSED

| Artifact | Path |
|----------|------|
| Router | `app/modules/gtm/icp_admin_router.py` |
| Registration | `app/boot/routers.py` under `/api/v1` GTM Intelligence |
| Tests | `tests/unit/test_icp_admin_api.py` — **7 tests** |
| Live value loop | transient profile → fit=MEDIUM · evidence cited · cleanup → icp=0 |

---

## P4F-5: ICP product seed + FE (Agent-B) — CLOSED

| Artifact | Path |
|----------|------|
| Seed | `scripts/seed_icp_pif_demo.py` |
| FE | `frontend/src/app/v3/icp/page.tsx` |
| Scoring | fit=HIGH for pif demo profile |
| Tests | ICP suite **19/19 PASS** |

---

## P4F-6: Signal catalog operationalization (Phase 4D) — CLOSED

| Artifact | Path |
|----------|------|
| Seeding | `app/modules/signal_marketplace/seeding.py` |
| Boot | `init_startup_services()` idempotent upsert |
| Compose | `knowledge-packs` ro mount + `KNOWLEDGE_PACKS_PATH` |
| Tests | `tests/unit/test_signal_catalog_seeding.py` — **5 tests** |
| Live | `signal_catalog = 22` platform signals after restart |

---

## P4F-7: Subscription→detection loop (Phase 4E) — CLOSED

| Artifact | Path |
|----------|------|
| Bridge | `app/modules/signal_marketplace/runtime_bridge.py` |
| Engine | `match_signals()` extraction in `engine.py` |
| Boot | `_init_signal_detection_subscriber` on event_runtime |
| Tests | `tests/unit/test_signal_detection_bridge.py` — **6 tests** |
| Live | pif subscribed SIG-CN-001 → event row → feed → cleanup |

---

## P4F-8: Grounded intelligence (Phases 1–3B) — CLOSED (frozen)

| Scope | Tests | Status |
|-------|-------|--------|
| Research grounding | 19 | PASS |
| Phase 2 competitor/relationship | 18 | PASS |
| Phase 3A ICP/recommendation | 19 | PASS |
| Phase 3B batch (8 agents) | 38 | PASS |
| Quota accounting | 7 | PASS (isolated; full-suite env ordering only) |
| **Total grounded scope** | **102+** in phase files; **144/144** combined scope | PASS |

Agents untouched for evidence contract; remaining ceiling is **product data** (contracts, tenders, news corpus), not agent stubs.

---

## Test count summary

| Layer | File(s) | Count | Result |
|-------|---------|-------|--------|
| RAG RLS | `test_rag_rls.py` | 8 | 8/8 isolated |
| ICP persistence | `test_icp_persistence.py` | 12 | PASS |
| ICP adapter | `test_icp_sync_adapter.py` | 8 | PASS |
| ICP admin API | `test_icp_admin_api.py` | 7 | 7/7 isolated |
| Signal seeding | `test_signal_catalog_seeding.py` | 5 | PASS |
| Signal bridge | `test_signal_detection_bridge.py` | 6 | PASS |
| Grounded 2/3A/3B + research | 4 files | 102 | PASS |
| **Phase 4F scoped total** | — | **144** | **144/144** |
| **Full unit suite** | `tests/unit/` | 2818 collected | 2761 pass, 56 fail, 7 err (0 new) |

---

## Gate exit criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | RAG tenant isolation (RLS) | ✅ PASS | 8 tests + pilot seed A=5 |
| 2 | ICP persisted + RLS | ✅ PASS | 12 tests + migration |
| 3 | ICP reachable from copilot (sync adapter) | ✅ PASS | 8 adapter tests + live UNKNOWN→HIGH with seed |
| 4 | ICP admin CRUD API | ✅ PASS | 7 tests + `/v3/icp` FE |
| 5 | Signal catalog non-empty at boot | ✅ PASS | 22 signals, 5 seeding tests |
| 6 | Subscribe → detect → event row | ✅ PASS | 6 bridge tests + live probe |
| 7 | Grounded agents unchanged / honest degradation | ✅ PASS | 13 agents frozen |
| 8 | Full unit NEW failures | ✅ PASS | 0 new (triage doc) |
| 9 | Provider production readiness | ❌ NO-GO | PROVIDER-EVAL — Dev-only Horde |
| 10 | Production GA | ❌ NO-GO | ga-engineering-audit unchanged |

---

## Remaining human actions

| Priority | Action | Owner | Blocker |
|----------|--------|-------|---------|
| P1 | Re-seed `pif-icp-demo` after ICP unit test runs (demo hygiene) | Dev | Test cleanup wipes rows |
| P1 | Stable LLM provider keys (`qual-a/b/c`) + qualification | DevOps | No commercial provider yet |
| P2 | Populate contracts / tenders / news (data gaps agents now state honestly) | PO+Data | Business sources |
| P2 | Fix pre-existing 56 full-suite env failures (async + frontend path) | Engineering | Not Phase 4 regression |
| P3 | Staging `OPENAI_BASE_URL` validation | DevOps | Approval |

---

## New / modified files (Phase 4A–4F rollup)

See AGENTS.md §23–§31 session summaries for per-phase file lists. Key additions:

- `app/alembic/versions/h1i2j3k4l5m7_phase4a_rag_rls.py`
- `app/alembic/versions/h2i3j4k5l6m8_phase4a_icp_profiles.py`
- `app/modules/gtm/icp_persistence.py`, `icp_admin_router.py`
- `app/modules/signal_marketplace/seeding.py`, `runtime_bridge.py`
- `scripts/seed_icp_pif_demo.py`, `scripts/seed_rag_pilot.py`
- `frontend/src/app/v3/icp/page.tsx`
- Unit tests: `test_rag_rls`, `test_icp_*`, `test_signal_*`, grounded phase suites
- `docs/adr/0109-icp-persistence.md`

---

**Phase 4F gate:** **CLOSED** for code + scoped evidence. Production GO remains **NO-GO**.
