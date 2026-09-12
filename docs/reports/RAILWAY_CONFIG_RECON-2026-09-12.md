# Railway Config Reconciliation — 2026-09-12

**Agent:** A3 — Deployment Config Reconciliation  
**Workspace:** `D:\AISalesOS`  
**Scope:** Repo config files only. No deploy. No secret/.env edits. No git write.  
**Honest label:** **light validated** (file existence + JSON parse). Live Railway dashboard **not** probed this session.

---

## 1. Which file Railway actually uses

### Verdict

| Period | Canonical file | Status |
|--------|----------------|--------|
| **Before this reconciliation** | `D:\AISalesOS\railway.json` (repo root) was the file CI/Railway *would* read — but it was **incomplete** (`preDeployCommand` missing). `salesos/railway.json` was a **second live config** with a different Dockerfile and the migrate command. | Split-brain |
| **After this reconciliation** | **`D:\AISalesOS\railway.json`** is the single procedural source of truth. `salesos/railway.json` is a **pointer stub**, not a deploy config. | Single file |

### Evidence (FACT)

| Source | What it says |
|--------|----------------|
| `.github/workflows/deploy.yml:134` | Comment: *“Deploy from repo root so the root railway.json / Dockerfile.railway path is used.”* Job runs `railway up --ci -y` from the repository root (not `salesos/`). |
| `.github/workflows/deploy-staging.yml:138` | Same instruction for staging. |
| `.github/workflows/deploy.yml:91–92` | Schema-drift gate comment: DB-vs-repo sync is enforced at deploy time by `railway.json` `preDeployCommand` (`alembic upgrade head`). |
| `AGENTS.md` §17 / remaining human actions | “Align live Railway `preDeployCommand` with `railway.json`” — treats one `railway.json` as the repo contract; does not name `salesos/railway.json`. |
| `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` §9–10 | Expected repo command is `alembic upgrade head`. Live dashboard (2026-08-21 evidence) used `init_db()` instead. |
| `docs/current-state/GATE_D5_REVIEW.md` (2026-08-24) | Claimed root `railway.json` already had `preDeployCommand` and that `salesos/railway.json` was archived to `docs/archive/railway.json.stale`. **Disk on 2026-09-12 contradicted that claim** (see §3). |
| Railway / CI working directory | `railway up` from repo root → Railway reads **root** `railway.json` and `dockerfilePath: "Dockerfile.railway"` (also at repo root). |

**Not FACT (not re-verified this session):** whether the live Railway *dashboard* still overrides the file with `init_db()`. Last written evidence of that override is 2026-08-21 (`FINAL_GO_NOGO` §9, `HUMAN-GATE-CLOSURE-SUMMARY-2026-08-21.md`).

---

## 2. Inventory (files inspected)

| Path | Existed? | Role before | Role after |
|------|:--------:|-------------|------------|
| `D:\AISalesOS\railway.json` | Yes | Root config: Dockerfile.railway + multiplexed start; **no** `preDeployCommand` | **Canonical** — added `preDeployCommand` |
| `D:\AISalesOS\salesos\railway.json` | Yes | Live duplicate: `backend/Dockerfile`, `preDeployCommand: alembic upgrade head`, retries=10 | **Pointer stub** (not a Railway deploy config) |
| `D:\AISalesOS\railway.beat.json` | Yes | Optional beat overlay (`Dockerfile.railway.celery`) | Unchanged — not the API canonical file |
| `D:\AISalesOS\railway.worker.json` | Yes | Optional worker overlay (`Dockerfile.railway.celery`) | Unchanged — not the API canonical file |
| `D:\AISalesOS\salesos\railway.beat.json` | **No** | — | — |
| `D:\AISalesOS\salesos\railway.worker.json` | **No** | — | — |
| `D:\AISalesOS\Dockerfile.railway` | Yes | Image used by root `railway.json` | Unchanged |
| `D:\AISalesOS\Dockerfile.railway.celery` | Yes | Image referenced by beat/worker JSON | Unchanged |
| `D:\AISalesOS\salesos\backend\Dockerfile` | Yes | Image referenced only by the stale `salesos/railway.json` | Unchanged (not owned for edit) |
| `D:\AISalesOS\docs\archive\railway.json.stale` | Yes | Snapshot of the old `salesos/railway.json` body | Unchanged |
| `D:\AISalesOS\salesos\frontend\vercel.json` | Yes | Frontend Vercel config; `regions: ["iad1"]` | Unchanged (JSON cannot hold comments) |

---

## 3. Before / after — exact config changes

### 3.1 Canonical: `D:\AISalesOS\railway.json`

