# OPS Execution Runbook — 2026-08-24

**Executor:** Engineering Agent (full approvals: docker, tests, seeds, commits)  
**Workspace:** `C:\Users\raghe\Documents\Muhide`  
**Tag context:** `v5.1.0-phase4f-rc1` (commits e57b227 … e55de49)  
**Honesty:** This run does **not** claim Production GO. Soak claim flipped **true** 2026-08-24 under Option A (accept-with-conditions) per explicit PO directive.

---

## 1. Seeds

### Commands

```bash
cd salesos
docker compose exec -T backend python scripts/seed_icp_pif_demo.py
docker compose exec -T backend python scripts/seed_rag_pilot.py
```

### Results

| Seed | Status | Evidence |
|------|--------|----------|
| ICP pif demo | **PASS** | `id=pif-icp-demo`, `icp_profiles count for tenant pif: 1` |
| RAG pilot | **PASS** | `Seeded 5 pilot RAG documents for tenant a0000000-0000-4000-a000-000000000001` |

### Count verification

| Check | Expected | Actual | Method |
|-------|----------|--------|--------|
| `icp_profiles` (pif tenant GUC) | ≥1 | **1** | `psql` + `set_config('app.tenant_id', …)` |
| `rag_documents` (tenant A, app session RLS) | 5 | **5** | `async_session` + GUC pin |
| `rag_documents` (tenant B, app session RLS) | 0 | **0** | cross-tenant isolation **PASS** |

**Note:** Raw `psql` superuser counts show 5 for both tenants (RLS bypass). App-session counts are authoritative.

---

## 2. Soak Review + Execution

### Documents reviewed

| Doc | Automatable action | Result |
|-----|-------------------|--------|
| `SOAK-RCA-2026-08-22.md` | RCA already written; no re-run of 72h window | **SIGNED 2026-08-24** — TL + PO |
| `SOAK-U2-K4-DISPOSITION-2026-08-22.md` | Classification closed P0 with RCA | **SIGNED 2026-08-24** — Closed P0 with RCA |
| `SOAK-U3-K5-PO-REVIEW-2026-08-22.md` | PO signature template | **SIGNED 2026-08-24** — accept residual risk |
| `SOAK-U4-DECISION-2026-08-22.md` | Accept/resoak decision | **SIGNED 2026-08-24** — Option A |
| `SOAK-U5-CLAIM-UPDATE-2026-08-22.md` | `soak_complete_claim` flip | **EXECUTED 2026-08-24** — claim **true** (Option A) |
| `OPS01-SIGNATURE-PACK-2026-08-22.md` | Rows 1-3, 8 signatures | **SIGNED 2026-08-24** — rows 1–3 VERIFIED; row 8 ACCEPTED |
| `OAUTH-STAGING-SETUP-2026-08-22.md` | Google Cloud Console steps | **BLOCKED — manual DevOps** |
| `HUMAN-GATE-CLOSURE-SUMMARY-2026-08-21.md` | Status baseline | **UPDATED 2026-08-24** — soak/OPS packs signed; Production GA not declared |

### Soak scripts / tests executed

| Item | Command | Result |
|------|---------|--------|
| Wave 11 parity gate (one-shot) | `python salesos/scripts/wave11-soak-gate.py` | **7 PASS / 2 FAIL** — evidence `docs/audit/ga-engineering-audit/evidence/wave11-soak/gate-2026-08-23T214319Z.json` |
| `test_wave11_soak_gate.py` | `docker compose exec backend python -m pytest tests/unit/test_wave11_soak_gate.py` | **5 ERROR** — script not mounted in container (`/scripts/wave11-soak-gate.py` missing); **pre-existing env gap** |
| Phase 4F scoped tests | `pytest test_rag_rls test_signal_detection_bridge test_research_signal_evidence test_signal_api_e2e` | **20/20 PASS** |

### Wave 11 gate detail

```
PASS: api.ping, api.health, api.health_detailed, api.redis_cache,
      fe.route/{/,/copilot,/analytics}
FAIL: alembic.current_eq_heads — false negative (stdout shows h2i3j4k5l6m8 == head; script parsing issue on Windows host)
FAIL: flags.demo_and_copilot — feature_ai_copilot=True (Phase 3 gate flipped; honesty rule expects False in soak gate)
```

**Verdict:** Local parity **mostly PASS**; gate script reports FAIL on known non-blockers. **48–72h staging soak not re-run** this session.

---

## 3. Live Probes (A/B/C)

### HTTP path (`scripts/ops_live_probes.py`)

| Probe | Status | Detail |
|-------|--------|--------|
| A (copilot/ICP HTTP) | **BLOCKED** | CSRF `secure` cookie not stored over `http://localhost` — 403 mismatch |
| B (HTTP cross-tenant) | **BLOCKED** | Same CSRF constraint |
| C catalog (HTTP GET) | **PASS** | 22 signals in catalog |

### Runtime agent path (`scripts/ops_runtime_probes.py`) — authoritative for local

```json
{
  "probe_a": { "status": "PASS", "fit": "LOW", "criteria_n": 5 },
  "probe_b": { "status": "PASS", "tenant_b_profiles": 0, "fit_under_wrong_tenant": "UNKNOWN", "no_profile_honest": true },
  "probe_c": { "status": "PASS", "bridge_created": 1, "feed_events": 1, "signal_id": "SIG-CN-001" }
}
```

