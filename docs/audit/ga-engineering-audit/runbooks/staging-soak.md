# Staging Soak Runbook (Wave 11 — PREPARE + LOCAL GATE)

**ID:** PROD-W11-001 / PROD-W11-002  
**Status:** Local readiness tooling **DONE**; **cloud 72h soak IN PROGRESS** (started 2026-08-07; claim **false** — see [../completion/SOAK-PROGRESS-SNAPSHOT-2026-08-08.md](../completion/SOAK-PROGRESS-SNAPSHOT-2026-08-08.md)); **48–72h NOT complete**  
**48h plan:** [../PROGRESS-WAVE11-SOAK-48H.md](../PROGRESS-WAVE11-SOAK-48H.md)  
**Restart/status:** [ops01-soak-restart.ps1](./ops01-soak-restart.ps1)  
**Classification:** Operational prep; does **not** grant Production GO

---

## Purpose

1. Establish staging ↔ production **parity** (images, schema, flags, monitoring).  
2. Run **48–72 hours** soak with light synthetic traffic and no new P0 incidents.

---

## Staging deploy path (evidence)

| Artifact | Path / note |
|----------|-------------|
| Staging workflow | `salesos/.github/workflows/deploy-staging.yml` |
| Staging compose | `salesos/infra/staging/docker-compose.staging.yml` |
| Staging env file | `.env.staging` (secrets — **do not commit**) |
| Health check in CI | `http://localhost:8000/health` (workflow `HEALTH_ENDPOINT`) |
| Production contrast | `deploy-production.yml` → K8s/`infra/k8s` + GHCR |
| **Readiness gate script** | `salesos/scripts/wave11-soak-gate.py` (+ `wave11-soak-gate.ps1`) |

**يحتاج تحقق:** That staging GitHub Environment runners and hosts actually exist and are managed. **No cloud staging deploy was performed in this Wave 11 local gate pass** (no safe staging credentials assumed).

---

## Automated readiness gate (run this first)

One-shot parity / smoke gate (stdlib Python + optional `docker compose exec`):

```powershell
# From repo root (Windows) — local Docker stack must already be up
python salesos/scripts/wave11-soak-gate.py `
  --api http://localhost:8000 `
  --fe http://localhost:3000 `
  --compose-dir salesos `
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak

# Or:
.\salesos\scripts\wave11-soak-gate.ps1
```

```bash
# Linux/macOS
python salesos/scripts/wave11-soak-gate.py \
  --api http://localhost:8000 \
  --fe http://localhost:3000 \
  --compose-dir salesos \
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak
```

**Checks performed**

| Check | Source |
|-------|--------|
| `/ping`, `/health`, `/health/detailed` | Backend HTTP |
| Redis/cache connected | `/health` (fallback: detailed) |
| Alembic `current` == `heads` | `docker compose exec backend alembic …` |
| `demo_mode` / `feature_ai_copilot` | Settings inside backend container |
| FE `/`, `/copilot`, `/analytics` HTTP 200 | Frontend HTTP |

Exit `0` = readiness **GATE PASS** only. It is **not** a soak pass and **not** Production GO.

Evidence JSON lands under `docs/audit/ga-engineering-audit/evidence/wave11-soak/`.

---

## Local gate executed (2026-07-22)

| Field | Value |
|-------|--------|
| Environment | Local Docker (`salesos/docker-compose.yml`) — **not** cloud staging |
| Timestamp (UTC) | 2026-07-22T07:56:25Z |
| Evidence | `docs/audit/ga-engineering-audit/evidence/wave11-soak/gate-2026-07-22T075625Z.json` |
| Result | **GATE PASS** (9/9 PASS) |
| Alembic | Gate-day: `current=0039` == `heads=0039`. **Current head = `0040`** — [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](../PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) |
| Flags | `demo_mode=False`, `feature_ai_copilot=False`, `env=development` |
| Redis/cache | connected |
| FE routes | `/`, `/copilot`, `/analytics` → 200 |
| Prior attempt | `gate-2026-07-22T075429Z.json` — `/health` TimeoutError (transient); detailed + FE still OK |

