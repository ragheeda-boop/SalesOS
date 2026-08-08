# DEC-057 — CI-16 ecdsa disposition: accept residual risk (Option A)

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Board:** Security + Documentation (SalesOS)  
> **Story / risk:** CI-16 / R-21 residual package `ecdsa` (PYSEC-2026-1325 / CVE-2024-23342 Minerva)  
> **Authority:** Executable usage evidence (jose/JWT grep) + upstream “no planned fix” + CI-16 slice progress through DEC-056  
> **Out of scope:** CI-22 FastAPI/Starlette/Pydantic cascade; blind `ecdsa` version bumps; weakening `pip-audit --strict` without this DEC

---

## 1. Decision required

After CI-16 Slice 1 (`python-multipart` @ `1e73a2f`) and Slice 3 (`strawberry-graphql` @ `d3f1eef`), R-21 residuals are:

| Package | Owner | Status |
|---|---|---|
| `starlette` | **CI-22** (DEC-052 → DEC-054) | Not CI-16 slice work |
| `ecdsa 0.19.2` | **CI-16** disposition | This DEC |

`ecdsa` has **no patched release** (upstream treats side-channels as out of scope; **no planned fix**). Blind bump is invalid. Disposition must be chosen without pretending a version floor exists.

---

## 2. Options

### Option A — Accept residual risk with documented justification + monitor

Keep `python-jose[cryptography]` / transitive `ecdsa` in the lock. Document that SalesOS JWT signing/verification paths do **not** exercise ECDSA (`ES*`) algorithms. Monitor advisories / `python-jose` issue [#399](https://github.com/mpdavis/python-jose/issues/399). Optional later: authorize a **named** `pip-audit --ignore-vuln` for PYSEC-2026-1325 / CVE-2024-23342 only after this DEC (separate CI policy commit — not required to Accept A).

### Option B — Migrate JWT signing off `python-jose` to cryptography / PyJWT backend

Replace `from jose import jwt` call sites with PyJWT (cryptography backend) so `ecdsa` can leave the dependency tree. Existing adjacent pattern: `domains/workflow/webhook_auth.py` already uses PyJWT for HS256. Identity path already builds RSA PEM via `cryptography` in `app/modules/identity/jwks.py` and only uses jose for encode/decode.

### Option C — Pin / replace dependency path

Force-exclude or replace the `ecdsa` edge under `python-jose` (Poetry override / fork / alternate JOSE stack) without a full JWT call-site migration. Solver risk: `python-jose` declares a hard dependency `ecdsa != 0.15`.

---

## 3. Usage evidence (SalesOS)

| Path | Library | Algorithms observed |
|---|---|---|
| `app/modules/identity/jwks.py` | `jose.jwt` + `cryptography` keys | **RS256** encode/decode only |
| `app/config.py` | settings | `jwt_algorithm` default **`RS256`** |
| `sdk/security.py` | `jose.jwt` | default **HS256**; caller-supplied `algorithm` (no ES* defaults) |
| `domains/workflow/webhook_auth.py` | **PyJWT** (optional import) | default **HS256** |
| Repo grep `ES256` / `ES384` / `ES512` / direct `import ecdsa` | — | **No matches** in application code |

Dependency path: `python-jose 3.5.0` → hard dep `ecdsa != 0.15` (lock **0.19.2**), even with extras `[cryptography]` enabled. Advisory class: Minerva timing on **ECDSA P-256 signing / keygen / ECDH** via `ecdsa.SigningKey.sign_digest()` — not RSA/HMAC JWT ops SalesOS uses.

Validation label for this disposition package: **light validated** (static grep + lock/advisory review). No JWT library migration executed in this commit.

---

## 4. Pros / cons

| | Option A | Option B | Option C |
|---|---|---|---|
| **Pros** | Matches evidence; no auth-path churn; honest “no bump possible”; unblocks CI-16 close for ecdsa leg | Removes vulnerable package from tree; aligns with upstream jose guidance; PyJWT pattern already exists for webhooks | Keeps jose API surface if a clean override existed |
| **Cons** | Package remains in lock; `pip-audit` stays red on ecdsa until named ignore or B | Touches identity token encode/decode — not “tiny”; needs regression on login/JWKS/refresh | Override fights hard dep; fork/maintenance cost; may still import ecdsa at runtime |
| **Architecture change** | None | Yes (JWT backend migration) | Yes (dependency surgery) |
| **CI GREEN** | Not met (ecdsa ± starlette) | Clears ecdsa only after lock prune; starlette still CI-22 | Uncertain |

---

## 5. Explicit recommendation → **Accepted: Option A**

### Recommend / Accept: **Option A**

**Rationale (Security + Docs):**

1. **No ECDSA JWT algorithms in product paths.** Attack surface of PYSEC-2026-1325 requires exercising python-ecdsa signing/keygen/ECDH; SalesOS signs with **RS256** (RSA via cryptography PEM + jose) and **HS256** (HMAC).  
2. **No advisory fix to bump to.** Upstream ecdsa: side-channels out of scope, won’t-fix. Blind version bump is forbidden.  
3. **Option B is correct long-term hygiene** but is **not** clearly small/safe for an unattended CI-16 residual close — it changes identity token mint/verify. Deferred as a future hardening story if/when authorized.  
4. **Option C** is high-friction against a hard `python-jose` dependency without call-site migration.

### Explicit non-claims

- Does **not** start or expand **CI-22**.  
- Does **not** claim `pip-audit` / overall **CI GREEN**.  
- Does **not** authorize silent scanner disablement beyond a future **named** ignore for this CVE/PYSEC if engineering chooses that follow-on.  
- Does **not** implement Option B in this package.

---

## 6. Consequence

- Mint **DEC-057 Accepted** (this file).  
- CI-16: ecdsa leg **CLOSED-as-accepted-residual**; starlette remains **CI-22**; story **CLOSED** for CI-16 slice scope (Slices 1+3 complete; Slice 2 transferred).  
- R-21: ecdsa → accepted residual (monitor); starlette → CI-22; risk remains **Open — mitigating** until starlette cleared (and optional ecdsa ignore if authorized).  
- Update `SPRINT_05_DELIVERY_BOARD.md`, `RISK_REGISTER.md`, `EXECUTION_DAG.md`, `DECISION_LOG.md`.  
- Prefer **docs-only** commit (no allowlist / workflow code in this land).

### Follow-on (2026-08-01) — DEC-090

Named CI `--ignore-vuln PYSEC-2026-1325` authorized and landed under **DEC-090** after CI-22 Phase 1 cleared starlette (evidence run `30681284601`: sole remaining finding was ecdsa). `--strict` retained. See [`DEC-090-CI-PIP-AUDIT-ECDSA-NAMED-IGNORE.md`](DEC-090-CI-PIP-AUDIT-ECDSA-NAMED-IGNORE.md).
