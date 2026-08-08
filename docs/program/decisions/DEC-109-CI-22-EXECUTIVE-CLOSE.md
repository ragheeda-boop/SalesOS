# DEC-109 — CI-22 executive close: FastAPI / Starlette / Pydantic cascade COMPLETE; starlette floor cleared

> **Status:** **Accepted** — CI-22 **CLOSED**  
> **Date:** 2026-08-01  
> **Board:** Backend / Deps (SalesOS)  
> **Story / risk:** CI-22 / R-21 starlette leg  
> **Authority:** DEC-054 (register) · DEC-073 (plan C0) · DEC-081 (Phase 1 land) · DEC-052 STOP · DEC-057 ecdsa out of scope  
> **Out of scope this land:** package/lock bumps · ecdsa / PyJWT (DEC-057) · CI-16 reopen · CI-08 GHCR · CI-14 · Railway · DEC-085 `set_config` · auth/CSRF/RBAC weaken

---

## 1. Why executive close (AC met; no further CI-22 package work)

CI-22 was registered to clear the **starlette `pip-audit` floor (≥1.3.1)** via a scoped FastAPI + pydantic cascade. Phase 1 landed the cascade; field corroboration and compatibility residuals are now complete. Leaving the story OPEN idle during GHCR wait adds no AC value.

| AC signal | Evidence |
|---|---|
| Lock cascade | fastapi **0.141.1** / starlette **1.3.1** / pydantic **2.13.4** / email-validator **2.3.0** (DEC-081 @ `442af64` + tip lock) |
| Starlette floor | **≥1.3.1** explicit constraint; host + field **NO starlette** findings |
| Field Stage 5 pip-audit | Run `30688863161` @ `3084e5b` job `91339902722` **SUCCESS** — log: `No known vulnerabilities found, 1 ignored` (ecdsa PYSEC-2026-1325 via DEC-090) |
| Field Secrets Scan / Trivy | Same run Secrets Scan **SUCCESS** (DEC-098 `CVE-2024-23342` ignore — ecdsa, not CI-22) |
| Stages 1–5 corroboration | Run `30689682988` @ `7ba137b` — Stages 1–5 **SUCCESS** incl. pip-audit + Secrets Scan; Stage 6 fail = CI-08 GHCR only |
| C3 compatibility | Request param fixes (DEC-081); excel_import `Request = Request` (`4f035dd`); FastAPI 0.141 `_IncludedRouter` RBAC override walk (`3084e5b`) — Backend Unit **0 failed** / 2700 passed (job `91339985115`) |
| ecdsa residual | **Not CI-22** — DEC-057 Option A + DEC-090/098 named ignores |

No remaining CI-22-owned vulns. Further FastAPI majors beyond **0.141.x** are optional modernization, not this story’s close gate.

---

## 2. Decision

1. **CLOSE CI-22** as **COMPLETE** (starlette leg of R-21 cleared).  
2. **Do not** reopen CI-16.  
3. **Do not** claim whole-pipeline **CI GREEN**, Production GO, or Stage 6/7 green.  
4. **Residuals (documented, not CI-22 reopen):**
   - `ecdsa` Minerva (PYSEC-2026-1325 / CVE-2024-23342) — accepted under DEC-057; CI ignore policy DEC-090/098  
   - Optional future FastAPI/Starlette/Pydantic majors — new story if authorized  
   - CI-08 GHCR push 403 — ops (DEC-104)

---

## 3. Acceptance / honesty

| Claim | Status |
|---|---|
| CI-22 story | **CLOSED** |
| Starlette `pip-audit` floor ≥1.3.1 | **MET** |
| Field pip-audit (starlette) | **Clear** (1 ignored = ecdsa only) |
| Whole-pipeline CI GREEN | **Not met** (CI-08) |
| Production GO / External pilot | **NO-GO** |
| Validation this land | **build validated** (field pip-audit + Unit + Stages 1–5); docs close only this commit |

---

## 4. Next READY (if any)

- **CI-08** (P0 BLOCKED) — GHCR Packages write (DEC-104 Option A).  
- **DB-05** schema reconciliation (R-20).  
- Optional Jest 30 backlog (not CI-14 reopen).  
- Contract-tests further endpoints (optional; slices 1–4 landed).
