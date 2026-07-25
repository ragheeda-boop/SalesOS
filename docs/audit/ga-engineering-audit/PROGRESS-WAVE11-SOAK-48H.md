# Progress — Wave 11 · 48h local soak plan (PROD-W11-002)

**Date:** 2026-07-22 (checkpoint **2026-07-24T13:11Z**)  
**IDs:** PROD-W11-002 (soak)  
**Product:** SalesOS on AQLIYA  
**Status:** **IN PROGRESS** — 48h local loop **RUNNING** / **NOT complete** (~**46.7h** wall-clock elapsed of 48h)  
**`soak_complete_claim`:** **false**  
**Production GO:** **Not claimed**  
**Prerequisite:** The **4.0h** extended loop has **finished** ([PROGRESS-WAVE11-SOAK.md](./PROGRESS-WAVE11-SOAK.md): exit 1, 45 iters). 48h started after that window — **do not** claim GO from local evidence alone.

---

## Why sequential (not parallel)

| Constraint | Guidance |
|------------|----------|
| Local stack load | One `wave11-soak-gate.py --loop` at a time |
| Evidence clarity | Separate evidence dir for 48h vs short/4h samples |
| Honest duration | Wall-clock **≥48h** continuous; 4h does **not** count as 48h |
| Cloud staging | Still **UNVERIFIED** — this plan is **local Docker** only unless staging host is later confirmed |

---

## When to start

1. Confirm 4h loop has exited — **DONE** (`loop-summary-2026-07-22T142544Z.json`, `SOAK_END_UTC=2026-07-22T14:25:46Z`, exit 1).  
2. ~~Do not kill PID of a healthy in-flight 4h run.~~ (complete)  
3. Summarize 4h honestly in [PROGRESS-WAVE11-SOAK.md](./PROGRESS-WAVE11-SOAK.md) — **DONE**.  
4. Then start 48h with commands below (human/agent decision; still `soak_complete_claim: false` until ≥48h wall-clock + soak report).

**Expected 4h end (approx):** `2026-07-22T14:25:06Z` (± interval sleep).

---

## Evidence directory (48h)

Use a **dedicated** folder so short/4h artifacts are not confused with the GO-required window:

```text
docs/audit/ga-engineering-audit/evidence/wave11-soak-48h/
```

Optional: keep a one-line pointer file in `evidence/wave11-soak/README-48H.txt` linking here after start.

---

## Start commands (after 4h ends)

### PowerShell (repo root)

```powershell
# Ensure SalesOS local stack is up (backend :8000, FE :3000)
cd "C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide"

# Optional: SQL-verify alembic head once, then skip CLI hang risk
# docker compose -f salesos/docker-compose.yml exec -T postgres `
#   psql -U salesos -d salesos -c "SELECT version_num FROM alembic_version;"

New-Item -ItemType Directory -Force -Path "docs\audit\ga-engineering-audit\evidence\wave11-soak-48h" | Out-Null

$env:PYTHONUNBUFFERED = "1"
python -u salesos/scripts/wave11-soak-gate.py --loop --interval 300 --duration-hours 48 --skip-alembic `
  --api http://localhost:8000 --fe http://localhost:3000 `
  --compose-dir salesos `
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak-48h
```

### Notes

- `--interval 300` → ~576 iterations over 48h (light synthetic; not load soak).  
- `--skip-alembic` only after a same-day SQL/`alembic current` verify is filed under evidence.  
- Do **not** pass `--fail-soft` for the GO candidate run unless TL explicitly accepts continued collection after hard fails (still not a soak pass).  
- Heavier `soak-test.py` / k6: **optional**, needs explicit approval (low-load protocol).

### Started (2026-07-22) — live fields

**Backgrounding:** `Start-Process python … -WindowStyle Hidden` with stdout/stderr redirected under the evidence dir (detached from agent shell).

