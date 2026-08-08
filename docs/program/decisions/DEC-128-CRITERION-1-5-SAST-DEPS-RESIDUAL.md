# DEC-128 — Phase 0 criterion 1.5: SAST + dependency scan wired; READY FOR REVIEW with residual

> **Status:** **Accepted** — Cursor packaging **COMPLETE** · Criterion 1.5 = **VERIFIED/CLOSED CONDITIONAL** (DEC-128a; Architecture PASS · Validation PASS_CONDITIONAL). Residual: post-align Security Scan pip-audit field-verify PENDING.  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Security P0 (SalesOS)  
> **Story / risk:** Phase 0 Exit Criterion **1.5** · R-21 (ecdsa mitigating) · R-24 Closed mitigating (CI-19 Semgrep alembic)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §1.5 · CI-02/16/17/18/19/21/22 CLOSED · DEC-057/090/098/105/109 · DEC-085 `set_config` · DEC-128a Orchestrator  
> **Out of scope this land:** Unconditional CLOSED · Production GO · whole-pipeline CI GREEN · CI-08 GHCR · PyJWT (DEC-057 Option B) · alembic Semgrep churn · DEC-085 / auth / CSRF / RBAC weaken

---

## 1. Decision

Accept criterion **1.5** as **Cursor COMPLETE** / **READY FOR REVIEW**: SAST + dependency vulnerability scanning are **wired** into both `security-scan.yml` and `ci.yml`, with Stage 5 security jobs field-green under **named** accepted residuals only.

| Pin | Value |
|---|---|
| Evidence required (checklist) | `security-scan.yml` + `ci.yml` security jobs green |
| Prior checklist status | ⬜ Partial (pip-audit findings remain) — **stale** vs closed CI-16/22 + DEC-090 |
| This land | (1) Package executive residual for 1.5; (2) Align `security-scan.yml` pip-audit to poetry export + DEC-090 named ignore (replace stale `PYSEC-2024-1`) |
| DEC-085 | **Intact** (not touched) |
| Criterion state | **VERIFIED/CLOSED CONDITIONAL** (DEC-128a) — residual post-align Security Scan pip-audit PENDING |

### Stories already CLOSED (do not reopen)

| Story | DEC | Role for 1.5 |
|---|---|---|
| CI-02 | DEC-025 | pip-audit toolchain (poetry export → findings) |
| CI-16 | DEC-051/056/057 | multipart/strawberry remediations; ecdsa Option A |
| CI-17 | DEC-031 | Bandit high gate green |
| CI-18 | DEC-030 | Semgrep SARIF upload |
| CI-19 | DEC-105 | Semgrep residual-close (alembic **11**) |
| CI-21 | DEC-041 | Gitleaks fixture (Security Scan) |
| CI-22 | DEC-109 | starlette floor cleared |
| CI policy | DEC-090 / DEC-098 | named pip-audit + Trivy ignores for ecdsa |

---

## 2. Accepted residual (honest; not finding-zero)

| Residual | Authority | Gate behavior |
|---|---|---|
| `ecdsa` Minerva **PYSEC-2026-1325** / **CVE-2024-23342** | DEC-057 Option A + DEC-090/098 | Named `--ignore-vuln` / `.trivyignore` only; `--strict` / Trivy exit-code **retained** |
| Semgrep Code Scanning **11** alembic-only | DEC-105 / DEC-103 | Semgrep ERROR/WARNING + SARIF **unchanged**; do not churn RLS migrations |
| Whole-pipeline CI GREEN | CI-08 GHCR 403 | Stage 6 publish still BLOCKED — **not** 1.5 |

**Do not claim:** finding-zero Semgrep · zero ignored advisories · Production GO · CI GREEN · criterion CLOSED.

---

## 3. Field evidence (pre-land / corroboration)

