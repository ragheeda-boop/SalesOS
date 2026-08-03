# 06 — Quarterly access-review worksheet (TEMPLATE — UNSIGNED)

> **Status:** Template **LANDED** in-repo · filled / signed worksheets = **Program Director residual** (do not commit PII).  
> **Story:** STORY-14-05 · links [`02-access-review.md`](./02-access-review.md) · gap PD-1.  
> **Honesty:** Not SOC2 Type I certified · Not Production GO · Not an executed review.

## How to use

1. Copy this file **offline** (or to the auditor evidence folder) for period `YYYY-Qn`.  
2. Fill population + findings; obtain manager / Security / Program Director signatures.  
3. Store completed packet **outside** this git tree (privilege + PII).  
4. Update crumb / gap inventory only with period label + storage location — never paste user lists here.

## Header

| Field | Value |
|-------|-------|
| Review period | YYYY-Qn (e.g. 2026-Q3) |
| Window start (UTC) | YYYY-MM-DD |
| Window end (UTC) | YYYY-MM-DD |
| System / scope | SalesOS / AQLIYA identity (platform admins + in-scope tenants) |
| Population source | ☐ Admin API · ☐ DB export · ☐ IdP · ☐ Other: ________ |
| Export artifact ID / path | _(offline)_ |
| Reviewer (name / role) | |
| Facilitator (Security) | |
| Program Director | |

## Population summary (aggregate only in-repo copies)

| Metric | Count |
|--------|------:|
| Users / principals in scope | |
| Privileged / admin roles | |
| Service accounts / automation | |
| Suspended / disabled retained | |

## Line items (complete offline)

| # | Principal (redact in git) | Role / entitlement | Still required? (Y/N) | Action (keep / reduce / revoke) | Ticket | Done (Y/N) |
|---|---------------------------|--------------------|------------------------|----------------------------------|--------|------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

_Add rows as needed. Do not commit filled rows to this repository._

## Findings & remediation

| Field | Value |
|-------|-------|
| Findings count | |
| Excess privilege count | |
| Revokes / adjustments completed | |
| Open remediation tickets | |
| Residual risk accepted (Y/N + note) | |

## Attestation (signatures — residual until executed)

| Role | Name | Signature | Date (ISO) |
|------|------|-----------|------------|
| Reviewer / manager | | ☐ UNSIGNED | |
| Security | | ☐ UNSIGNED | |
| Program Director | | ☐ UNSIGNED | |
| Tenant admin (if scoped) | | ☐ UNSIGNED / N/A | |

## Explicit non-claims

- This template alone does **not** satisfy a Type I access-review test.  
- Blank signature rows mean the control sample is **not validated**.  
- Do **not** claim “SOC2 Type I certified” after filing an unsigned copy.
