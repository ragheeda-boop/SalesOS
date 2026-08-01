# DEC-120 — DEC-016 Railway R-14 security closure CONTRADICTED; S04-04 + R-14 REOPENED

> **Status:** **Accepted** — Phase 0 (DEC-008 / R-14) exit reset to **NO-GO** until live AC re-proven  
> **Date:** 2026-08-01  
> **Board:** Architecture Review Board + Risk Manager + Program Director (SalesOS / AQLIYA)  
> **Authority:** Tier-1 Principal Audit [`docs/audit/PRINCIPAL_AUDIT_2026-08-01_DEC016_RAILWAY_CI.md`](../../audit/PRINCIPAL_AUDIT_2026-08-01_DEC016_RAILWAY_CI.md) (agent `ddf9d84e`)  
> **Amends / supersedes (consequence only):** DEC-016 security-closure consequence; DEC-086 Phase 0 GO on R-14  
> **Numbering note:** DEC-119 reserved for Category B Slice B7 (parallel agent). This reopen is **DEC-120**.  
> **Does not:** reopen STORY-02-01 (DEC-044); weaken DEC-085 `set_config`; claim Production GA GO; rotate secrets in-repo

---

## 1. Decision

Treat DEC-016 Option A **infrastructure steps** as partially verified and its **security closure** (runtime least-privilege + bypass-probe + Railway RLS isolation) as **CONTRADICTED** by live Tier-1 evidence.

| Field | Value |
|---|---|
| S04-04 | **REOPENED** (BLOCKED on remediation slices A–E + live re-proof) |
| R-14 (Railway slice) | **REOPENED** — local/CI/compose template remediation (DEC-014/015) **not** revoked; Railway live isolation **not** proven |
| Phase 0 (DEC-008 / R-14) exit | **NO-GO** (DEC-086 Phase 0 GO on R-14 **withdrawn**) |
| Production GA | **NO-GO** (unchanged; never cleared by DEC-016) |
| Dual honesty | **Env provision ≠ runtime RLS** — `APP_POSTGRES_*` present does **not** equal sessions as `salesos_app` or tenant isolation |

**Validation label for this records land:** **docs / light validated** (encodes auditor Tier-1 claims; this land does **not** re-run Railway probes).

---

## 2. Auditor claims encoded (cite audit file)

Source: [`PRINCIPAL_AUDIT_2026-08-01_DEC016_RAILWAY_CI.md`](../../audit/PRINCIPAL_AUDIT_2026-08-01_DEC016_RAILWAY_CI.md). Deploy IDs match DEC-016; outcome does **not** equal RLS isolation.

| ID | Claim | Auditor verdict |
|---|---|---|
| A1–A5 | Staging deploy `7d33a0bc…` / prod `1328309a…` SUCCESS; `APP_POSTGRES_USER=salesos_app` + password present; `/health` 200; `salesos_app` NOSUPERUSER/NOBYPASSRLS | **VERIFIED** (infra) |
| A6 | Runtime connects as `salesos_app` | **FALSE** — `pg_stat_activity` all `postgres` (BYPASSRLS); **0** `salesos_app` |
| A7 | Bypass-probe PASS | **FALSE** — prod `salesos_app` SELECT companies → **141,221** with no tenant; `pg_policies` tenant_isolation\_\* = **0**; `relrowsecurity` = **0** |
| A8 | Prod honors `APP_POSTGRES_*` | **FALSE** — health image **`3.1.0`** (pre-`APP_POSTGRES` consumption era); wiring landed in `5e7023f` (2026-07-31) |
| A9 | S04-04 / R-14 Railway CLOSED | **CONTRADICTED** |
| B4 | Staging isolation proof | **Weak** — empty-ish DB; also **0** policies |
| C7 | Tunnel password exposure | **Rotate required** (human/ops — see §4) |
| E2–E4 | Tip CI Ruff I001/E501; CI-08 GHCR 403; CI-09 SSH host missing | **VERIFIED** (adjacent; not Phase 0 substitute) |

**Honesty rule:** Tier 1 (live CLI/DB/API) overrides Tier 3 (DEC-016 / board / DEC-086 text).

---

## 3. Remediation plan (executable slices)

Do **not** weaken RLS or DEC-085. Prefer docs/ops/code for DB URL wiring; avoid Category B Alembic fights.

| Slice | Action | Ready now? | Notes |
|---|---|---|---|
| **A** | Confirm commit that introduced `APP_POSTGRES` / `app_database_url` wiring | **READY** | Tip evidence: **`5e7023f`** (`R-14: least-privilege runtime role…` — `config.py` + `database.py`). Category B lands do not replace this. |
| **B** | Image promote path Railway staging → prod | **READY (path choice)** | Primary: CI Stage 6 → GHCR → Railway pull — **BLOCKED by CI-08 GHCR 403** (DEC-104). **Alternate (authorized for ops):** Railway build-from-GitHub / redeploy from tip SHA without GHCR. Goal: running image ≥ post-`5e7023f` that consumes `APP_POSTGRES_*`. |
| **C** | Alembic upgrade Railway DBs to tip RLS head | **READY after change-control** | Prod was at alembic `0051` with **0** policies; tip head includes Category A + B policies. Staging first; backup; **apply existing tip revisions only** (no new migration authorship in this reopen land). |
| **D** | Force app runtime to `salesos_app` (not `postgres` `DATABASE_URL`) | **READY after B** | Env already has `APP_POSTGRES_*`; prove process uses `app_database_url`. Do not commit passwords. |
| **E** | Re-run bypass-probe + session proof | **READY after C+D** | PASS criteria: `pg_stat_activity` shows **`salesos_app`**; with unset tenant, app role must **not** read cross-tenant rows; `tenant_isolation_%` policies present on Railway. Staging empty-DB caveat: seed or use known multi-tenant fixtures before claiming PASS. |

