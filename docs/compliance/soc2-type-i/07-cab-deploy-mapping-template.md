# 07 — CAB ↔ deploy mapping (TEMPLATE — UNSIGNED)

> **Status:** Template **LANDED** in-repo · filled CAB minutes / ticket archive = **Program Director residual**.  
> **Story:** STORY-14-05 · links [`03-change-management.md`](./03-change-management.md) · gap PD-2.  
> **Honesty:** Pipeline tip-line ≠ CAB approval · Not Type I certified · Not Production GO.

## Purpose

Map each **production deploy** (git tip SHA + Deploy workflow run) to a **change ticket / CAB record** so auditors can trace authorization → artifact → Health Gate.

## How to use

1. For each production roll in the Type I examination window, add one row.  
2. Attach or link CAB minutes / RFC / change ticket offline if they contain customer data.  
3. Prefer tip SHAs already cited in the DevOps pack; do not invent SUCCESS URLs.  
4. Sign / approve offline; keep this file as a blank template or aggregate index without secrets.

## Canonical pipeline pointers (do not duplicate as CAB)

| Artifact | Path / tip |
|----------|------------|
| DevOps evidence pack | [`PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md`](../../program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md) |
| Change-mgmt index | [`03-change-management.md`](./03-change-management.md) |
| Example tip pin (CI/Deploy) | `4754b8b` (update when PD refreshes the window) |
| Deploy workflow | `.github/workflows/deploy.yml` + Health Gate |
| Stage 6 GHCR | **SKIPPED** (DEC-150 B) — not a CAB substitute |

## Mapping worksheet

| Deploy date (UTC) | Tip SHA | Deploy Actions run URL | Health Gate result | Change / CAB ticket ID | CAB decision (approve / emergency / rollback) | Approver | Evidence stored (path) |
|-------------------|---------|------------------------|--------------------|------------------------|-----------------------------------------------|----------|------------------------|
| | | | ☐ pass ☐ fail ☐ N/A | | | | |
| | | | ☐ pass ☐ fail ☐ N/A | | | | |
| | | | ☐ pass ☐ fail ☐ N/A | | | | |

## Emergency / break-glass changes

| Date | Tip SHA | Reason | Post-facto CAB ticket | Retro-approved (Y/N) | Owner |
|------|---------|--------|----------------------|----------------------|-------|
| | | | | ☐ UNSIGNED | |

## Period attestation (signatures — residual until executed)

| Field | Value |
|-------|-------|
| Examination / evidence window | YYYY-MM-DD → YYYY-MM-DD |
| Rows completed | n / expected |
| Gaps explained | |
| Program Director sign-off | ☐ UNSIGNED — name / date: ________ |
| Engineering / DevOps corroboration | ☐ UNSIGNED — name / date: ________ |

## Explicit non-claims

- Green CI/Deploy alone is **not** CAB approval.  
- An empty mapping table means PD-2 remains **not validated**.  
- Do **not** claim Type I certified from this template.
