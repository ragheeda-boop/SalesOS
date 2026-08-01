# DEC-150 — After DEC-149: Is Stage 6 GHCR still a required Phase 0 exit criterion?

> **Status:** **Proposed — pending ARB / Chief Architect**  
> **Date:** 2026-08-02  
> **Board:** Architecture Review Board + Chief Architect (SalesOS / AQLIYA) — program/governance scribe land  
> **Story / risk:** CI-08 / Phase 0 criteria **3.6**, **3.7**, **3.9**, **3.10** / **R-17** (GHCR leg)  
> **Authority:** User ruling (Cursor must not decide Stage 6 necessity) · DEC-149 (+ single-env amend) · PHASE_0_EXIT_CHECKLIST · EXECUTION_DAG · `.github/workflows/ci.yml` Stage 6 · DEC-104 · DEC-120  
> **Out of scope this land:** Accepting Option A or B · closing / retiring CI-08 · rewriting exit criteria as Accepted · GHCR ops fix · workflow / app code changes · inventing EOS **4.1/4.8** PASS · Phase 0 GO · Production GO · full CI GREEN claim · DEC-085

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
No implementation.
```

**This paper does not answer the question as Accepted.** It packages evidence and options for ARB / Chief Architect.

---

## 2. Current dual paths (honest)

| Path | What it does today | GHCR dependency |
|---|---|---|
| **Canonical live deploy** (DEC-149 Accepted + DEC-149a CLOSED CONDITIONAL) | Backend → **Railway** (`railway up` cwd `salesos/`); Frontend → **Vercel** (Git-primary). Staging Railway **deferred** (single-env). | **Not required** for the live path — DEC-149 §4: “Railway `railway up` path does **not** require GHCR.” |
| **CI Stage 6 publish** (`.github/workflows/ci.yml`) | On `master`/`main`, after Stages 1–5 (+ arch jobs): build + **push** backend/frontend images to `ghcr.io/ragheeda-boop/salesos/{backend,frontend}` tags **`:latest`** and **SHA (7-char)**; Stage 7 E2E `needs` Stage 6. | **Required by current YAML** (`push: true`, `packages: write`). Field push historically **403** (CI-08). |
| **Historical staging image push** | Previously part of Deploy Staging / GHCR promote narrative (triage #15/#16). | Staging auto-deploy **removed/deferred** by DEC-149 single-env amend (`deploy-staging.yml` dispatch + soft-skip). GHCR 403 on staging push may be **moot for live deploy** if Stage 6 itself is retired — **ARB decides**, not Cursor. |

**Dual-path honesty:** Live production can succeed (and did under DEC-149a) while Stage 6 GHCR publish remains red or skipped. Checklist still treats Stage 6 push as Phase 0 exit criteria until ARB revises them.

---

## 3. Evidence table (quotes + paths)

| Source | Quote / fact | Path |
|---|---|---|
| **DEC-149 §4** | “CI-08 (GHCR) remains a **separate** ops blocker for Stage 6 publish (DEC-104); Railway `railway up` path does **not** require GHCR.” | `docs/program/decisions/DEC-149-CANONICAL-DEPLOY-RAILWAY-VERCEL.md` |
| **DEC-149 §6** | “`ci.yml` Stage 6 \| **Unchanged** (GHCR publish orthogonal — CI-08)” | same |
| **DEC-149 §1a** | Single-env: production Railway only; staging deferred; `deploy-staging.yml` no longer auto-runs on push | same |
| **DEC-149a** | CI-09 / **3.11 CLOSED CONDITIONAL**; “Does **not** close **3.6/3.9/3.10** (CI-08 GHCR)” | `docs/program/DECISION_LOG.md` (DEC-149a) |
| **Checklist 3.6** | “Stage 6: Docker Build + Push green \| Backend + Frontend images build + push \| ☐ CI-08 BLOCKED (GHCR 403)” | `docs/program/PHASE_0_EXIT_CHECKLIST.md` |
| **Checklist 3.7** | “Stage 7: E2E green” — Stage-6-dep (Playwright needs Stage 6 path) | same |
| **Checklist 3.9** | “Full pipeline: CI GREEN (incl. publish) \| Stages 1–7 all green on same run \| ⬜ CI-08 BLOCKED” | same |
| **Checklist 3.10** | “CI-08 GHCR 403 resolved \| Stage 6 push succeeds (DEC-104 Option A)” \| OPEN ops/human | same |
| **Checklist 3.11** | CLOSED CONDITIONAL (DEC-149a); explicitly does **not** close 3.6/3.9/3.10 | same |
| **EXECUTION_DAG** | CI-08 GHCR 403 **BLOCKED**; “Also blocks primary image promote path for Railway; alternate = Railway build-from-GitHub” | `docs/program/EXECUTION_DAG.md` |
| **EXECUTION_DAG** | “CI GREEN (full incl. publish) **BLOCKED** \| Stage 6 GHCR push (CI-08) + Stage 7 …” | same |
| **ci.yml Stage 6** | `REGISTRY: ghcr.io`; `push: true`; tags `:latest` + SHA; jobs `build-backend` / `build-frontend`; Stage 7 `needs: [build-backend, build-frontend]` | `.github/workflows/ci.yml` |
| **DEC-104** | Prefer Option A (org Packages write); Option D dual honesty (code path vs full+publish); do **not** soften push without AC DEC | `docs/program/decisions/DEC-104-CI-08-GHCR-OPS-OPTIONS.md` |
| **DEC-120 §3 B** | Primary promote: “CI Stage 6 → GHCR → Railway pull — **BLOCKED by CI-08**.” Alternate authorized: “Railway build-from-GitHub / redeploy from tip SHA without GHCR.” | `docs/program/decisions/DEC-120-DEC016-RAILWAY-R14-CONTRADICTED.md` |
| **Board CI-08** | Field Deploy Staging `30721601875` BE+FE push still **403**; do **not** CLOSE on link alone | `docs/program/SPRINT_05_DELIVERY_BOARD.md` |

**Inference for ARB (not a Cursor verdict):** Evidence shows (1) checklist/DAG/CI still encode Stage 6 GHCR as required for Phase 0 / full CI GREEN; (2) DEC-149 explicitly kept Stage 6 orthogonal and stated Railway live path does not need GHCR; (3) staging GHCR push is no longer on the canonical auto path. Whether (1) should yield to (2)+(3) is the ARB question.

---

## 4. Options (for ARB only)

### Option A — Stage 6 remains a required capability

**Meaning:** Keep Phase 0 exit criteria that demand GHCR Docker build+push (and publish-inclusive CI GREEN).

**Why this could be correct:**

- Checklist **3.6 / 3.9 / 3.10** still require Stage 6 push SUCCESS; **3.7** is Stage-6-dep.
- `ci.yml` still publishes `:latest` + SHA to GHCR as the artifact promote surface.
- DEC-104 Option A remains the preferred ops closure for CI-08 if publish stays in-scope.
- DEC-120 named GHCR→Railway as the *primary* image promote path (even though an alternate exists).
- DEC-149 called Stage 6 “orthogonal,” not “retired” — it closed deploy topology (**3.11**), not publish criteria.

**What stays (if A Accepted later):**

| Criterion / story | Stays |
|---|---|
| **3.6** Stage 6 Docker Build + Push | Required (ops CI-08) |
| **3.9** CI GREEN (incl. publish) | Required |
| **3.10** CI-08 GHCR 403 resolved | Required (DEC-104 Option A field SUCCESS) |
| **3.7** Stage 7 E2E | Still Stage-6-dep unless separately revised |
| **CI-08** | Remains BLOCKED until push SUCCESS — **ops**, not governance retirement |
| **R-17** GHCR leg | Remains open until push SUCCESS |

**Implementation note:** No code/workflow change in this land. Ops may still pursue DEC-104 Option A **only if** ARB selects A (or explicitly authorizes interim ops while A stands).

---

### Option B — Stage 6 GHCR obsolete / legacy relative to DEC-149 live path

**Meaning:** Treat GHCR Stage 6 publish (and CI-08 as a Phase 0 exit gate) as superseded by Railway+Vercel canonical deploy; **governance change only** in a follow-on Accepted DEC — **no implementation in this land**.

**Why this could be correct:**

- Live deploy path (Railway+Vercel) does not consume GHCR images (DEC-149 §4).
- Staging GHCR auto-push path is deferred/removed (DEC-149 §1a / §6).
- DEC-120 already authorized Railway build-from-GitHub as alternate promote — aligns with `railway up`.
- Continuing to block Phase 0 on GHCR 403 may force ops work that does not serve the accepted topology.
- Honesty: GHCR **403 may be moot** for live deploy if Stage 6 publish is retired as an exit criterion.

**Governance-only change sketch (propose only — do not apply until ARB Accepts):**

| Artifact | Proposed change (B only, later land) |
|---|---|
| **3.6** | Rewrite: either retire, or redefine as “image build attest without GHCR push,” or “N/A — Railway/Vercel deploy path” per ARB wording |
| **3.9** | Rewrite “CI GREEN (incl. publish)” so publish ≠ GHCR, or drop publish-inclusive gate |
| **3.10** | Retire or reframe CI-08 GHCR 403 as non-Phase-0 / tech-debt |
| **CI-08** board | Retire / CLOSED-as-superseded (governance) — **not** ops SUCCESS close |
| **3.7** | Decouple from GHCR Stage 6 or redefine E2E evidence independently |
| **ci.yml Stage 6** | Out of scope here — separate implementation DEC if B Accepted |
| **DEC-104** | Supersede Option A as Phase 0 gate (may keep optional hardening) |

**Explicit:** Cursor must **not** rewrite checklist rows to CLOSED/obsolete, must **not** edit workflows, and must **not** mark CI-08 obsolete in this Proposed land.

---

## 5. Explicit non-actions (Cursor / agents)

Until ARB / Chief Architect **Accepts** this DEC (or a follow-on) selecting A or B:

1. Do **not** decide whether Stage 6 GHCR is still required.  
2. Do **not** fix GHCR / Packages Write / invent tokens.  
3. Do **not** implement Option B workflow retirement or Option A soften (DEC-104 B).  
4. Do **not** CLOSE or mark CI-08 obsolete.  
5. Do **not** invent Architecture PASS on EOS **4.1 / 4.8**.  
6. Do **not** claim Phase 0 GO / Production GO / full CI GREEN.

**CI-08 interim board state for this paper:** **BLOCKED BY GOVERNANCE (Stage 6 necessity)** pending DEC-150 ARB answer — in addition to residual field GHCR 403. Honesty: if B is later Accepted, the 403 may be moot; until then, do not CLOSE.

---

## 6. Recommendation

**None / defer to ARB.**

This land is a **Proposed decision paper** only. Scribe does **not** pick Option A or Option B as Accepted.

| Field | Value |
|---|---|
| Scribe recommendation | **Defer** |
| Required next actor | **ARB / Chief Architect** |
| Validation label this land | **docs only / not validated** (pipeline untouched) |
| Phase 0 | Remains **NO-GO** (**46/54** pin unchanged by this paper) |

---

## 7. Records touched (this Proposed land)

| File | Change |
|---|---|
| This DEC | Proposed brief created |
| `SPRINT_05_DELIVERY_BOARD.md` | CI-08 crumb → BLOCKED BY GOVERNANCE (Stage 6 necessity) pending DEC-150 |
| `PHASE_0_EXIT_CHECKLIST.md` | Tiny honesty crumb on 3.6/3.10 / Remaining inventory — not CLOSED |
| `EXECUTION_DAG.md` | CI-08 block class note → governance necessity pending DEC-150 |
| `DECISION_LOG.md` | DEC-150 Proposed entry |
| `RISK_REGISTER.md` | R-17 GHCR leg — pending DEC-150 (optional crumb) |

**App code / workflows:** unchanged.

---

## 8. ARB decision block (to fill when Accepted)

```text
ARB verdict:  [ ] Option A — Stage 6 GHCR remains required
              [ ] Option B — Stage 6 GHCR obsolete; authorize governance rewrite only
              [ ] Other: _______________________
Accepted by:  ________________  Date: __________
Follow-on:    (if B) new Accepted DEC amending 3.6/3.9/3.10 + CI-08 retire text
              (if A) ops resume DEC-104 Option A; keep CI-08 BLOCKED until push SUCCESS
```