**Close gate for S04-04 / Railway R-14:** all of A–E with recorded Tier-1 evidence (redacted). Until then Phase 0 R-14 remains **NO-GO**.

---

## 4. Required human / ops (secrets)

| Item | Instruction |
|---|---|
| **Postgres password rotate** | **Required.** Audit tunnel printed credentials into agent terminals. Rotate Railway staging + production Postgres **and** `APP_POSTGRES_PASSWORD` via Railway dashboard or `railway variables set` **without** echoing full values into logs/transcripts/commits. Prefer human ops; do **not** commit secrets. |
| Historical `.env.staging` in git | Rotate any credentials that may still be reused (audit C2). |
| CI-08 / CI-09 | Remain BLOCKED (ops); alternate promote path (§3 B) unblocks Railway image independently of GHCR if chosen. |

---

## 5. Consequence

- DEC-016 remains historical **Accepted** for Option A *authorization* and for infra steps that Tier-1 still verifies; its **CLOSED / Phase 0 clearance consequence is revoked** by this DEC.
- DEC-086 Phase 0 (DEC-008 / R-14) **GO** is **withdrawn** pending re-proof.
- Board S04-04 → **REOPENED**; R-14 Railway → **REOPENED**; Phase 0 critical path → **BLOCKED** on S04-04 again.
- STORY-02-01 stays **CLOSED** (DEC-044). Category B parallel READY continues (DEC-107) except do not claim Phase 0 GO.
- **Production GA = NO-GO.** Prior Phase 0 R-14 GO **withdrawn**.

---

## 6. Out of scope this land

- Live Railway password rotation via agent CLI (leak risk)
- App image promote / alembic upgrade execution (ops follow-on) — **partially superseded by §7 Slice B** (staging `railway up` only; production not promoted)
- Category B Alembic authorship
- Weakening auth/CSRF/RBAC/RLS/DEC-085

---

## 7. Remediation progress (2026-08-01)

### Slice A — wiring VERIFIED (tip at land: `0bd73fc`; still ancestor of later tip)

| Check | Evidence |
|---|---|
| Ancestor | `5e7023f` is ancestor of `0bd73fc` / current tip |
| Config | `salesos/backend/app/config.py` — `app_postgres_user` / `app_postgres_password` / `app_database_url` (lines 85–107); empty password → fallback `resolved_database_url` |
| Engine | `salesos/backend/app/database.py` — request `engine = create_async_engine(settings.app_database_url, …)` (lines 35–36); `owner_engine` stays on `resolved_database_url` (lines 45–46); DEC-085 `set_config` intact (lines 90–96) |
| Tip vs prod version gap | Default `service_version = "5.1.0-rc1"` (`config.py` ~145). Live prod `/health` still **`3.1.0`**. Staging `/health` reports `5.1.0-rc1` but env `SERVICE_VERSION` can mask binary age — use session proof, not version alone |
| Staging env (redacted) | `APP_POSTGRES_USER=salesos_app`; `APP_POSTGRES_PASSWORD` present; `DATABASE_URL` user=`postgres`; `POSTGRES_HOST=postgres.railway.internal` |

### Slice B — staging tip image DEPLOYED

| Fact | Detail |
|---|---|
| Source model | **No GitHub repo** on SalesOS deploys (no `repo`/`commitHash`). Prior `7d33a0bc` was env **redeploy** (~3s) of old image |
| GHCR | Still BLOCKED (CI-08 403) |
| Alternate | `railway up` from clean worktree **`0bd73fc`** `salesos/backend` (pre-DEC-119 B7 — avoids alembic head fight with later `291bf3d`) |
| Deploy | **`98bf85bf-89cc-4198-97d9-d477b2734a23` SUCCESS** |
| Health | staging `/health` **200** `version=5.1.0-rc1` `database=connected` |
| Session proof (SSH; no secrets) | `APP_ENGINE salesos_app`; `pg_stat_activity`: `salesos_app=2`, `postgres=87`; `OWNER_ENGINE postgres` |
| Production | **Not promoted.** Prod remains **`3.1.0`** |
| Password rotate | Still **human/ops** (tunnel exposure) — dashboard / `railway variables set` without echoing values |

### Slice C/D prep (not closed)

| Item | Note |
|---|---|
| C | Staging `alembic_version` = **`0049`**; tip RLS head now includes B7 (`b7e2…` @ `291bf3d`). Policies `tenant_isolation_%` = **0**. Staging first + backup; change-control before `upgrade head` |
| D | Staging request path uses `salesos_app` after tip image; residual `postgres` sessions remain (owner + other services). Prod still needs tip image + proof |
| E | READY after C + D/prod image |

**Validation (A+B):** **light validated**. **Not** bypass-probe PASS. **Production GA = NO-GO.**
