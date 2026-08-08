# Migration Dress Rehearsal — Non-Prod ONLY Runbook

**Stream:** E (Migration Dress) — SalesOS Completion Program  
**Date:** 2026-08-08  
**Product:** SalesOS  
**Charter:** [COMPLETION-PROGRAM.md](../COMPLETION-PROGRAM.md)  
**Risk SoT:** [PROD-MIGRATION-RISK.md](../PROD-MIGRATION-RISK.md)  
**Prod cutover (reference only — do NOT execute here):** [PRODUCTION-CUTOVER-PACKAGE.md](../PRODUCTION-CUTOVER-PACKAGE.md)

**Principle:** AI assists. Humans decide. Evidence governs.

---

## 0. Hard forbidden list

| Action | Status |
|--------|--------|
| `alembic upgrade` / `downgrade` against **production** | **FORBIDDEN** |
| Railway prod migrate / `railway connect` / prod tunnel migrate | **FORBIDDEN** |
| Any write to Railway production Postgres | **FORBIDDEN** |
| Claiming rehearsal **PASS** without recorded non-prod evidence | **FORBIDDEN** |
| Equating this runbook with evidence-based Production GO | **FORBIDDEN** |

This document is a **dress-rehearsal** procedure for **local Docker** and/or **staging DB copies** only. It does **not** authorize cutover.

---

## 1. Scope

| Field | Value |
|-------|-------|
| Rehearsal range | `d1a8c35e7f09` → `e5f9a32b0c08` (15 revisions) — see risk doc |
| Highest risk revision | `a4f7c29e1b80` (≤37 non-`CONCURRENTLY` indexes) |
| Allowed targets | Local `salesos/docker-compose.yml` Postgres · staging / scratch DB **explicitly labeled non-prod** |
| Disallowed targets | Railway production · any URL whose host is prod · unknown `DATABASE_URL` |
| Rollback preference | Restore from **pre-rehearsal dump**; not multi-step Alembic downgrade |
| Validation vocabulary | AGENTS.md labels only |

---

## 2. Environment identity gate (must pass before any write)

Record answers; **abort if any fail**.

| # | Check | Pass criteria | How |
|---|-------|---------------|-----|
| G1 | Compose project is local | Services named `salesos-*`; ports on localhost | `docker compose ps` in `salesos/` |
| G2 | `DATABASE_URL` host | Host is `postgres` (compose DNS) or local staging hostname — **not** Railway prod | Sanitized print (`sed` credentials) |
| G3 | App env | `ENVIRONMENT` / `ENV` ∈ `{development, staging, test}` — **not** `production` | `printenv` in backend container |
| G4 | No Railway prod markers | `RAILWAY_ENVIRONMENT` unset **or** explicitly staging; no prod project tunnel | `printenv RAILWAY_ENVIRONMENT` |
| G5 | Operator intent | Written note: “non-prod dress rehearsal only” | Human ack in evidence folder |

**If G1–G4 cannot be proven → stop. Document `Blocked-Wall` or identity failure. Do not migrate.**

---

## 3. Read-only probe (always safe on non-prod)

Run from `salesos/` when Docker is up.

### 3.1 Docker availability

```powershell
cd salesos
docker compose ps
docker info --format "{{.ServerVersion}}"
```

| Outcome | Disposition |
|---------|-------------|
| Compose services Up (esp. `postgres`, `backend`) | Proceed to §3.2 |
| Docker daemon down / compose missing | **Blocked-Wall** — keep this runbook; do not invent PASS |

### 3.2 Schema revision (CLI restored 2026-08-08 W2; SQL still valid)

**W2 fix:** Eager imports in `app/__init__.py` (full FastAPI stack) + Alembic `env.py` importing `app.database` (engine create at import) caused Docker CLI hangs. Package init is now light; `env.py` imports `app.common.models.Base` only. Verified: `alembic current` / `check_alembic_head.py` exit 0 on local compose (~15–30s). Prefer SQL if CLI regresses:

```powershell
# Read-only — local compose Postgres
docker compose exec -T postgres psql -U salesos -d salesos -c "SELECT version_num FROM alembic_version;"
```

Optional (may hang — use timeout / kill if stuck >60s):

```powershell
docker compose exec -T backend alembic current
docker compose exec -T backend alembic heads
docker compose exec -T backend python scripts/check_alembic_head.py
```

`scripts/check_alembic_head.py` is **read-only** (never upgrades). Exit 0 iff `current == heads`.

### 3.3 Probe interpretation

| Observation | Meaning | Next |
|-------------|---------|------|
| `version_num == e5f9a32b0c08` | Local DB **already at tip** | Full path upgrade rehearsal **not applicable** until restore to baseline (§4) |
| `version_num == d1a8c35e7f09` | Ideal rehearsal start | May proceed to §4–§5 **after** dump |
| Other / multi-head | Drift / unexpected | Stop; investigate; do not upgrade blindly |
| CLI hang, SQL OK | Tooling Partial | Document hang; trust SQL for current pin |

---

## 4. Pre-rehearsal dump (required before any non-prod upgrade)

**Only** when operator intends to run `alembic upgrade` on a **non-prod** copy.

```powershell
$stamp = Get-Date -Format "yyyyMMddTHHmmssZ"
$out = "..\docs\audit\ga-engineering-audit\completion\evidence\migration-dress-$stamp.sql"
# Adjust path as needed; do not commit dumps with secrets/PII without scrub policy
docker compose exec -T postgres pg_dump -U salesos -d salesos --no-owner --format=plain > $out
```

Record: dump path, size, `version_num` before dump, UTC time.

