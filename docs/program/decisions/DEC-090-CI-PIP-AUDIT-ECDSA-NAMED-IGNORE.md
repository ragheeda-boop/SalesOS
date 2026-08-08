# DEC-090 — CI Stage 5 pip-audit: named ignore for DEC-057 ecdsa residual

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Board:** Backend Deps (SalesOS)  
> **Story / risk:** R-21 residual `ecdsa` after CI-16 / CI-22 Phase 1  
> **Authority:** DEC-057 Option A (accepted residual) + CI run `30681284601` @ `f2c7587` (sole ecdsa) + tip `e993e83` host pip-audit (NO starlette; ecdsa 0.19.2 only)
> **Out of scope:** PyJWT migration (DEC-057 Option B); Security Scan workflow redesign; weakening `--strict`; ignoring other CVEs

---

## 1. Context

CI run [`30681284601`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30681284601) (commit `e993e83`):

| Job | Result |
|---|---|
| Stage 1: Backend Lint | SUCCESS |
| Stage 5: pip-audit | **FAILURE** — `Found 1 known vulnerability in 1 package` |

Sole finding:

| Name | Version | ID | Fix |
|---|---|---|---|
| `ecdsa` | 0.19.2 | **PYSEC-2026-1325** | *(none — upstream no planned fix)* |

Multipart / strawberry / starlette findings are **gone** (CI-16 Slices 1+3 + CI-22 Phase 1 starlette **1.3.1**). Security Scan workflow `pip-audit` SUCCESS is a **different job path** (does not `poetry export` the lock the same way) — not evidence that CI Stage 5 should stay red without policy alignment.

DEC-057 Option A already accepted the ecdsa residual and explicitly allowed a **future named** `--ignore-vuln` for PYSEC-2026-1325 / CVE-2024-23342 (not required to Accept A; separate CI policy commit).

---

## 2. Decision

**Authorize DEC-057 follow-on CI policy:**

1. Add **named** `--ignore-vuln PYSEC-2026-1325` to CI workflow job `security-pip-audit` (both the JSON report leg and the `--strict` gate leg).
2. Keep `--strict` enabled — any **new** vulnerability fails the job.
3. Do **not** ignore other IDs, disable the job, or remove Poetry export.
4. Document on R-21 + Sprint 05 board; do **not** claim whole-pipeline CI GREEN.

---

## 3. Explicit non-claims

- Does **not** remove `ecdsa` from the lock.
- Does **not** implement Option B (PyJWT).
- Does **not** close CI-22 (residual modernization scope may remain).
- Does **not** fix Trivy filesystem / Backend Types / other red gates.
- Does **not** silent-weaken the scanner beyond this single named advisory.

---

## 4. Consequence

- Stage 5 pip-audit expected **green** after this land (field-verify on next CI run).
- R-21 remains **Open — mitigating** (package still present; monitor; Option B deferred).
- **Whole-pipeline CI GREEN not met.**
