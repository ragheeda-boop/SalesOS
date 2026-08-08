# DEC-098 — CI Stage 5 Secrets Scan (Trivy): named ignore for DEC-057 ecdsa residual

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Board:** Security / CI (SalesOS)  
> **Story / risk:** R-21 residual `ecdsa` after CI-16 / CI-22 Phase 1; Secrets Scan still red after DEC-090 pip-audit align  
> **Authority:** DEC-057 Option A + DEC-090 (same residual) + CI run `30684813480` @ `c8c1bce` Secrets Scan FAILURE (sole HIGH)  
> **Out of scope:** PyJWT migration (DEC-057 Option B); ignoring other CVEs; disabling Trivy `exit-code: 1`; weakening severity floor; DEC-085 / `get_db`

---

## 1. Context

CI run [`30684813480`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30684813480) (commit `c8c1bce`):

| Job | Result |
|---|---|
| Stage 1: Backend Lint | SUCCESS |
| Stage 2: Backend Types | SUCCESS (tip corroboration) |
| Stage 5: Secrets Scan | **FAILURE** — Trivy fs blocking gate exit 1 |

Sole HIGH finding (blocking table):

| Library | Vulnerability | Severity | Installed | Fixed |
|---|---|---|---|---|
| `ecdsa` | **CVE-2024-23342** | HIGH | 0.19.2 | *(none)* |

`salesos/frontend/package-lock.json` → **0** vulns. No other CRITICAL/HIGH.

This is the **same** accepted residual as DEC-090's pip-audit `PYSEC-2026-1325` (Minerva / python-ecdsa). Trivy and pip-audit use different ID namespaces for the same advisory. DEC-090 intentionally scoped to pip-audit only and left Trivy red; this DEC closes that policy gap without blanket-weakening.

`.trivyignore` previously stated "No CVEs accepted yet" — stale after DEC-057/090.

---

## 2. Decision

**Authorize DEC-090 follow-on for Trivy:**

1. Land **named** ignore `CVE-2024-23342` in repo-root `.trivyignore` with DEC references (single ID; no package-wide or severity-wide mute).
2. Stop gitignoring `.trivyignore` (was listed under Security tools in `.gitignore`) so the named ignore is tracked.
3. Wire `trivyignores: .trivyignore` on CI `security-secrets-scan` Trivy steps (blocking table + SARIF export) so the named file is explicit in the job log.
4. Keep `severity: CRITICAL,HIGH` and blocking `exit-code: 1` — any **new** HIGH/CRITICAL fails the job.
5. Do **not** ignore other IDs, drop severity, or remove the gate.
6. Document on R-21 + Sprint 05 board; do **not** claim whole-pipeline CI GREEN.
7. **Preserve DEC-085** — no edits to `get_db` / `set_config`.

---

## 3. Explicit non-claims

- Does **not** remove `ecdsa` from the lock.
- Does **not** implement Option B (PyJWT).
- Does **not** supersede DEC-090 (pip-audit PYSEC ignore remains).
- Does **not** silent-weaken Trivy beyond this single named CVE.
- Does **not** claim production GO or whole-pipeline CI GREEN.

---

## 4. Consequence

- Stage 5 Secrets Scan expected **green** after this land (field-verify on next CI run), assuming no new CRITICAL/HIGH appear.
- R-21 remains **Open — mitigating** (package still present; monitor; Option B deferred).
- **Whole-pipeline CI GREEN not met.**
