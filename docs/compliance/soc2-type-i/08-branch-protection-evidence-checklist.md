# 08 — Branch-protection evidence checklist (TEMPLATE — UNSIGNED)

> **Status:** Checklist **LANDED** in-repo · dated org screenshots = **Program Director / org-admin residual** (settings live outside git).  
> **Story:** STORY-14-05 · links [`03-change-management.md`](./03-change-management.md) · gap PD-3.  
> **Honesty:** Checklist ≠ captured evidence · Not Type I certified · Not Production GO.

## Scope

Capture GitHub (or equivalent) **branch protection / required checks / review** settings for the default production branch of this monorepo. Screenshots and export JSON belong in the **offline auditor packet** — not committed here.

## Repo identity (fill at capture time)

| Field | Value |
|-------|-------|
| Org / owner | |
| Repository | |
| Default branch | `master` / other: ________ |
| Capture date (UTC) | YYYY-MM-DD |
| Captured by (name / role) | |
| Screenshot / export location | _(offline path)_ |

## Protection rules checklist

Mark each control as observed at capture time. Leave unchecked until screenshot corroborates.

| # | Control | Expected (typical SOC2 SDLC) | Observed | Evidence ref |
|---|---------|------------------------------|----------|--------------|
| 1 | Branch protection enabled on default branch | On | ☐ | |
| 2 | Require a pull request before merging | On | ☐ | |
| 3 | Required approving review count | ≥ 1 (org policy) | ☐ count: __ | |
| 4 | Dismiss stale reviews on new commits | On (if policy) | ☐ / N/A | |
| 5 | Require review from Code Owners | On **or** documented exception (no `CODEOWNERS` = gap) | ☐ / exception noted | |
| 6 | Require status checks to pass | On — CI Stages 1–5 + Security Scan as applicable | ☐ | |
| 7 | Require branches to be up to date before merge | Per org policy | ☐ / N/A | |
| 8 | Restrict who can push / bypass | Named admins only; bypass audited | ☐ | |
| 9 | Block force pushes | On | ☐ | |
| 10 | Block deletions of default branch | On | ☐ | |
| 11 | Require linear history / signed commits | Per org policy | ☐ / N/A | |
| 12 | Rulesets (if used instead of classic protection) | Documented + screenshot | ☐ / N/A | |

## Required status checks (list at capture)

| Check name | Required (Y/N) | Notes |
|------------|----------------|-------|
| | | |
| | | |
| Stage 6 GHCR Build Backend / Frontend | **N** — quarantined DEC-150 B; cite as intentional skip | Do not treat skip as unexplained failure |

## Related in-repo pointers (not substitutes for screenshots)

| Artifact | Path |
|----------|------|
| CI workflow | `.github/workflows/ci.yml` |
| Security Scan | `.github/workflows/security-scan.yml` |
| Deploy + Health Gate | `.github/workflows/deploy.yml` |
| Change-mgmt evidence | [`03-change-management.md`](./03-change-management.md) |
| CODEOWNERS | **gap** if absent at tip — note exception on row 5 |

## Attestation (signatures — residual until executed)

| Role | Name | Signature | Date (ISO) |
|------|------|-----------|------------|
| Org admin / DevOps | | ☐ UNSIGNED | |
| Program Director | | ☐ UNSIGNED | |
| Security (optional) | | ☐ UNSIGNED | |

## Explicit non-claims

- An unchecked checklist is **not validated** evidence.  
- Workflow YAML presence ≠ branch-protection enforcement.  
- Do **not** claim “SOC2 Type I certified” after storing this blank checklist.
