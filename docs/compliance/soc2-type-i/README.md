# SOC2 Type I — In-repo evidence package (STORY-14-05)

> **Classification:** Evidence pack (engineering assembly) — **not** an auditor opinion, attestation letter, or Type I certification.  
> **Story:** STORY-14-05 · Sprint-25 · Security + Program Director  
> **Tip pin (change-mgmt CI):** `4754b8b` via DevOps pack  
> **Honesty:** Not Production GO. `feature_ai_copilot` remains **False**. Stage 6 GHCR **SKIPPED** (DEC-150 B).  
> **Assembled:** 2026-08-03 · **PD templates LANDED** (unsigned) — signatures / live samples still residual.

## What this pack is

In-repo index of **controls design / process / pipeline evidence** suitable for SOC2 Trust Services Criteria (TSC) Type I *preparation*:

| Domain | File | Board intent |
|--------|------|--------------|
| Audit logging | [`01-audit-logging.md`](./01-audit-logging.md) | Completeness pointers + code hooks |
| Access review | [`02-access-review.md`](./02-access-review.md) | Documented process + sample evidence gaps |
| Change management | [`03-change-management.md`](./03-change-management.md) | Tip-line / CI / deploy / PR evidence |
| Gap inventory | [`04-gap-inventory.md`](./04-gap-inventory.md) | Explicit residuals for Program Director / auditor |
| Controls mapping (TSC sketch) | [`05-controls-mapping.md`](./05-controls-mapping.md) | CC-ish mapping → repo pointers (not auditor-ready matrix) |

### Program Director templates (unsigned)

| Template | File | Closes in-repo? | Still residual |
|----------|------|-----------------|----------------|
| Quarterly access-review worksheet | [`06-access-review-worksheet-template.md`](./06-access-review-worksheet-template.md) | Template only | Signed / filled packet (PII offline) |
| CAB ↔ deploy mapping | [`07-cab-deploy-mapping-template.md`](./07-cab-deploy-mapping-template.md) | Template only | Filled ticket archive + signatures |
| Branch-protection evidence checklist | [`08-branch-protection-evidence-checklist.md`](./08-branch-protection-evidence-checklist.md) | Checklist only | Dated org screenshots |
| 90d audit-log export runbook | [`09-audit-log-export-90d-runbook.md`](./09-audit-log-export-90d-runbook.md) | Runbook only | Live export sample (OPS-1) |

## Authoritative crumbs / support

| Artifact | Path |
|----------|------|
| Story crumb | [`docs/program/PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md`](../../program/PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md) |
| Board hub | [`docs/program/PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md`](../../program/PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md) |
| DevOps CI/Deploy pack | [`docs/program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md`](../../program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md) |
| BE runtime hooks | [`docs/program/PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md`](../../program/PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md) (`d0070fa`) |
| AI honesty (canonical) | [`docs/audit/ga-engineering-audit/AI_HONESTY.md`](../audit/ga-engineering-audit/AI_HONESTY.md) — `feature_ai_copilot=False`; Decision package **STUB** |
| LLM regression harness (non-prod) | [`docs/program/PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`](../../program/PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md) |
| AI failover harness (non-prod) | [`docs/program/PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md`](../../program/PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md) |
| Program A5 (Type I audit post-GA) | [`docs/program/MASTER_EXECUTION_PLAN.md`](../../program/MASTER_EXECUTION_PLAN.md) |

## Explicit non-claims

| Claim | Status |
|-------|--------|
| SOC2 Type I **certified** / auditor signed | **Forbidden** — Type I **audit** = **post-GA residual-external** |
| SOC2 Type II | **post-GA** — N/A at GA |
| Production GO / GA GO / Companion acceptance | **Forbidden** |
| Stage 6 GHCR as compliance gate | **SKIPPED** — do not reopen |
| Zero pentest criticals | Owned by STORY-14-04 — do not invent here |
| Live LLM / copilot GA / Decision STUB as production AI | **Forbidden** — cite `AI_HONESTY.md`; harnesses are CI/non-prod only |
| Templates = executed control samples | **Forbidden** — signatures / screenshots / live export still residual |

## Validation label (this pack)

| Label | Meaning |
|-------|---------|
| **light validated** (assembly) | Paths, workflows, and tip-line URLs exist in-repo / linked; contents spot-checked against code/docs |
| **not validated** (ops samples) | Live access-review worksheets, 90d log export samples, auditor walkthroughs |
| **templates LANDED** | Unsigned worksheets / checklists / runbooks present under this directory |
| **residual-external** | Formal Type I examination by CPA/auditor firm |

## How to use

1. Security / Program Director: walk TSC mapping + gap inventory with auditor scoping.  
2. Program Director: copy templates `06`–`09` offline; execute + sign; keep PII out of git.  
3. DevOps: keep tip-line URLs current; Stage 6 stays quarantined.  
4. Do **not** paste this README into customer contracts as “SOC2 Type I complete.”