**Classification:** light validated (local stack). **production no-go** unchanged. **48–72h soak: not started.**

### Live 4h extended loop (2026-07-22) — do not kill

See [../PROGRESS-WAVE11-SOAK.md](../PROGRESS-WAVE11-SOAK.md). Prefer **sequential** 48h after this exits (avoid double load). Do **not** start a second `--loop` while PID for `--duration-hours 4` is alive.

---

## How to run 48–72h soak evidence loop (without claiming complete)

The gate script supports a light synthetic loop that **collects evidence only**. A human must still file the Soak Report template below before claiming PROD-W11-002.

**Full 48h local plan (monitoring, thresholds, evidence dir):** [../PROGRESS-WAVE11-SOAK-48H.md](../PROGRESS-WAVE11-SOAK-48H.md).

### Option A — Python loop (preferred) — start **after** 4h ends

```powershell
# 48h @ 5-minute interval — dedicated evidence dir (do not mix with short/4h samples)
# Prefer sequential: wait until 4h loop exits (no parallel second loop on local Docker)
New-Item -ItemType Directory -Force -Path "docs\audit\ga-engineering-audit\evidence\wave11-soak-48h" | Out-Null
$env:PYTHONUNBUFFERED = "1"
python -u salesos/scripts/wave11-soak-gate.py `
  --api http://localhost:8000 `
  --fe http://localhost:3000 `
  --compose-dir salesos `
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak-48h `
  --loop --interval 300 --duration-hours 48 --skip-alembic
```

For 72h: `--duration-hours 72`. Use `--fail-soft` only if you want the process to keep writing evidence after hard fails (still **not** a soak pass).

**Failure thresholds (human decision):** see PROGRESS-WAVE11-SOAK-48H (≥3 consecutive `api.health` fails / ≥5% iter fail rate → review or FAIL; new P0 → FAIL; flags True → FAIL).

### Option B — cron / Task Scheduler wrapping one-shot

```bash
# Every 5 minutes — Linux cron example (staging host UNVERIFIED)
*/5 * * * * cd /path/to/Muhide && python salesos/scripts/wave11-soak-gate.py \
  --api "$STAGING_API" --fe "$STAGING_FE" --compose-dir salesos \
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak \
  >> /var/log/salesos-soak-gate.log 2>&1
