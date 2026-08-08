# Progress — Wave 11 (Staging parity + soak readiness)

**Date:** 2026-07-22  
**IDs:** PROD-W11-001 (parity), PROD-W11-002 (soak)  
**Product:** SalesOS  
**Owner scope:** Local/staging **path automation + evidence start** — no cloud staging deploy, no Production GO  
**Validation class:** **light validated** (local Docker gate + 4h evidence loop + 48h **in progress**) — **production no-go** unchanged  
**Soak status:** **NOT complete** — 4.0h extended local loop **DONE**; **48h local loop STARTED** (`2026-07-22T14:31:46Z`, PID `21856`); **48–72h claim remains OPEN**  
**48h plan / live:** [PROGRESS-WAVE11-SOAK-48H.md](./PROGRESS-WAVE11-SOAK-48H.md) — sequential after 4h; **in progress** (not complete)

---

## Summary

| Item | Outcome |
|------|---------|
| Gate script | Added `salesos/scripts/wave11-soak-gate.py` (+ `.ps1` wrapper) |
| Local gate run | **GATE PASS** @ 2026-07-22T07:56:25Z; re-gate **PASS** @ 2026-07-22T10:24:51Z |
| Short evidence loop | **DONE** (~0.2h / 5 iterations, 2026-07-22T08:24–08:36Z) — **not** 48h |
| Extended local loop (4h) | **DONE** — 45 iters, 16 hard-fail iters, exit `1` — **not** 48h |
| 48h local soak | **STARTED** — PID `21856`; start `2026-07-22T14:31:46Z`; expected end ~`2026-07-24T14:31:46Z` — [PROGRESS-WAVE11-SOAK-48H.md](./PROGRESS-WAVE11-SOAK-48H.md) |
| Evidence | `docs/audit/ga-engineering-audit/evidence/wave11-soak/` (4h); **live** 48h dir `evidence/wave11-soak-48h/` |
| Runbook | `runbooks/staging-soak.md` (local gate + 48–72h loop how-to + sequential note) |
| Cloud staging soak | **Not started** — `.env.staging` / GH Environment host **UNVERIFIED** |
| Production GO | **Not claimed** |
| `soak_complete_claim` | **false** (48h **in flight**, not complete; 72h still OPEN) |

---

## Extended soak evidence loop (2026-07-22) — DONE (4.0h)

**Does NOT claim PROD-W11-002 / 48–72h complete.** Remaining gap: **≥44h** toward 48h minimum (and **≥68h** toward 72h).

### Start command

```text
$env:PYTHONUNBUFFERED = "1"
python -u salesos/scripts/wave11-soak-gate.py --loop --interval 300 --duration-hours 4 --skip-alembic `
  --api http://localhost:8000 --fe http://localhost:3000 `
  --compose-dir salesos `
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak
```

| Field | Value |
|-------|-------|
| **SOAK_START_UTC** | `2026-07-22T10:25:06Z` |
| **SOAK_END_UTC** | `2026-07-22T14:25:46Z` |
| **Wall clock** | ~4.01h (`elapsed_ms` ≈ 14443586) |
| **Window** | `duration-hours=4.0`, `interval=300s` |
| **Iterations** | **45** (29 PASS / 16 FAIL) |
| **Loop exit** | **`1`** (hard failures present; no `--fail-soft`) |
| **Alembic** | `--skip-alembic`; SQL verify `alembic_version=0039` → `alembic-sql-verify-20260722T102440Z.json` |
| **Pre-gate** | oneshot GATE PASS → `gate-2026-07-22T102451Z.json` |
| **Summary evidence** | `loop-summary-2026-07-22T142544Z.json` (`soak_complete_claim: false`, `production_go_claim: false`) |
| **`soak_complete_claim`** | `false` |

### Failure pattern (honest)

Most hard fails were **transient `api.ping` timeouts** while `/health` / FE often still PASS. Notable multi-check stress:

| Iter | Hard fails |
|------|------------|
| i3, i13, i22, i24, i25, i34–i36, i39–i40, i44–i45 | `api.ping` (timeout) |
| i23 | `api.ping` + `api.health` + FE `/` `/copilot` `/analytics` (timeouts) |
| i28, i30 | `api.ping` + `api.health` |
| i29 | `api.health` |

