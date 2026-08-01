# DEC-104 — CI-08 / R-17 GHCR 403: ops options + honesty labels (no workflow weaken)

> **Status:** **Accepted** — recommended program path (**Option A** preferred; interim **Option D** honesty)  
> **Date:** 2026-08-01  
> **Board:** DevOps-SRE / Program (SalesOS / AQLIYA)  
> **Story / risk:** CI-08 (P0 BLOCKED) / CI-09 (P2 BLOCKED) / **R-17**  
> **Authority:** Sprint 04 triage #15/#16 · board CI-08 · Stage 6 field evidence run `30690622307` @ `927276f` · PRODUCTION_PLAN / staging runbooks (GHCR path)  
> **Out of scope this land:** inventing GHCR credentials/tokens · editing `.env` · `continue-on-error` on push · force-push · git config · Stage 7 E2E implementation · Railway image promote · alternate registry cutover code

---

## 1. Problem (evidence)

| Fact | Evidence |
|---|---|
| Stage 6 **image builds succeed** (backend + frontend) | CI run [`30690622307`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30690622307) @ `927276f`: Backend job `91345633439` build OK; Frontend job `91345633450` npm install + next build DONE |
| Jobs **fail only on GHCR push 403** | Same jobs: push to `ghcr.io/ragheeda-boop/salesos/{backend,frontend}` → **403 Forbidden** |
| Stage 7 E2E **skipped** | `needs: [build-backend, build-frontend]` — both Stage 6 red |
| Stages **1–5 green** on recent tip path | Board Progress (2026-08-01); whole-pipeline still red on Stage 6 publish |
| Workflow YAML already requests `packages: write` | `.github/workflows/ci.yml` top-level + Stage 6 job-level; login uses `secrets.GITHUB_TOKEN`; same pattern in `deploy-staging.yml` / `deploy-production.yml` |
| Staging deploy same class | Triage #15/#16 (`SPRINT_04_CI_TRIAGE.md`): build+SBOM OK; push 403 |

**Inference:** CI-08 is **not** a missing YAML `permissions: packages: write` bug. Repo-side permission blocks are already present. Remaining failure is **org/account/package-level GHCR write access** for Actions → outside application-code scope (R-17).

---

## 2. Options (tradeoffs)

### A) Org grants GHCR / Packages write for Actions (**preferred ops fix**)

| | |
|---|---|
| **What** | Human ops enables Actions → GHCR write for `ghcr.io/ragheeda-boop/salesos/*` (account/org Packages settings, package↔repo link, Actions “read and write” / packages permission as applicable). Re-run Stage 6; confirm push **200/success** without inventing PATs in docs. |
| **Pros** | Matches existing workflows, staging/prod runbooks, PRODUCTION_PLAN GHCR path; unblocks Stage 6 → Stage 7 gate and Deploy Staging/Production image publish; no AC weaken; no `continue-on-error`. |
| **Cons** | Requires human with GitHub owner/admin access; may need package creation/visibility/link steps; cannot be closed by repo agents alone. |
| **Risk** | Low security risk if least-privilege GITHUB_TOKEN retained (already declared). Do **not** commit long-lived PATs. |

### B) Split Stage 6: build-attest (required) vs push (optional / continue-on-error)

| | |
|---|---|
| **What** | `push: false` (or separate jobs) so image **build** is required green; push becomes optional or `continue-on-error`. |
| **Pros** | Could green Stage 6 build attestation and unblock Stage 7 Playwright (E2E does not pull GHCR today). |
| **Cons** | Changes program meaning of Stage 6 / “CI GREEN”; masks publish failure; Deploy Staging/Production still blocked; Stage 7 green ≠ deployable images. |
| **Gate** | **Not authorized by this DEC.** Requires a **separate** executive DEC revising Stage 6 AC **before** any workflow land. Prefer **not** to use `continue-on-error` on publish. |

