# DEC-147 — Phase 0 criterion 3.5: Stage 5 Security Scan green (READY FOR REVIEW CONDITIONAL)

> **Status:** **Accepted** — Cursor packaging **COMPLETE** · Criterion 3.5 = **READY FOR REVIEW** (Architecture PENDING · Validation PENDING). Expected close path: **VERIFIED/CLOSED CONDITIONAL** after Arch+Val+Orchestrator — not self-CLOSED.  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / CI-adjacent (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **3.5** · Stage 5 Security Scan green under named accepted residuals  
> **Authority:** PHASE_0_EXIT_CHECKLIST §3.5 · DEC-057/090/098/105/128 · CI-02/16/17/18/19/21 CLOSED · DEC-085 `set_config`  
> **Out of scope this land:** Unconditional CLOSED · Production GO · whole-pipeline CI GREEN · **3.8** same-run Stages 1–5 tip green · **3.7** E2E services · CI-08/CI-09 ops · inventing EOS **4.1/4.8** ARB · DEC-085 / auth / CSRF / RBAC weaken

---

## 1. Decision

Package criterion **3.5** as **Cursor COMPLETE** / **READY FOR REVIEW CONDITIONAL**: CI Stage 5 security jobs and the dedicated `security-scan.yml` workflow are field-green under **named** accepted residuals only (ecdsa Minerva + Semgrep alembic **11**). Does **not** auto-close **3.8** (code-path Stages 1–5 same run on tip) or **3.9** (publish path).

| Pin | Value |
|---|---|
| Evidence required (checklist) | pip-audit (named ignore only), Bandit, Gitleaks, Semgrep residual-only |
| Overlap | Criterion **1.5** CLOSED CONDITIONAL (DEC-128a) wires scans; **3.5** is Stage 5 / Security Scan **green under residual** — explicitly left open by DEC-128 |
| This land | Docs packaging + gh corroboration only (no workflow soften; no finding-zero claim) |
| DEC-085 | **Intact** (not touched) |
| Criterion state | **READY FOR REVIEW** — do **not** claim VERIFIED/CLOSED until Arch+Val+Orchestrator |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| CI Stage 5 pip-audit SUCCESS (named ignore only) | **Yes** — tip-pushed `30704321096` @ `c842245`: `No known vulnerabilities found, 1 ignored` (`PYSEC-2026-1325`) |
| CI Stage 5 Bandit / Secrets / npm audit SUCCESS | **Yes** — same run |
| Security Scan workflow SUCCESS (secret-scan / pip-audit / sast / sbom / report) | **Yes** — `30704321107` @ `c842245` |
| Semgrep residual-only (alembic) | **Yes** — DEC-105 field-verify `30693735860` CLI **11** / CS **11** alembic-only |
| Tip containing `fa266b5` Security Scan pip-audit (poetry-export align) | **Pending push** — same residual as DEC-128a |
| Stages 1–5 same-run tip green (**3.8**) | **No** — last pushed tip Stage 1 Backend Lint **failure**; local tip unpushed |
| Production GO / CI GREEN / unconditional CLOSED | **No** |

**Not claimed:** finding-zero Semgrep · zero ignored advisories · Production GO · CI GREEN · **3.7/3.8/3.9** closed · Phase 0 exit.

---

## 2. Accepted residual (honest; not finding-zero)

| Residual | Authority | Gate behavior |
|---|---|---|
| `ecdsa` Minerva **PYSEC-2026-1325** / **CVE-2024-23342** | DEC-057 Option A + DEC-090/098 | Named `--ignore-vuln` / `.trivyignore` only; `--strict` / Trivy exit-code **retained** |
| Semgrep Code Scanning **11** alembic-only | DEC-105 / DEC-103 | Semgrep ERROR/WARNING + SARIF **unchanged**; do not churn RLS migrations |
| Post-align Security Scan pip-audit (`fa266b5`) | DEC-128a | **PENDING** until tip containing `fa266b5` is pushed and Security Scan pip-audit SUCCESS with poetry export + 1 ignored |
| Adjacent **3.8** tip code-path | last push `c842245` Lint red; local tip ahead unpushed | Does **not** auto-close from 3.5 |
| Whole-pipeline incl. publish | CI-08 GHCR 403 | Stage 6/7/3.9 still BLOCKED |

---

## 3. Field evidence (gh reads; prefer not trigger new full CI)

| Surface | Run / job | Result |
|---|---|---|
| CI Stage 5 (pip-audit / Bandit / Secrets / npm / Arch Compliance) | [`30704321096`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30704321096) @ `c842245` | All listed Stage 5 security jobs **SUCCESS** (overall run red on Stage 1 Backend Lint — out of 3.5 scope) |
| CI Stage 5 pip-audit log | job `91380692806` | `No known vulnerabilities found, 1 ignored` |
| Security Scan workflow | [`30704321107`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30704321107) @ `c842245` | **SUCCESS** (secret-scan, pip-audit, npm-audit, sast-scan, sbom, report) |
| Stages 1–5 same-run (historical corroboration for adjacent 3.8) | [`30689682988`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30689682988) @ `7ba137b` | Stages 1–5 **SUCCESS**; Stage 6 **FAILURE** (CI-08); Stage 7 skipped — **not** claimed as tip 3.8 |
| CI-19 Semgrep residual | [`30693735860`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30693735860) / sast `91352893256` @ `b9062d6` | CLI **11** blocking; CS open **11** alembic-only |

**Post-land field-verify (Validation / push):** Security Scan `pip-audit` after poetry-export alignment — expected green with **1 ignored** (ecdsa). **PENDING** until tip containing `fa266b5` (and this land) is pushed. Prefer **not** push this land.

---

## 4. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Leave 3.5 open indefinitely because 1.5 already CONDITIONAL | Rejected — checklist explicitly says 1.5 does not auto-close 3.5; Stage 5 green packaging was missing |
| (b) Claim VERIFIED/CLOSED / CI GREEN / finding-zero this land | Rejected — Arch+Val+Orchestrator; tip post-align PENDING; residuals named |
| (c) Soften Semgrep / remove `--strict` / widen ignores | Rejected — security weaken |
| (d) Package READY FOR REVIEW CONDITIONAL with gh Stage 5 + Security Scan evidence | **Approved** |
| (e) Land 3.8 instead | Rejected for this turn — tip last-push Stages 1–5 **not** all green (Backend Lint failure); 3.5 is the executable Stage 5 slice |

---

## 5. Validation

| Check | Result |
|---|---|
| Checklist packaging | **READY FOR REVIEW** (this land) |
| Architecture | **PENDING** |
| Validation | **PENDING** (expected PASS_CONDITIONAL: tip post-`fa266b5` Security Scan pip-audit PENDING push) |
| Narrow Docker pytest | **Not required** (no app/runtime change) |
| Production / Railway | **Not run** |
| Label | **light validated** (gh Stage 5 + Security Scan corroboration; tip post-align PENDING) |

**Production GO not claimed. CI GREEN not met. Unconditional CLOSED not claimed.**

---

## 6. Records

- Phase 0 criterion **3.5** → **READY FOR REVIEW** (Phase 0 remains **43/54** until Orchestrator CLOSE)
- Expected Orchestrator path: **VERIFIED/CLOSED CONDITIONAL** with residual *post-align Security Scan pip-audit field-verify PENDING until tip containing `fa266b5` is pushed*
- Adjacent **3.7** BLOCKED (E2E needs Stage 6 builds → CI-08; job has no backend services)
- Adjacent **3.8** OPEN (tip code-path not green on last push)
- Ops **3.6 / 3.9 / 3.10** CI-08 BLOCKED · **3.11** CI-09 BLOCKED
- EOS **4.1 / 4.8** ARB — do not invent
- **Not claimed:** Unconditional CLOSED · Production GO · CI GREEN · Semgrep finding-zero · Phase 0 exit

---

## 7. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | CI Stage 5 pip-audit | `.github/workflows/ci.yml` `security-pip-audit` + DEC-090 |
| EV-002 | CI Stage 5 Bandit / Secrets | `security-bandit` / `security-secrets-scan` (+ DEC-098 `.trivyignore`) |
| EV-003 | Security Scan SAST + Gitleaks | `.github/workflows/security-scan.yml` `sast-scan` / `secret-scan` |
| EV-004 | Field tip Stage 5 | Run `30704321096` @ `c842245` Stage 5 SUCCESS |
| EV-005 | Field tip Security Scan | Run `30704321107` @ `c842245` SUCCESS |
| EV-006 | CI-19 residual | DEC-105 / run `30693735860` (11 alembic) |
| EV-007 | Post-align Security Scan | PENDING (after push of tip containing `fa266b5`) |
| EV-008 | This DEC | `docs/program/decisions/DEC-147-CRITERION-3-5-STAGE5-SECURITY-SCAN.md` |

---

## 8. Rollback

| Step | Action |
|------|--------|
| 1 | Revert DEC-147 docs crumbs (checklist / board / DAG / DECISION_LOG / this file) |
| 2 | Do **not** remove DEC-090/098 named ignores or Semgrep gates |
| Expected impact | 3.5 returns informal Open; Stage 5 CI behavior unchanged |

---

## 9. Risk

| Surface | Level | Note |
|---------|-------|------|
| Dependency | MEDIUM | ecdsa remains in lock (accepted); JWT paths RS256/HS256 only |
| SAST residual | LOW | Alembic Semgrep **11** visible in Code Scanning by design (DEC-105) |
| Tip drift | MEDIUM | Local tip **49** ahead of `origin/master` (`c842245`); Backend Lint red on last push may block adjacent **3.8** until remediated + pushed |
| Overclaim | LOW | Explicit CONDITIONAL / no CI GREEN / no Production GO |

---

## 10. Next PARALLEL

| Track | Note |
|---|---|
| Architecture / Validation / Orchestrator | Gate 3.5 → CLOSED CONDITIONAL |
| **3.8** tip code-path | Needs Backend Lint green + Stages 1–5 same run on pushed tip (incl. `test-architecture`) |
| **3.7** | BLOCKED behind Stage 6 / CI-08 unless E2E `needs:` redesigned + services added |
| EOS **4.1/4.8** | ARB — do not invent |
| Ops CI-08 / CI-09 | Human/ops |
