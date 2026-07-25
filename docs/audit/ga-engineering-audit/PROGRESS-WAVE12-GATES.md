# Progress — Wave 12 Deploy Gates (2026-07-22)

**IDs:** PROD-W12-001 / PROD-W12-002 (prep) + pre-deploy automation  
**Classification:** light validated (scripts/docs only)  
**Production:** still **NO-GO** — no staging tabletop, no prod cutover, no Production GO claim

---

## Done this wave

| Item | Status | Notes |
|------|--------|-------|
| `jsonschema` in backend deps | **Done (declare)** | Added to `salesos/backend/pyproject.toml` (`^4.22`). Image rebuild **not** run (low-load). Until rebuild: `docker compose exec backend pip install 'jsonschema>=4.22'` |
| Pre-deploy gate script | **Done** | `salesos/scripts/pre-deploy-gates.ps1` — fails on alembic drift, `/health` not ok, `SALESOS_TESTING` trap; optional `-RunUnitTests` |
| Deploy/rollback runbook sync | **Done (docs)** | Evidence links to PROGRESS-* ; DONE vs OPEN marked |
| Go-live checklist sync | **Done (docs)** | Evidence column points at wave progress; boxes remain unchecked for unexecuted cutover |
| GA scoreboard | **Done** | [GA_STATUS.md](./GA_STATUS.md) — **NO-GO** with reasons |

---

## Gate script usage

```powershell
cd salesos
.\scripts\pre-deploy-gates.ps1
.\scripts\pre-deploy-gates.ps1 -RunUnitTests
.\scripts\pre-deploy-gates.ps1 -BackendUrl http://localhost:8000
# Host-only health + alembic (no compose exec):
.\scripts\pre-deploy-gates.ps1 -SkipDocker
```

Hard fail conditions:

1. Alembic `current != heads` (`scripts/check_alembic_head.py`)
2. `GET {BackendUrl}/health` not HTTP 200 with `status` ok/healthy
3. `SALESOS_TESTING` non-empty on host or in backend container (`1/true/yes/on` or trap `0/false/no/off`)
4. With `-RunUnitTests`: unit pytest non-zero exit

Advisory (warn): `jsonschema` missing inside running image until Poetry rebuild.

---

## Wave 12 acceptance vs PRODUCTION_PLAN

| Acceptance | Status |
|------------|--------|
| Rolling deploy model documented | **Done** (runbook) |
| Rollback protocol documented | **Done** (runbook) |
| Pre-deploy gates automated | **Done** (script; runtime proof depends on local stack) |
| Local tabletop of deploy + rollback | **DONE** — [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md) |
| Staging tabletop of deploy + rollback | **BLOCKED** — [PROGRESS-WAVE12-STAGING.md](./PROGRESS-WAVE12-STAGING.md) |
| Production cutover | **OPEN** — not executed; must not claim GO |

---

## Evidence links (prior waves)

| Wave | Progress file | Prep status |
|------|---------------|-------------|
| 0 FE | [PROGRESS-WAVE0-FE.md](./PROGRESS-WAVE0-FE.md) | lint/tsc/build green (local) |
| 1/3/5 | [PROGRESS-WAVE1-3-5-PLATFORM.md](./PROGRESS-WAVE1-3-5-PLATFORM.md) | Alembic local head now **0040** (was 0039); auth probes |
| 2 Sec | [PROGRESS-WAVE2-SEC.md](./PROGRESS-WAVE2-SEC.md) | P0 IDOR/SSRF/KG/Forecast fixes (light validated) |
| 4/8/9 | [PROGRESS-WAVE4-8-9-INFRA.md](./PROGRESS-WAVE4-8-9-INFRA.md) | Compose/obs/secrets config |
| 4 FE image | [PROGRESS-WAVE4-FE-IMAGE.md](./PROGRESS-WAVE4-FE-IMAGE.md) | `/copilot` `/analytics` → 200 |
| Cont. | [PROGRESS-CONTINUATION.md](./PROGRESS-CONTINUATION.md) | Unit ~1542 passed; cache/graph connected |
| 6–7 | [PROGRESS-WAVE6-7-DOCS.md](./PROGRESS-WAVE6-7-DOCS.md) | Docs / AI honesty / runbook prep |

---

## Local runtime evidence (2026-07-22 follow-up)

Windows PowerShell 5.1 previously failed to **parse** the script (Unicode em-dash). Script was ASCII-hardened; compose-exec stderr + `python -c` quoting were fixed so advisory probes do not abort under `$ErrorActionPreference=Stop`.

```powershell
cd salesos
.\scripts\pre-deploy-gates.ps1 -BackendUrl http://127.0.0.1:8000
```

| Gate | Result |
|------|--------|
| SALESOS_TESTING (host + container) | **PASS** (unset/empty) |
| Alembic current == heads | **PASS** (`0040` == `0040`) — re-verified 2026-07-22 after graph_edges fix |
| `/health` | **PASS** HTTP 200; status ok |
| Unit pytest | **SKIP** (no `-RunUnitTests`) |
| jsonschema advisory | **PASS** (import ok; image bake 4.26.0) |
| Script exit | **0** — RESULT: PASS (still not Production GO) |

Evidence: [evidence/wave12-migrate-prep/local-verify-2026-07-22T131700Z.json](./evidence/wave12-migrate-prep/local-verify-2026-07-22T131700Z.json); prior 0039-era gate log `evidence/wave12-gates/gate-rerun-2026-07-22T1307Z.log`.  
Head pin: **`0040`** — see [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) (0040 must be on any future staging/prod upgrade path; execution still **BLOCKED**).

Related: [PROGRESS-WAVE12-IMAGE.md](./PROGRESS-WAVE12-IMAGE.md), [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md).

---

## Still open (blocks GO)

1. Staging soak (Wave 11) + cloud backup/restore beyond local drill (Wave 10)  
2. Staging deploy/rollback **tabletop** (PROD-W12 acceptance)  
3. Full authenticated browser e2e beyond Wave 13 smoke  
4. Human CTO+TL GO signatures on [go-live-checklist.md](./runbooks/go-live-checklist.md)  
5. Production migrate + cutover — **forbidden until above close**

**Validation:** **light validated** for local gate run; **production no-go** unchanged.