### C) Alternate registry already approved in docs

| | |
|---|---|
| **What** | Point `REGISTRY` / deploy runbooks at Docker Hub, ECR, Railway registry, etc. |
| **Pros** | Escape hatch if GHCR permanently forbidden. |
| **Cons** | **No alternate registry is approved** in program/ops docs. Staging fill-in, soak, deploy-rollback, PRODUCTION_PLAN all assume `ghcr.io/ragheeda-boop/salesos/*`. Cutover would be a multi-workflow + secrets + VPS auth program story. |
| **Gate** | **Rejected** until a named registry DEC + ops approval. |

### D) Park Stage 6/7 as ops-blocked; dual honesty labels (**interim**)

| | |
|---|---|
| **What** | Keep CI-08 **BLOCKED**. Distinguish **CI GREEN (code path)** = Stages 1–5 (+ non-publish gates) from **CI GREEN (full incl. publish)** = Stages 1–7 + GHCR push + deploy publish. |
| **Pros** | Honest progress reporting while A is pending; avoids false whole-pipeline GREEN; pairs with A. |
| **Cons** | Does not unblock Stage 7 or staging image promote by itself. |
| **Gate** | **Accepted as interim framing** under this DEC until A field-verifies. |

---

## 3. Decision

1. **Recommend Option A** as the sole preferred closure path for CI-08 / R-17 GHCR leg.  
2. **Adopt Option D** honesty labels immediately for program reporting (docs only).  
3. **Do not implement Option B** without a follow-on DEC that revises Stage 6 AC.  
4. **Reject Option C** until an approved alternate-registry DEC exists.  
5. **Do not** claim whole-pipeline **CI GREEN (full incl. publish)**. Do not invent credentials. Do not weaken auth/CSRF/RBAC/audit.

---

## 4. Human ops checklist (Option A) — executable, no secrets in git

Owner: **DevOps-SRE** (GitHub account/org admin for `ragheeda-boop`).

1. Confirm Packages / GHCR is enabled for the owner of namespace `ragheeda-boop`.  
2. Confirm Actions workflow permissions allow **read and write** (or equivalent that grants `packages: write` to `GITHUB_TOKEN`) for this repository.  
3. Ensure packages `salesos/backend` and `salesos/frontend` under `ghcr.io/ragheeda-boop/` either do not yet exist (first successful push creates) **or** are linked to this repo with Actions write.  
4. Do **not** paste PATs into the repo; prefer default `GITHUB_TOKEN` already used by workflows.  
5. Field-verify on `master`: CI Stage 6 both jobs **SUCCESS** including push; optionally Deploy Staging push jobs. Record run IDs on the board.  
6. Only then consider CI-08 → CLOSED and R-17 GHCR leg mitigated (SSH/VPS leg remains CI-09).

---

## 5. Honesty labels (Option D)

| Label | Meaning |
|---|---|
| **CI GREEN (code path)** | Stages 1–5 (and other non-publish gates) green on a named run — **does not** include GHCR push or Stage 7 |
| **CI GREEN (full incl. publish)** | Stages 1–7 green **and** GHCR push success for backend+frontend (and deploy publish as scoped) |
| Current | Stages 1–5 have been green on tip evidence; Stage 6 **build** proven / **push** ops-blocked → **neither full label claimed**. Prefer: “Stages 1–5 green; Stage 6 build proven; publish **BLOCKED** (CI-08).” |

Production GA / external pilot remain **NO-GO** (unchanged). Phase 0 RLS exit **GO** (DEC-086) unchanged.

---

## 6. Validation

| Check | Result |
|---|---|
| Workflow / secrets / credentials changed | **None** |
| Pipeline re-run for this DEC | **Not run** |
| Label | **docs only / not validated** for pipeline |

**CI GREEN (full incl. publish):** not met.  
**CI GREEN (code path):** not claimed as a closed program gate by this DEC (use named Stage evidence only).