| Surface | Run / job | Result |
|---|---|---|
| CI Stage 5 pip-audit | [`30688863161`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30688863161) / `91339902722` @ `3084e5b` | **SUCCESS** — `No known vulnerabilities found, 1 ignored` (ecdsa) |
| CI Stages 1–5 (incl. all Stage 5 security) | [`30689682988`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30689682988) @ `7ba137b` | **SUCCESS** (pip-audit, Bandit, Secrets Scan, npm audit, Arch Compliance) |
| Tip Stage 5 (security jobs) | [`30704321096`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30704321096) @ `c842245` | pip-audit / Bandit / Secrets / npm audit / Arch **SUCCESS** (overall run red on unrelated Stage 1 Lint) |
| Security Scan workflow | [`30704321107`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30704321107) @ `c842245` | **SUCCESS** (secret-scan, pip-audit, npm-audit, sast-scan, sbom, report) |
| CI-19 Semgrep residual | [`30693735860`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30693735860) / sast `91352893256` @ `b9062d6` | CLI **11** blocking; CS open **11** alembic-only |

**Post-land field-verify (Validation / push):** Security Scan `pip-audit` after poetry-export alignment — expected green with **1 ignored** (ecdsa). **PENDING** until tip containing `fa266b5` is pushed and observed SUCCESS (DEC-128a residual; does not block CLOSED CONDITIONAL).

---

## 4. Validation

| Check | Result |
|---|---|
| Checklist packaging | **VERIFIED/CLOSED CONDITIONAL** (DEC-128a) |
| Workflow honesty land | `security-scan.yml` pip-audit → poetry export + `PYSEC-2026-1325` |
| Architecture | **PASS** ([architecture review 1.5](66828f20-228e-491f-a499-50c808d04c44)) |
| Validation | **PASS_CONDITIONAL** ([Validate 1.5](ff24e413-5483-4530-a507-dc64c5ed3fda)) |
| Narrow Docker pytest | **Not required** (no app/runtime change) |
| Production / Railway | **Not run** |
| Label | **light validated** (field Stage 5 + Security Scan corroboration; post-align Security Scan pip-audit PENDING push) |

**Production GO not claimed. CI GREEN not met. Unconditional CLOSED not claimed.**

---

## 5. Records

- Phase 0 criterion **1.5** → **VERIFIED/CLOSED CONDITIONAL** (DEC-128a; Phase 0 **23/54**)
- Residual explicit: *post-align Security Scan pip-audit field-verify PENDING until tip containing `fa266b5` is pushed and Security Scan pip-audit SUCCESS with poetry export + 1 ignored (ecdsa)*
- Adjacent checklist **3.5** remains open/residual narrative (Stage 5 cluster overlaps; does **not** auto-close 3.5 / 3.8)
- **Not claimed:** Unconditional CLOSED · Production GO · CI GREEN · Semgrep finding-zero

---

## 6. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | CI Stage 5 pip-audit | `.github/workflows/ci.yml` `security-pip-audit` + DEC-090 |
| EV-002 | CI Stage 5 Bandit / Secrets | `security-bandit` / `security-secrets-scan` (+ DEC-098 `.trivyignore`) |
| EV-003 | Security Scan SAST | `.github/workflows/security-scan.yml` `sast-scan` (Bandit + Semgrep) |
| EV-004 | Security Scan pip-audit align | poetry export + `--ignore-vuln PYSEC-2026-1325` (this land) |
| EV-005 | Field Stage 5 | Runs `30688863161`, `30689682988`, tip `30704321096` Stage 5 SUCCESS |
| EV-006 | CI-19 residual | DEC-105 / run `30693735860` (11 alembic) |
| EV-007 | Post-align Security Scan | PENDING (after push) |

---

## 7. Rollback

| Step | Action |
|------|--------|
| 1 | Revert DEC-128 docs + `security-scan.yml` pip-audit alignment |
| 2 | Do **not** remove DEC-090/098 named ignores from `ci.yml` / `.trivyignore` |
| Expected impact | Lose Security Scan lockfile parity; Stage 5 ci.yml behavior unchanged |

---

## 8. Risk

| Surface | Level | Note |
|---------|-------|------|
| Dependency | MEDIUM | ecdsa remains in lock (accepted); JWT paths RS256/HS256 only |
| SAST residual | LOW | Alembic Semgrep **11** visible in Code Scanning by design (DEC-105) |
| Workflow | LOW | Aligning security-scan pip-audit may surface new lock vulns — `--strict` fails honestly (desired) |
| Database / DEC-085 | N/A | Untouched |