```

Windows Task Scheduler: run `wave11-soak-gate.ps1` every 5 minutes for ≥ 48 hours; archive evidence folder.

### Option C — existing load soak (optional, heavier)

`salesos/scripts/soak-test.py` is a **load** soak (default multi-hour moderate traffic). It needs approval for staging and is **optional** per PRODUCTION_PLAN (k6/full load optional). Prefer the light gate loop for PROD-W11-002 unless TL approves load.

### Stop conditions (fail soak)

- New P0 security/regression  
- Sustained `/health` failure / alembic drift  
- Error-rate breach per `docs/ops/SLO_ALERTS.md` / `infra/monitoring/alerts.yml` (**alert scrape on staging: UNVERIFIED**)

**Do not** mark PROD-W11-002 complete until duration elapsed **and** Soak Report signed.

---

## Parity checklist (PROD-W11-001)

| Dimension | Staging | Production | Match? |
|-----------|---------|------------|--------|
| Image digest (backend) | GHCR tag from workflow SHA | Same SHA promoted | ☐ **UNVERIFIED** (no cloud deploy this pass) |
| Image digest (frontend) | same | same | ☐ **UNVERIFIED** |
| Alembic `current` | must equal `heads` | must equal `heads` | ☑ local Docker: head **`0040`** (was 0039 at gate-day). Cloud staging: **UNVERIFIED** |
| `DEMO_MODE` | false for soak candidate | false | ☑ local Settings `demo_mode=False`. Cloud staging: **UNVERIFIED** |
| `feature_ai_copilot` | **False** (AI honesty) | **False** | ☑ local `False`. Cloud staging: **UNVERIFIED** |
| Redis / Neo4j / Kafka | per signed degraded matrix | same | ☑ local redis connected; kafka `in_memory` (GA degraded). Cloud: **UNVERIFIED** |
| Observability stack | root vs salesos compose split-brain risk | K8s monitoring manifests | ☐ Wave 8; staging compose includes Prometheus/Grafana — **runtime scrape UNVERIFIED** |
| Secrets source | GH / env files | GH `environment: production` | ☐ Wave 9; `.env.staging` not committed |

Fill cloud rows during real staging execution; do not invent green checkmarks.

### Local compose ↔ staging compose parity gaps (config review)

Safe static comparison of `salesos/docker-compose.yml` vs `salesos/infra/staging/docker-compose.staging.yml` (no staging stack started — `.env.staging` secrets not assumed present):

| Gap | Local | Staging compose | Risk for soak |
|-----|-------|-----------------|---------------|
| Env file | `.env` | `.env.staging` (required) | Cannot bring up staging compose without secrets |
| Backend debug / reload | uvicorn no `--reload` | `SALESOS_DEBUG=true` + `--reload` | Staging less production-like |
| Env name | `development` (observed) | `SALESOS_ENV=staging` | Expected; do not treat local as staging |
| Migrations | No dedicated migrations service | `migrations` service `alembic upgrade head` | Staging path clearer for migrate-before-app |
| Image source | build context / `salesos-frontend:local` | Workflow pushes GHCR; compose still `build:` | Digest promotion **UNVERIFIED** until GHCR pins used |
| Monitoring image pins | Prometheus/Grafana often `:latest` | Pinned tags (e.g. prometheus v3.3.0, grafana 11.6.0) | Local ≠ staging pin discipline |
| Extras | schema-registry (+ kafdrop profile) | No schema-registry | Local has extra surface |
| Postgres port wiring | App defaults to **5432** direct (PgBouncer hang note) | Via `.env.staging` | Confirm staging uses same pool strategy |

---

## Soak procedure (PROD-W11-002)

### Duration

- Minimum **48 hours**; target **72 hours** continuous.

### Traffic (light)

Prefer the readiness gate loop above; full k6 load is **optional** and needs approval:

```bash
# Examples — adjust host to staging URL (UNVERIFIED hostname)
curl -sf "$STAGING_API/ping" || curl -sf "$STAGING_API/health"
curl -sf "$STAGING_API/health/detailed" | jq .
# Authenticated GA paths — requires staging credentials (do not paste secrets into docs)
```

Suggested cadence: synthetic check every 1–5 minutes via gate `--loop`, CI cron, or monitoring blackbox (**UNVERIFIED** if blackbox is live).

### Watch

| Signal | Source | Action if breach |
|--------|--------|------------------|
| 5xx rate | Prometheus / logs | Open incident; stop soak promotion |
| `/health` latency | logs (local saw intermittent timeout) | Investigate; note in soak report |
| DB connections / pool | exporter | Scale or fix leaks |
| Alembic drift | `alembic current` vs `heads` | Fail soak |
| New P0 security/regression | manual + tests | Fail soak |

Alert rules reference: `salesos/infra/monitoring/alerts.yml` — **يحتاج تحقق** that rules are scraped on staging.

### Change freeze

- No feature merges into soak candidate without TL approval.
- Hotfixes only for P0/P1 blockers.

---

## Soak report template (create when executed)

```markdown
# Soak Report — YYYY-MM-DD
- Environment:
- Image digests:
- Duration:
- Incidents (P0/P1/P2):
- Error rate summary:
- Decision: CONTINUE / FAIL / EXTEND
- Sign-off:
```

---

## Acceptance

| Criterion | Status |
|-----------|--------|
| Parity table filled | **Partial** — local rows filled; cloud staging/prod digests **UNVERIFIED** |
| Readiness gate script + local execution | **Done** (2026-07-22) |
| 48–72h without new P0 | **Pending** — 4h in progress; 48h not started ([PROGRESS-WAVE11-SOAK-48H.md](../PROGRESS-WAVE11-SOAK-48H.md)) |
| Report filed | **Pending** |

**This runbook alone is not a soak pass.**  
**Local GATE PASS is not Production GO.**