Stack did **not** stay fully clean for 4h; treat as light soak evidence with latency/timeout noise — **not** a green 48h claim.

---

## 48h local soak (2026-07-22) — STARTED / NOT complete

**Does NOT claim PROD-W11-002 / 48–72h complete.** Details + monitoring: [PROGRESS-WAVE11-SOAK-48H.md](./PROGRESS-WAVE11-SOAK-48H.md).

| Field | Value |
|-------|-------|
| **SOAK_48H_START_UTC** | `2026-07-22T14:31:46Z` |
| **Expected end** | `2026-07-24T14:31:46Z` (approx) |
| **PID** | `21856` (detached `Start-Process` Hidden) |
| **Evidence** | `docs/audit/ga-engineering-audit/evidence/wave11-soak-48h/` |
| **Pre-gate** | `gate-2026-07-22T143121Z.json` (PASS) |
| **Alembic** | SQL verify `0040` + `--skip-alembic` |
| **Iter 1** | `loop-2026-07-22T143209Z-i00001.json` (`gate_pass: true`) |
| **`soak_complete_claim`** | `false` |

---

## Short soak evidence loop (2026-07-22)

**Does NOT claim PROD-W11-002 / 48–72h complete.**

### Start command

```text
# First attempt (alembic CLI hung under docker exec → iter1 FAIL on alembic):
python salesos/scripts/wave11-soak-gate.py --loop --interval 120 --duration-hours 0.2 ...

# Restarted with SQL-verified alembic head + skip CLI:
$env:PYTHONUNBUFFERED = "1"
python -u salesos/scripts/wave11-soak-gate.py --loop --interval 120 --duration-hours 0.2 --skip-alembic `
  --api http://localhost:8000 --fe http://localhost:3000 `
  --compose-dir salesos `
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak
```

**SOAK_RESTART_UTC:** `2026-07-22T08:24:27Z`  
**Window:** `duration-hours=0.2`, `interval=120s` → **5 iterations**  
**Loop exit:** `1` (1 hard failure: transient `/ping` timeout on iteration 4)  
**`soak_complete_claim`:** `false`

### Alembic note

`docker compose exec … alembic current` hung (multiple stuck processes). Compensating check:

- SQL: `alembic_version = 0039` → evidence `alembic-sql-verify-20260722T082427Z.json`  
- Loop used `--skip-alembic` after that verify

### Evidence files (first N + summary)

| File | Role |
|------|------|
| `gate-2026-07-22T075429Z.json` | Earlier oneshot (transient `/health` timeout) |
| `gate-2026-07-22T075625Z.json` | Earlier oneshot **GATE PASS** |
| `loop-2026-07-22T081519Z-i00001.json` | First loop attempt (alembic FAIL) |
| `alembic-sql-verify-20260722T082427Z.json` | SQL head verify |
| `loop-2026-07-22T082528Z-i00001.json` | Loop PASS |
| `loop-2026-07-22T082809Z-i00002.json` | Loop PASS |
| `loop-2026-07-22T083055Z-i00003.json` | Loop PASS |
| `loop-2026-07-22T083359Z-i00004.json` | Loop FAIL (`api.ping` timeout; health OK) |
| `loop-2026-07-22T083630Z-i00005.json` | Loop PASS |
| `loop-summary-2026-07-22T083630Z.json` | Summary (`failures=1`, `soak_complete_claim=false`) |

---

## Deliverables

### 1. Readiness gate script

**Path:** `salesos/scripts/wave11-soak-gate.py`  
**Wrapper:** `salesos/scripts/wave11-soak-gate.ps1`

Automates:

1. `/ping`, `/health`, `/health/detailed`
2. Alembic `current == heads` via `docker compose exec`
3. `demo_mode` / `feature_ai_copilot` via backend Settings
4. Redis/cache from health payload
5. FE HTTP 200 for `/`, `/copilot`, `/analytics`
6. Optional `--loop` for 48–72h evidence collection (does **not** auto-declare soak pass)

### 2. Local Docker gate results (executed)

Command:

```text
python salesos/scripts/wave11-soak-gate.py --api http://localhost:8000 --fe http://localhost:3000 --compose-dir salesos --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak
```

