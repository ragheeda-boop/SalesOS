# DEC-150 — After DEC-149: Is Stage 6 GHCR still a required Phase 0 exit criterion?

> **Status:** **Accepted — Option B** (ARB Decision Approved)  
> **Date:** 2026-08-02 (Proposed land); **Accepted:** 2026-08-02  
> **Board:** Architecture Review Board + Chief Architect (SalesOS / AQLIYA)  
> **Story / risk:** CI-08 / Phase 0 criteria **3.6**, **3.7**, **3.9**, **3.10** / **R-17** (GHCR leg)  
> **Authority:** **ARB Decision — DEC-150 Option B (Approved).** Stage 6 GHCR publish is **no longer** a required Phase 0 capability after DEC-149. Cross-ref DEC-149 (+ DEC-149a).  
> **Out of scope this Accepted land (execution):** GHCR ops fix / invent Packages tokens · app/backend/frontend business logic · inventing EOS **4.1/4.8** PASS · Phase 0 GO · Production GO · full CI GREEN claim · DEC-085  
> **In scope:** Governance rewrite (checklist / DAG / board / decision log / risk) + quarantine Stage 6 GHCR jobs in `ci.yml` (comments + `if: false`); do **not** break Railway/Vercel `deploy.yml`

---

## 1. Question (exact)

```text
After DEC-149:
Is Stage 6 GHCR still a required exit criterion?
Answer with evidence from:
- DEC-149
- PHASE_0_EXIT_CHECKLIST
- EXECUTION_DAG
- CI workflow
If required:
state why.
If obsolete:
propose governance change only.
```

---

## 2. ARB verdict (Accepted)

```text
ARB verdict:  [x] Option B — Stage 6 GHCR obsolete; authorize governance rewrite
              [ ] Option A — Stage 6 GHCR remains required
Accepted by:  ARB / Chief Architect (user-authorized Execution Assignment)
Date:         2026-08-02
Follow-on:    Governance migration land — rewrite 3.6/3.9/3.10; retire CI-08 as Phase 0 gate;
              quarantine ci.yml Stage 6 GHCR; canonical deploy path = DEC-149 Railway+Vercel
```

**Decision:** **Option B Accepted.** Stage 6 GHCR publish is **not** a required Phase 0 exit capability after DEC-149. Canonical live deploy = Backend → Railway + Frontend → Vercel (DEC-149 / DEC-149a). Residual GHCR 403 = **legacy / non-blocking** tech debt — not an ops close gate for Phase 0.

---

## 3. Current dual paths (honest — post Accepted)

| Path | What it does | GHCR dependency |
|---|---|---|
| **Canonical live deploy** (DEC-149 Accepted + DEC-149a CLOSED CONDITIONAL) | Backend → **Railway** (`railway up`); Frontend → **Vercel** (Git-primary). Staging deferred. | **Not required** |
| **CI Stage 6 publish** (`.github/workflows/ci.yml`) | Historical GHCR `:latest` + SHA push. | **QUARANTINED** (DEC-150 B) — `if: false`; not Phase 0 required |
| **Stage 7 E2E** | Playwright; previously `needs` Stage 6. | **Decoupled** from GHCR Stage 6; still OPEN for real services (criterion **3.7**) |

---

## 4. Evidence table (quotes + paths) — unchanged facts that justified B

| Source | Quote / fact | Path |
|---|---|---|
| **DEC-149 §4** | “Railway `railway up` path does **not** require GHCR.” | `docs/program/decisions/DEC-149-CANONICAL-DEPLOY-RAILWAY-VERCEL.md` |
| **DEC-149a** | CI-09 / **3.11 CLOSED CONDITIONAL**; deploy evidence @ `c3507ed` / run `30723120473` | `docs/program/DECISION_LOG.md` |
| **DEC-120 §3 B** | Alternate promote: Railway build-from-GitHub without GHCR | `docs/program/decisions/DEC-120-DEC016-RAILWAY-R14-CONTRADICTED.md` |

---

## 5. Option B governance changes (applied)

| Artifact | Change |
|---|---|
| **3.6** | Rewritten → canonical Railway+Vercel deploy validation; **CLOSED — SUPERSEDED** (evidence at **3.11** / DEC-149a) — not field GHCR green |
| **3.9** | Rewritten → CI GREEN (DEC-149 topology) = Stages 1–5 + Railway/Vercel deploy; **does not** require Stage 6 GHCR; remains **OPEN** (tip Stages 1–5 residual) |
| **3.10** | **CLOSED — SUPERSEDED** — CI-08 GHCR 403 no longer Phase 0 exit gate; residual 403 = legacy/non-blocking |
| **CI-08** board | **GOVERNANCE COMPLETED** (superseded DEC-150 B) — not ops SUCCESS close |
| **3.7** | Decoupled from GHCR Stage 6; remains OPEN (no E2E services) |
| **ci.yml Stage 6** | Quarantined (`if: false` + DEC-150 B comments); Stage 7 `needs` decoupled from Stage 6 |
| **DEC-104** | Option A no longer Phase 0 gate for CI-08; optional legacy hardening only |
| **R-17** | Mandatory GHCR publish leg **retired**; residual GHCR = legacy/non-blocking |

---

## 6. Explicit non-claims

1. Do **not** claim Phase 0 GO / Production GO / full CI GREEN.  
2. Do **not** invent Architecture PASS on EOS **4.1 / 4.8**.  
3. Do **not** claim field GHCR push SUCCESS or ops CLOSE of CI-08 via 403 clearance.  
4. Validation level this land: **governance implementation only**; runtime validation pending.

---

## 7. Recommendation (historical Proposed land)

**Superseded:** Proposed land deferred to ARB. **ARB selected Option B** — this Accepted document records that verdict and the governance migration authority.

| Field | Value |
|---|---|
| ARB verdict | **Option B Accepted** |
| Validation label this land | **governance implementation only / runtime validation pending** |
| Phase 0 | Remains **NO-GO** (**48/54** after 3.6/3.10 SUPERSEDED closes) |