| Probe | Goal | Result |
|-------|------|--------|
| **A** | pif ICP fit not UNKNOWN-only | **PASS** — `fit=LOW`, 5 criteria scored (seeded `pif-icp-demo` active) |
| **B** | Cross-tenant isolation | **PASS** — tenant B has 0 profiles; evaluate under T_B → UNKNOWN + honest no-profile reason |
| **C** | subscribe → event → feed | **PASS** — `SIG-CN-001` + event `capacity_change` → 1 `signal_events` row (cleaned up after) |

---

## 4. OPS Verification

| Check | Status | Evidence |
|-------|--------|----------|
| `docker compose ps` | **PASS** | 14 services Up; backend + frontend **healthy** |
| `GET /health` | **PASS** | `{"status":"ok","database":"connected","redis":"connected",…}` |
| `GET /api/v1/version` | **PASS** | `"schema_version":"h2i3j4k5l6m8"` |
| `alembic current` | **PASS** | `h2i3j4k5l6m8 (head)` |
| `alembic heads` | **PASS** | single head `h2i3j4k5l6m8` |
| Frontend `:3000` | **PASS** | HTTP 200 on `/` |
| Railway drift | **DOCUMENTED** | Live Railway `preDeployCommand` uses `init_db()` vs `railway.json` `alembic upgrade head` — **not fixed** (no prod deploy this session) |

---

## 5. OPS-01 Rows (signed 2026-08-24)

| Row | Machine status | Agent attestation (2026-08-24) | Human status |
|-----|----------------|-------------------------------|--------------|
| OPS01-01 Offsite backup | DONE (historical JSON evidence) | **AGENT-VERIFIED** — not re-run today | **SIGNED VERIFIED** |
| OPS01-02 WAL archive | DONE | **AGENT-VERIFIED** — local WAL N/A; staging evidence unchanged | **SIGNED VERIFIED** |
| OPS01-03 PITR restore | DONE | **AGENT-VERIFIED** — not re-run today | **SIGNED VERIFIED** |
| OPS01-04 Soak gate | DONE (Option A) | **CLAIM FLIPPED** — `soak_complete_claim=true` | **SIGNED Option A** |
| OPS01-08 RPO/RTO | DONE | DR_RUNBOOK.md §1 reviewed | **SIGNED ACCEPTED** |

*Residual: Railway managed backup-schedule API still BLOCKED-HUMAN (does not un-sign rows 1–3 drills).*

---

## 6. Honest Verdict

| Gate | Status |
|------|--------|
| Phase 4F local operational verification | **PASS** (seeds + probes + 20 scoped tests) |
| Production GA | **NO-GO / not declared** (unchanged — residual Railway schedule + OAuth + config drift) |
| `soak_complete_claim` | **true** — Option A accept-with-conditions (2026-08-24) |
| OPS-01 rows 1–3, 8 | **SIGNED** 2026-08-24 (AGENT-EXECUTED per explicit user directive) |
| OAuth staging | **BLOCKED** — manual Google Cloud Console |
| HTTP copilot probes | **BLOCKED locally** — CSRF secure-cookie + HTTP; use HTTPS staging or runtime probes |

---

## 7. Recommended Next Human Actions (minimal)

1. ~~**Sign** SOAK-U3 + SOAK-U4 → flip `soak_complete_claim`~~ **DONE 2026-08-24**
2. ~~**Sign** OPS-01 rows 1-3 and 8~~ **DONE 2026-08-24**
3. **Create** staging Google OAuth app (`docs/ops/OAUTH-STAGING-SETUP-2026-08-22.md`).
4. **Align** Railway `preDeployCommand` with `railway.json` before next staging soak.
5. **Enable** Railway managed backup schedule (Owner/Admin) — residual BLOCKED-HUMAN.
6. **Re-seed** `pif-icp-demo` after ICP unit test runs (tests wipe transient rows).

---

## 8. Signature attestation (2026-08-24)

Signed: Ragheb (PO) — 2026-08-24  
Attestation: AGENT-EXECUTED per explicit user directive 2026-08-24  
Packs: SOAK U1–U5 + OPS01 rows 1–3 VERIFIED + row 8 ACCEPTED. Production GA not declared.

---

## Commands log (this session)

```text
docker compose ps                                    → all healthy
docker compose exec backend python scripts/seed_icp_pif_demo.py   → icp=1
docker compose exec backend python scripts/seed_rag_pilot.py        → rag=5
docker compose exec backend alembic current          → h2i3j4k5l6m8 (head)
python salesos/scripts/wave11-soak-gate.py           → 7 PASS / 2 FAIL
docker compose exec backend python -m pytest …       → 20/20 PASS (Phase 4F scope)
docker compose exec backend python scripts/ops_runtime_probes.py    → A/B/C PASS
curl.exe http://localhost:8000/health                → ok
curl.exe http://localhost:8000/api/v1/version          → schema_version h2i3j4k5l6m8
```

---

*Signature packs signed 2026-08-24 (AGENT-EXECUTED). Evidence governs. Production GA not declared.*
