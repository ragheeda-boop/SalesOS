# SOC2 Type I — In-repo evidence package (STORY-14-05)

> **Classification:** Evidence pack (engineering assembly) — **not** an auditor opinion, attestation letter, or Type I certification.  
> **Story:** STORY-14-05 · Sprint-25 · Security + Program Director  
> **Tip pin (change-mgmt CI):** `4754b8b` via DevOps pack  
> **Honesty:** Not Production GO. `feature_ai_copilot` remains **False**. Stage 6 GHCR **SKIPPED** (DEC-150 B).  
> **Assembled:** 2026-08-03

## What this pack is

In-repo index of **controls design / process / pipeline evidence** suitable for SOC2 Trust Services Criteria (TSC) Type I *preparation*:

| Domain | File | Board intent |
|--------|------|--------------|
| Audit logging | [`01-audit-logging.md`](./01-audit-logging.md) | Completeness pointers + code hooks |
| Access review | [`02-access-review.md`](./02-access-review.md) | Documented process + sample evidence gaps |
| Change management | [`03-change-management.md`](./03-change-management.md) | Tip-line / CI / deploy / PR evidence |
| Gap inventory | [`04-gap-inventory.md`](./04-gap-inventory.md) | Explicit residuals for Program Director / auditor |
| Controls mapping (TSC sketch) | [`05-controls-mapping.md`](./05-controls-mapping.md) | CC-ish mapping → repo pointers (not auditor-ready matrix) |

## Authoritative crumbs / support

| Artifact | Path |
|----------|------|
| Story crumb | [`docs/program/PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md`](../../program/PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md) |
| Board hub | [`docs/program/PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md`](../../program/PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md) |
| DevOps CI/Deploy pack | [`docs/program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md`](../../program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md) |
| BE runtime hooks | [`docs/program/PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md`](../../program/PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md) (`d0070fa`) |
| Program A5 (Type I audit post-GA) | [`docs/program/MASTER_EXECUTION_PLAN.md`](../../program/MASTER_EXECUTION_PLAN.md) |

## Explicit non-claims

| Claim | Status |
|-------|--------|
| SOC2 Type I **certified** / auditor signed | **Forbidden** — Type I **audit** = **post-GA residual-external** |
| SOC2 Type II | **post-GA** — N/A at GA |
| Production GO / GA GO / Companion acceptance | **Forbidden** |
| Stage 6 GHCR as compliance gate | **SKIPPED** — do not reopen |
| Zero pentest criticals | Owned by STORY-14-04 — do not invent here |

## Validation label (this pack)

| Label | Meaning |
|-------|---------|
| **light validated** (assembly) | Paths, workflows, and tip-line URLs exist in-repo / linked; contents spot-checked against code/docs |
| **not validated** (ops samples) | Live access-review worksheets, 90d log export samples, auditor walkthroughs |
| **residual-external** | Formal Type I examination by CPA/auditor firm |

## How to use

1. Security / Program Director: walk TSC mapping + gap inventory with auditor scoping.  
2. DevOps: keep tip-line URLs current; Stage 6 stays quarantined.  
3. Do **not** paste this README into customer contracts as “SOC2 Type I complete.”