**Before** (no migrate step):

```json
"deploy": {
  "startCommand": "sh -c 'case \"$RAILWAY_SERVICE_NAME\" in *celery-worker*) …esac'",
  "healthcheckPath": "/health",
  "restartPolicyType": "ON_FAILURE",
  "restartPolicyMaxRetries": 3
}
```

**After** (one added key):

```json
"deploy": {
  "preDeployCommand": "alembic upgrade head",
  "startCommand": "sh -c 'case \"$RAILWAY_SERVICE_NAME\" in *celery-worker*) exec python -m app.railway_celery_service worker;; *celery-beat*) exec python -m app.railway_celery_service beat;; *) exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000};; esac'",
  "healthcheckPath": "/health",
  "restartPolicyType": "ON_FAILURE",
  "restartPolicyMaxRetries": 3
}
```

Unchanged: `builder: DOCKERFILE`, `dockerfilePath: Dockerfile.railway`, multiplexed `startCommand`, healthcheck, restart policy.

### 3.2 Neutralized duplicate: `D:\AISalesOS\salesos\railway.json`

**Before** (conflicting live config — same body as `docs/archive/railway.json.stale`):

- `dockerfilePath`: `backend/Dockerfile` (only valid if Railway root were `salesos/`)
- `preDeployCommand`: `alembic upgrade head`
- `restartPolicyMaxRetries`: `10` (root uses `3`)
- No `startCommand` / `healthcheckPath` (relied on `salesos/backend/Dockerfile` ENTRYPOINT)

**After** (pointer only — no `$schema`, no `build`, no `deploy`):

- `NOTICE`: stale / not used by Railway
- `canonicalFile`: `../railway.json`
- `doNotDeployFromThisFile`: `true`
- `evidence`: CI line citations + archive path

### 3.3 GATE_D5 claim vs disk (2026-09-12)

`docs/current-state/GATE_D5_REVIEW.md` (2026-08-24) claimed Condition 1 CLOSED:

- Root already had `preDeployCommand: "alembic upgrade head"`
- `salesos/railway.json` archived; only root remained

**Disk fact this session:** root was **missing** `preDeployCommand`; `salesos/railway.json` was still a **full live Railway schema**. D5 is **stale documentation**, not current repo state. This reconciliation applies the D5 *intent* for real.

`Dockerfile.railway` also does **not** match the D5 claim (tini / poetry / `scripts/` copy). That image gap is documented in §7; it was **not** rewritten here (out of the migrate-command question; `app/alembic/lib/rls.py` states production images do not need `scripts/`).

---

## 4. `preDeployCommand` — FACT vs RECOMMENDATION

### FACT (working directory / command)

| Fact | Evidence |
|------|----------|
| Image `WORKDIR` is `/app` | `Dockerfile.railway` lines 3 and 46 |
| `alembic.ini` is copied to `/app` | `COPY salesos/backend/alembic.ini .` then `COPY --from=builder /app/alembic.ini .` |
| Alembic script dir is `app/alembic` | `salesos/backend/alembic.ini` → `script_location = app/alembic`; `COPY salesos/backend/app/ app/` includes versions |
| Alembic is a runtime dependency | `salesos/backend/pyproject.toml` → `alembic = "^1.13"`; image runs `pip install --no-cache-dir .` |
| In-container CWD for the built image is `/app` | Therefore the correct command is **`alembic upgrade head`** — no `cd salesos/backend` |
| A `cd salesos/backend && alembic …` form would be **wrong** inside this image | That path does not exist at `/app` |
| RLS revisions do not require `scripts/` in the image | `app/alembic/lib/rls.py` duplicates the generator “so that the production Docker image does not need the `scripts/` package” |

### FACT (what audits expected)

Repo contract in CI + `FINAL_GO_NOGO` + HUMAN-GATE: `preDeployCommand` = `alembic upgrade head`.

### FACT (live drift — last evidence 2026-08-21; not re-probed)

Live Railway used `python -c "… init_db() …"`. `init_db()` **detects** drift and does **not** auto-migrate (B03-B). That is why deploys could succeed while schema sat at `f4aee055fd6e` until the 2026-08-21 manual upgrade.

### RECOMMENDATION (do not apply live from this session)