```powershell
$env:PYTHONUNBUFFERED = "1"
# Actual launch used Start-Process (PID below); equivalent CLI:
python -u salesos/scripts/wave11-soak-gate.py --loop --interval 300 --duration-hours 48 --skip-alembic `
  --api http://localhost:8000 --fe http://localhost:3000 `
  --compose-dir salesos `
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak-48h
```

| Field | Value |
|-------|-------|
| **SOAK_48H_START_UTC** | `2026-07-22T14:31:46Z` |
| **Expected end (approx)** | `2026-07-24T14:31:46Z` (± interval sleep / wall clock) |
| **PID** | `21856` |
| **Pre-gate oneshot** | `evidence/wave11-soak-48h/gate-2026-07-22T143121Z.json` (GATE PASS, exit 0) |
| **Alembic verify** | SQL `alembic_version=0040` → `evidence/wave11-soak-48h/alembic-sql-verify-20260722T143100Z.json`; loop uses `--skip-alembic` |
| **First iteration** | `loop-2026-07-22T143209Z-i00001.json` (`gate_pass: true`) |
| **Logs** | `soak-48h-stdout.log` / `soak-48h-stderr.log` |
| **Pointer** | `evidence/wave11-soak/README-48H.txt` |
| **`soak_complete_claim`** | `false` until ≥48h wall-clock + human Soak Report |

**Pre-start health (light):** API `/health`+`/ping` 200; FE `/`, `/copilot`, `/analytics` 200; no prior `wave11-soak` process. Note: `kafka` container was Restarting at start; API reported `kafka=in_memory` / `graph=unavailable` — not treated as start blockers for this gate.

---

## Monitoring (during 48h)

| Cadence | Action |
|---------|--------|
| Every ~5–15 min (optional) | Confirm new `loop-*-iNNNNN.json` appears under `evidence/wave11-soak-48h/` |
| Hourly | Spot-check last iteration `gate_pass` / `hard_fails` |
| Daily | Count PASS vs FAIL; note multi-check outages |
| On host sleep/reboot | Treat as soak interrupt — restart **new** 48h window or EXTEND with TL note (do not stitch silently) |
| Process alive | `Get-CimInstance Win32_Process` where CommandLine matches `wave11-soak-gate` + `duration-hours 48` |

### Quick status snippet

```powershell
$ev = "docs\audit\ga-engineering-audit\evidence\wave11-soak-48h"
Get-ChildItem $ev -Filter "loop-*-i*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 3 Name, LastWriteTime
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'duration-hours 48' -and $_.CommandLine -match 'wave11-soak' } |
  Select-Object ProcessId
```

### Checkpoint — 2026-07-23T07:15Z (agent item 5)

| Field | Value |
|-------|-------|
| **Process** | **ALIVE** — PID `21856` (`python` `wave11-soak-gate.py --duration-hours 48 --skip-alembic`) |
| **Wall-clock** | ~**16.7h** elapsed of 48h; expected end still `2026-07-24T14:31:46Z` |
| **Iterations** | **190** (`loop-*-i*.json`); latest `loop-2026-07-23T071459Z-i00190.json` |
| **PASS / FAIL** | **142 PASS** / **48 FAIL** (~**25.3%** fail rate) |
| **No `loop-summary-*`** | Correct — window not finished |
| **`soak_complete_claim`** | **false** (not ≥48h; do not claim) |
| **Hard-fail mix (approx)** | `api.ping` dominant (~42); also `api.health`, FE routes |
| **Max consecutive FAIL** | **6** (seen earlier in window) |
| **Recent (last 20)** | 18 PASS / 2 FAIL — still writing; primary stack **not** killed |
| **Threshold note** | Fail rate **≥5%** → human **Review / EXTEND** per table below; loop left **RUNNING** (no silent restart; no Production GO) |
| **Next check** | ~**2026-07-23T13:15Z** (≈6h) or sooner if PID dies / evidence stalls &gt;15 min |

### Checkpoint — 2026-07-24T13:11Z (pre-end)