**Do not** skip dump “because local.” Restore is the rehearsal rollback path.

---

## 5. Optional upgrade dress rehearsal (NON-PROD write)

**Preconditions:** §2 gates pass · §4 dump exists · human explicitly wants upgrade practice · DB not already at tip (or restored to `d1a8c35e7f09`).

### 5.1 Restore-to-baseline (if currently at tip)

To rehearse the **15-revision path**, restore a dump taken at `d1a8c35e7f09`, **or** restore a labeled staging scratch clone at that pin. Do **not** invent a baseline by destructive prod copy without approval.

### 5.2 Upgrade (local backend → local Postgres only)

```powershell
# CONFIRM: DATABASE_URL host is compose `postgres` / staging scratch
docker compose exec -T backend alembic upgrade e5f9a32b0c08
# or: alembic upgrade head  — only if heads == e5f9a32b0c08 on this image
```

Watch wall clock especially around `a4f7c29e1b80`. Capture full stdout to evidence file.

### 5.3 Post-upgrade verify (read-only)

```powershell
docker compose exec -T postgres psql -U salesos -d salesos -c "SELECT version_num FROM alembic_version;"
# Expect: e5f9a32b0c08

# Spot checks aligned with cutover package T+1 (non-prod):
docker compose exec -T postgres psql -U salesos -d salesos -c "\dt sync_runs*"
docker compose exec -T postgres psql -U salesos -d salesos -c "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname IN ('external_system_connections','field_mapping_configs','sync_runs','conflict_resolution_policies');"
```

Optional smoke: `GET http://localhost:8000/health` — local only.

### 5.4 Rehearsal PASS criteria (all required)

A rehearsal may be labeled **PASS** only if **all** are true and evidenced:

1. Identity gates G1–G4 recorded as pass  
2. Pre-upgrade dump ID recorded  
3. Upgrade exit code **0** on **non-prod** target  
4. Post `version_num == e5f9a32b0c08`  
5. No production / Railway prod commands in the evidence trail  
6. Timing note for `a4f7c29e1b80` captured (even if approximate)

Anything less → **Partial** / **not validated** / **Blocked-Wall** — never shop as PASS.

---

## 6. Abort / restore (non-prod)

| Condition | Action |
|-----------|--------|
| Wrong env detected mid-run | **STOP** immediately; do not continue |
| Upgrade non-zero exit | Restore from §4 dump; do not chain-fix under uncertainty |
| Lock wait excessive on local | Cancel backend; restore dump; resize expectations for prod window |
| Operator unsure of URL | Treat as prod-risk → **STOP** |

```powershell
# Example restore (local) — after confirming target is non-prod
Get-Content .\path\to\pre-rehearsal.dump.sql | docker compose exec -T postgres psql -U salesos -d salesos
```

Policy: prefer restore over `alembic downgrade` ([runbooks/deploy-rollback.md](../runbooks/deploy-rollback.md)).

---

## 7. Staging cloud variant (when host exists)

When a **real staging** DB/host is available (Human-Gate today for cloud GH Environments):

1. Repeat §2 identity gates against **staging** labels only  
2. Dump / snapshot staging before upgrade  
3. Run same revision range via staging migrate runner / backend  
4. Save evidence under `completion/evidence/` or EAB evidence tree  
5. Still **FORBIDDEN:** production package § T-0 migrate commands  

Until staging host exists: document **Human-Gate** for cloud staging; local compose remains the available rehearsal surface.

---

## 8. Evidence template

Save under `docs/audit/ga-engineering-audit/completion/evidence/` (create when first used):

```text
migration-dress-YYYYMMDDTHHMMSSZ/
  identity-gate.md          # G1–G5 answers
  docker-compose-ps.txt
  alembic-version-before.sql.txt
  pg_dump-note.md           # path + size (dump itself may be gitignored)
  upgrade.out               # only if upgrade attempted
  alembic-version-after.sql.txt
  PASS-or-NOT.md            # honest label + rationale
```

---

## 9. Cross-links

| Doc | Role |
|-----|------|
| [PROD-MIGRATION-RISK.md](../PROD-MIGRATION-RISK.md) | Per-revision risk; maintenance window class |
| [PRODUCTION-CUTOVER-PACKAGE.md](../PRODUCTION-CUTOVER-PACKAGE.md) | Prod minute-by-minute — **reference only** |
| [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](../PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) | Historical prep / execution blocked policy |
| [STREAM-E-M1.md](./STREAM-E-M1.md) | This milestone probe outcome |
| [HUMAN-GATE-CARD.md](./HUMAN-GATE-CARD.md) | Prod migrate remains human gate |

---

## 10. Session probe snapshot (2026-08-08) — honesty

See [STREAM-E-M1.md](./STREAM-E-M1.md) for command outcomes. Summary:

| Item | Result |
|------|--------|
| Docker local compose | **Available** (14 services running; `postgres` + `backend` healthy) |
| `DATABASE_URL` host | `postgres:5432/salesos` (compose) |
| `ENVIRONMENT` | `development` |
| SQL `alembic_version` | `e5f9a32b0c08` (already at tip) |
| `alembic current` / `check_alembic_head.py` | **Hung** — not used as PASS evidence |
| Non-prod `alembic upgrade` | **NOT RUN** (probe-only; tip already applied; no invented PASS) |
| Production touch | **NONE** |

**Validation label for this session:** **light validated** (Docker + SQL read-only). Full path dress-rehearsal upgrade: **not validated**.

---

*Stream E — non-prod dress rehearsal runbook — 2026-08-08 — no commit — NEVER prod upgrade*
