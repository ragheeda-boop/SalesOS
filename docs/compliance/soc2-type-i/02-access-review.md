# 02 — Access review process evidence (STORY-14-05)

> **Intent:** Documented process + sample evidence for user/admin access reviews.  
> **Label:** Process **documented in this pack** · executed quarterly worksheets / attested reviews = **not validated** (Program Director / ops).  
> **Not:** Type I auditor opinion.

## Process (in-repo proposed control — Security-owned)

Cadence: **at least quarterly** (aligns with common SOC2 CC6.x expectations; exact period is auditor-scoped).

| Step | Owner | Evidence expected |
|------|-------|-------------------|
| 1. Export active users + roles/permissions per tenant (or platform admins) | Security / BE admin | Export artifact dated |
| 2. Manager / tenant-admin attestation of need-to-have | Tenant admin + Security | Signed/dated worksheet |
| 3. Revoke / adjust excess privileges | Identity admin | Ticket + audit log of revoke |
| 4. File packet under compliance evidence | Program Director | Stored with period label |

### Worksheet template (unsigned)

Canonical blank worksheet: [`06-access-review-worksheet-template.md`](./06-access-review-worksheet-template.md) — **LANDED**.  
Suggested fields: review period `YYYY-Qn`, system, reviewer, population source, findings count, remediation tickets, sign-off date.

**No filled / signed production worksheet is checked into this repo** (PII / privilege data). Template ≠ executed sample — signatures remain **Program Director residual**.

## Technical enablers (implementation evidence)

| Capability | Path / note | Evidence class |
|------------|-------------|----------------|
| RBAC / identity | `salesos/backend/app/modules/identity/` | Design |
| Admin audit query schemas | `salesos/backend/app/modules/admin/schemas.py` (`AuditLogQueryResponse`, …) | Design |
| Entitlement enforcement | `EntitlementEnforcementMiddleware` + entitlements module | Design |
| Suspended-tenant write guard | `SuspendedTenantWriteGuardMiddleware` | Design |
| CSRF / JWT / tenant context | BE support crumb §3.4 | Design |
| `feature_ai_copilot` default False | `app/config.py` | Reduces AI surface (scope) |

## Related policies

| Doc | Path |
|-----|------|
| Vulnerability disclosure | `salesos/docs/pentest/VULNERABILITY_DISCLOSURE_POLICY.md` |
| Incident response | `salesos/docs/INCIDENT_RESPONSE_PLAN.md` |
| Portal security architecture | `salesos/docs/portal/architecture/security.md` |
| Production readiness (access / logging rows) | `docs/program/PRODUCTION_READINESS_CHECKLIST.md` |

## What is **not** evidenced

| Item | Label |
|------|-------|
| Completed Qn access-review packet with signatures | **not validated** — Program Director |
| IdP / SSO joiner-mover-leaver runbooks with samples | **gap** if SSO not in GA scope |
| CODEOWNERS file for privileged path owners | **gap** (no `CODEOWNERS` found at tip) |
| Branch-protection screenshot as access control for engineers | **residual** — GitHub org settings (external to git tree) |

## Linkage to change management

Engineer access to production deploy paths is partially evidenced via CI/Deploy workflows and tip-line SUCCESS URLs in the DevOps pack — that is **change** evidence, not a substitute for **user access review** worksheets.