| Field | Value |
|-------|-------|
| **Process** | **ALIVE** — PID `21856` (`python` `wave11-soak-gate.py --duration-hours 48 --skip-alembic` → `evidence/wave11-soak-48h/`) |
| **Wall-clock** | ~**46.7h** elapsed of 48h (~**1.3h** remaining); expected end still `2026-07-24T14:31:46Z` |
| **Iterations** | **529** (`loop-*-i*.json`); latest `loop-2026-07-24T130753Z-i00529.json` |
| **PASS / FAIL** | **418 PASS** / **111 FAIL** (~**21.0%** fail rate; stdout `failures so far=111`) |
| **No `loop-summary-*`** | Correct — window not finished |
| **`soak_complete_claim`** | **false** (not ≥48h; no human Soak Report; do not claim) |
| **Latest hard-fail** | Iter 529: `api.ping` TimeoutError (~10s); `api.health` + FE routes still PASS |
| **Note** | Separate PID `26064` also running against `evidence/wave11-soak-48h-rerun/` — **not** this primary window; do not merge evidence |
| **Threshold note** | Fail rate **≥5%** → human **Review / EXTEND**; loop left **RUNNING** (no restart; process not dead; no Production GO) |
| **Next check** | After expected end (~`2026-07-24T14:31:46Z`) for `loop-summary-*.json` + exit code, or sooner if PID dies / evidence stalls &gt;15 min |

---

## Failure thresholds (human soak decision)

Script exits non-zero if any iteration hard-fails (unless `--fail-soft`). That alone is **not** the Soak Report. Humans apply:

| Severity | Threshold (local candidate) | Action |
|----------|----------------------------|--------|
| **FAIL soak** | New **P0** security/regression during window | Stop; file FAIL Soak Report |
| **FAIL soak** | Sustained outage: **≥3 consecutive** iterations with `api.health` hard FAIL, or FE all-routes FAIL for **≥15 minutes** wall-clock | Investigate; default FAIL unless TL documents root cause + restart |
| **FAIL / EXTEND** | Alembic drift (`current != heads`) if alembic checks enabled | FAIL until repaired |
| **Review / EXTEND** | Transient single-check fails (e.g. intermittent `/ping` timeout) **&lt; 5%** of iterations and self-recover | Note in report; may CONTINUE |
| **Review / EXTEND** | Failure rate **≥ 5%** of iterations OR any multi-service simultaneous fail (API+FE together) | Require TL review before CONTINUE |
| **FAIL soak** | `demo_mode=True` or `feature_ai_copilot=True` observed | FAIL (AI honesty / soak candidate) |

Alert/SLO context: `docs/ops/SLO_ALERTS.md`, `salesos/infra/monitoring/alerts.yml` — staging scrape still **UNVERIFIED**.

---

## After 48h completes

1. Confirm `loop-summary-*.json` exists with `"soak_complete_claim": false` (script never auto-claims).  
2. File human Soak Report (template in [runbooks/staging-soak.md](./runbooks/staging-soak.md)).  
3. Update this file + [PROGRESS-WAVE11-SOAK.md](./PROGRESS-WAVE11-SOAK.md) + [GA_STATUS.md](./GA_STATUS.md).  
4. Still required for GO path: cloud staging soak/parity if PRODUCTION_PLAN demands it; CTO/TL signatures remain separate ([SIGN_HERE.md](./SIGN_HERE.md)).

**Do not** mark PROD-W11-002 complete from agent docs alone.

---

## Honesty labels

| Claim | Status |
|-------|--------|
| 48h plan documented | **DONE** (this file) |
| 48h loop started (local) | **IN PROGRESS** (PID 21856; start `2026-07-22T14:31:46Z`; checkpoint `2026-07-24T13:11Z`: 529 iters, 418 PASS / 111 FAIL) |
| 48h wall-clock executed | **not complete** (~46.7h / 48h in flight; ~1.3h remaining) |
| 48–72h soak complete | **false** |
| Production GO | **production no-go** |