1. Set (or clear-to-file) the Railway **dashboard** `preDeployCommand` on the **API** service to `alembic upgrade head` so it cannot silently stay on `init_db()`.
2. Do **not** keep a dashboard override that disagrees with `railway.json`.
3. If celery-worker / celery-beat share the same `railway.json`, they will also run `alembic upgrade head` before start. Alembic’s version lock makes concurrent `upgrade head` usually safe; prefer migrate **only on the API service** in the dashboard if you want a single migrator.
4. Beat/worker JSON files (`railway.beat.json`, `railway.worker.json`) have **no** `preDeployCommand` — leave it that way if those files are attached as per-service config paths.
5. Confirm `alembic` is on `PATH` in the running image (`pip install .` should install the CLI). If a future image drops that, switch to `python -m alembic upgrade head` (same CWD).

---

## 5. Drift vs `FINAL_GO_NOGO` and HUMAN-GATE / OPS

Source: `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` (dated 2026-09-05 in-file).

| Assessment statement | Repo state **before** this change | Repo state **after** |
|----------------------|-----------------------------------|----------------------|
| Expected `railway.json` `preDeployCommand` = `alembic upgrade head` | **False for the file Railway CI uses** (root lacked the key). True only on the unused `salesos/` duplicate. | **True** on canonical root file |
| Live dashboard = `init_db()` vs file = `alembic upgrade head` | File-side half of the drift was *also* broken (root had no command). Live side **unknown today** | File-side aligned. **Live dashboard still a human action** |
| Residual: “Railway `preDeployCommand` drift” (§4, §9, Executive Decision) | Open | **Repo contract closed.** Dashboard alignment still open |
| Residual: Railway backup schedule, staging OAuth, Phase 7 ER, Production GA | Unchanged | Unchanged — **not** claimed closed |
| `docs/ops/HUMAN-GATE-CLOSURE-SUMMARY-2026-08-21.md` P1 “Align live Railway `preDeployCommand` with `railway.json`” | Open | Still open — **dashboard**, not git |
| `AGENTS.md` §17 / §18 same P1 | Open | Still open — dashboard |
| GATE_D5 “Railway config conflict CLOSED” | **Incorrect vs disk** | Conflict neutralized in git; D5 text remains stale until a docs owner updates it |

**This report does not edit `FINAL_GO_NOGO_ASSESSMENT.md`.** After a human confirms the dashboard, that assessment’s residual row should be updated with new evidence (deploy log showing `alembic upgrade head`, not `init_db()`).

Production GA remains **not declared**. This work does not overturn the 2026-07-22 audit NO-GO.

---

## 6. `vercel.json` `iad1` — KSA residency (documentation only)

**File:** `D:\AISalesOS\salesos\frontend\vercel.json`  
**Setting:** `"regions": ["iad1"]`  
**Comment in file:** **not added**. The file is JSON (`$schema`: `https://openapi.vercel.sh/vercel.json`). JSON does not allow comments; a `//` or `/* */` would break parse / Vercel.

### Honest meaning

| Item | Statement |
|------|-----------|
| What `iad1` is | Vercel region code for **Washington, D.C. / US East (Ashburn)** — not a Middle East or KSA region. |
| What it pins | Next.js serverless / SSR execution region for this project (plus Vercel’s usual global CDN for static assets). |
| KSA / PDPL implication | Frontend **origin compute is US-resident**, not KSA-resident. If the product story is “data residency in KSA,” this file is a **residency gap** for anything the Vercel app processes (SSR, server actions, env-backed API routes), independent of Railway Postgres region. |
| What this is not | Not an ISO registration. Not a PDPL compliance claim. Not proof of Railway or database region. |
| Change this session | **None.** Region left as `iad1`. Changing region is a product/legal decision, not a config typo fix. |

---

## 7. Dockerfile.railway notes (no edit)

Path: `D:\AISalesOS\Dockerfile.railway`.

- Matches root `railway.json` `dockerfilePath`.
- Copies backend tree from `salesos/backend/…` into `/app` so root-context Docker builds work.
- `CMD` is uvicorn; root `railway.json` `startCommand` overrides that and multiplexes worker/beat via `RAILWAY_SERVICE_NAME`.
- Gaps vs `salesos/backend/Dockerfile` (documented, not fixed): no `tini`, no Poetry, no `scripts/` copy, no `docker-entrypoint.sh`. D5 claimed these were added; they are not on disk.
- Sufficient for `alembic upgrade head` as reasoned in §4.

Beat/worker overlays still point at `Dockerfile.railway.celery` (root). They are **not** a second API canonical. Do not attach them to the API service.

---

## 8. Recommended Railway dashboard steps (do not apply live)

Owner: DevOps / Railway project Admin. **Do not deploy from this session.**