| Check | Result |
|-------|--------|
| api.ping | PASS |
| api.health | PASS (HTTP 200, status=ok) |
| api.health_detailed | PASS (healthy) |
| api.redis_cache | PASS (cache=connected, redis=connected) |
| alembic.current_eq_heads | PASS (`0039` == `0039`) |
| flags.demo_and_copilot | PASS (`False` / `False`, env=development) |
| fe `/`, `/copilot`, `/analytics` | PASS (200) |

**Evidence file:** `docs/audit/ga-engineering-audit/evidence/wave11-soak/gate-2026-07-22T075625Z.json`

**Earlier attempt (same day):** `gate-2026-07-22T075429Z.json` — `/health` timed out once (transient); detailed + FE OK. Gate hardened with retries + detailed fallback for redis/cache.

### 3. Runbook update

`docs/audit/ga-engineering-audit/runbooks/staging-soak.md` now includes:

- Automated gate usage
- **Local gate executed** section with honest classification
- How to run 48–72h loop / cron without claiming soak complete
- Local ↔ staging compose **parity gaps** (config review only)

---

## Parity gaps (local vs `infra/staging/docker-compose.staging.yml`)

Safe review only — staging stack **not** started (secrets / cloud host not assumed):

| Gap | Note |
|-----|------|
| Secrets | Staging requires `.env.staging` (not in git) |
| Debug/reload | Staging backend `--reload` + `SALESOS_DEBUG=true` — not prod-like for soak |
| Env label | Local observed `env=development` vs staging `SALESOS_ENV=staging` |
| Migrations service | Present in staging compose; absent as sidecar in local compose |
| Image digests | GHCR promotion path in workflow; local builds context — **digest parity UNVERIFIED** |
| Monitoring pins | Staging pins Prometheus/Grafana versions; local often `:latest` |
| Cloud host | Staging GitHub Environment runner/host existence **UNVERIFIED** |

---

## Still UNVERIFIED

- Real cloud staging hostname / deploy execution  
- Staging↔production **image digest** match  
- Staging Alembic / flags / redis on remote host  
- Alert rules actually scraped on staging  
- **48–72h continuous soak** + signed Soak Report (short + **4h done**; 48h **STARTED in flight** — [PROGRESS-WAVE11-SOAK-48H.md](./PROGRESS-WAVE11-SOAK-48H.md); claim still **false**)  
- Authenticated GA API paths under soak traffic  
- Optional k6 / `soak-test.py` load (needs approval)  
- Production GO / GA readiness scores  

---

## Commands run

| Command | Outcome |
|---------|---------|
| `docker ps` (salesos stack) | Backend/FE/postgres/redis/neo4j/… up |
| Manual `/health`, `/health/detailed`, FE routes | 200 (health occasionally slow) |
| `docker compose exec backend alembic current/heads` | `0039 (head)` |
| Settings probe (`demo_mode`, `feature_ai_copilot`) | both False |
| `python …/wave11-soak-gate.py` (oneshot) | exit 0 GATE PASS |
| `python … --loop --duration-hours 4 --skip-alembic` | exit **1**; 45 iters; 16 fails; summary filed |
| SQL `alembic_version` (pre-4h) | `0039` (CLI skipped) |
| SQL `alembic_version` (pre-48h) | `0040` → `wave11-soak-48h/alembic-sql-verify-20260722T143100Z.json` |
| oneshot gate → `wave11-soak-48h/` | exit 0 GATE PASS (`gate-2026-07-22T143121Z.json`) |
| `Start-Process` 48h `--loop --interval 300 --skip-alembic` | **running** PID `21856`; start `2026-07-22T14:31:46Z` |

Heavy npm build/lint/test: **not run** (low-load protocol). No production migrate. No commit.

---

## Honesty labels

| Claim | Status |
|-------|--------|
| Local readiness gate | **light validated** |
| Short local evidence loop (~12 min / 5 iters) | **light validated** (1 transient ping fail) |
| Extended 4h local loop | **light validated** (45 iters; 16 hard-fail iters, mostly `/ping` timeouts) |
| 48–72h soak | **not complete** — 48h **in progress** (`soak_complete_claim: false`) |
| Staging cloud parity | **UNVERIFIED** |
| Production GO | **production no-go** (unchanged) |