1. Open the SalesOS Railway project → **API** (web) service → Settings → Deploy.
2. Confirm **Config as Code** / railway.json path is the **repository root** file (`railway.json`), not `salesos/railway.json`.
3. Inspect **Pre-deploy command**:
   - If it is `python -c "… init_db() …"` (or any `init_db` wrapper) → replace with `alembic upgrade head`, **or** delete the override so the file value is used.
   - If it is already `alembic upgrade head` → record a screenshot / deploy log as evidence and close the HUMAN-GATE P1.
4. Confirm **Dockerfile** path is `Dockerfile.railway` (repo root), not `salesos/backend/Dockerfile`, unless a service is explicitly rooted at `salesos/` (CI says it is not).
5. Confirm start command matches the multiplexed `startCommand` in root `railway.json` (or leave empty if you rely on the file).
6. Repeat the pre-deploy check on **staging** (`deploy-staging.yml` also deploys from repo root).
7. Celery worker / beat services:
   - If they use root `railway.json`, expect `alembic upgrade head` on those deploys too, or set those services’ config path to `railway.worker.json` / `railway.beat.json` (no migrate).
   - Do **not** point worker/beat at the `salesos/railway.json` stub.
8. After the next approved deploy, capture logs: pre-deploy must show Alembic `upgrade head` (Running upgrade … / already at head), **not** “Automatic migration is disabled (B03-B)”.
9. Then update `FINAL_GO_NOGO` residual row with that evidence. Until then, dashboard drift remains **open**.

---

## 9. Commands run + validation

Low-load: no npm, no pytest, no full builds, no deploy, no Railway CLI against live.

| Command / check | Result |
|-----------------|--------|
| Read `railway.json`, `salesos/railway.json`, beat/worker JSON, `vercel.json`, `Dockerfile.railway` | Files found as inventoried in §2 |
| Read `salesos/railway.beat.json`, `salesos/railway.worker.json` | **Do not exist** |
| Read CI `deploy.yml` / `deploy-staging.yml` | Root-deploy comments at lines 134 / 138 |
| Read `FINAL_GO_NOGO_ASSESSMENT.md` §4, §9, §10 | Drift residual still listed |
| Read `HUMAN-GATE-CLOSURE-SUMMARY-2026-08-21.md` | P1 dashboard align still listed |
| Read `AGENTS.md` §17 remaining actions | Same P1 |
| Read `GATE_D5_REVIEW.md` | Stale CLOSED claim vs disk |
| PowerShell `ConvertFrom-Json` on canonical `railway.json` | **PASS** (see below) |
| PowerShell `ConvertFrom-Json` on stub `salesos/railway.json` | **PASS** |
| PowerShell `ConvertFrom-Json` on `vercel.json` | **PASS** (unchanged) |
| PowerShell `ConvertFrom-Json` on `railway.beat.json` / `railway.worker.json` | **PASS** (unchanged) |

Validation command (PowerShell):

```powershell
@(
  'D:\AISalesOS\railway.json',
  'D:\AISalesOS\salesos\railway.json',
  'D:\AISalesOS\railway.beat.json',
  'D:\AISalesOS\railway.worker.json',
  'D:\AISalesOS\salesos\frontend\vercel.json'
) | ForEach-Object { Get-Content -Raw $_ | ConvertFrom-Json | Out-Null; $_ }
```

Live Railway dashboard / `railway status`: **not run**.

---

## 10. Files changed

| File | Change |
|------|--------|
| `D:\AISalesOS\railway.json` | Added `"preDeployCommand": "alembic upgrade head"` under `deploy` |
| `D:\AISalesOS\salesos\railway.json` | Replaced live duplicate with pointer stub to `../railway.json` |
| `D:\AISalesOS\docs\reports\RAILWAY_CONFIG_RECON-2026-09-12.md` | This report (new) |

**Not changed (owned but no edit needed):** `Dockerfile.railway`, `railway.beat.json`, `railway.worker.json`, `salesos/frontend/vercel.json`.

**Not changed (forbidden):** `AGENTS.md`, `AI_HONESTY`, `app/config.py`, `.gitignore`, tests, `project-audit/`, `FINAL_GO_NOGO_ASSESSMENT.md`, secrets, `.env`.

---

## 11. Short summary (for parent / human)

- **Canonical file:** `D:\AISalesOS\railway.json`
- **preDeployCommand:** `alembic upgrade head`
- **Remaining human Railway dashboard actions:** confirm API (+ staging) pre-deploy is `alembic upgrade head` (clear `init_db()` override); confirm config path is repo-root `railway.json` + `Dockerfile.railway`; capture next-deploy Alembic logs; then update the GO/NO-GO residual. Do not treat this git change as live alignment.
