# 05 — Controls mapping sketch (TSC → repo)

> **Classification:** Engineering sketch for auditor scoping — **not** a signed SOC2 control matrix.  
> **Not:** Type I certified · Not Production GO.

Common Trust Services Criteria themes mapped to **in-repo pointers**. Criterion IDs are illustrative (CC-family); final IDs belong to the auditor’s system.

| Theme (illustrative) | Intent | Primary evidence | Status |
|----------------------|--------|------------------|--------|
| CC1 / governance | Program honesty, GO/NO-GO | `docs/audit/ga-engineering-audit/`, `AGENTS.md` | Design docs |
| CC2 / communication | Incident + disclosure | `salesos/docs/INCIDENT_RESPONSE_PLAN.md`, `salesos/docs/pentest/VULNERABILITY_DISCLOSURE_POLICY.md` | Policies present; drill samples **not validated** |
| CC3 / risk | Security architecture audits | `docs/audit/11-security-architecture.md`, Wave 2 SEC progress | Historical findings — not all closed |
| CC5 / monitoring | Health, metrics, Sentry (as documented) | `/health`, runbooks, CI | Partial — SIEM gap |
| CC6 / logical access | Auth, CSRF, RBAC, RLS, access review | BE crumb §3.4; `02-access-review.md` | Design **light**; review worksheets **gap** |
| CC7 / change | CI/CD, tip-line, Health Gate | `03-change-management.md` + DevOps pack @ `4754b8b` | Pipeline **build validated**; CAB **gap** |
| CC8 / change (vuln) | Scans | `.github/workflows/security-scan.yml`, CI bandit/Trivy | Pipeline **build validated** @ tip |
| CC9 / risk mitigation | Rate limit, headers, entitlements | middleware stack | Design present |
| Availability (A) | Health Gate, chaos/DR harnesses | Deploy gate; STORY-14-02/14-03 crumbs | Harness landed; live kill **not claimed** |
| Confidentiality (C) | Tenant isolation, secrets scan | RLS GUC; gitleaks/Trivy | Design + scan; RLS completeness **auditor-scoped** |
| Privacy (P) / PDPL | Regional scope A5 | `MASTER_EXECUTION_PLAN.md` A5 | Saudi/GCC focus at GA — not full GDPR claim |

## AI scope control

| Control | Evidence | Note |
|---------|----------|------|
| Copilot off by default | `feature_ai_copilot: bool = False` in `salesos/backend/app/config.py` | Keeps AI marketing honesty; see `AI_HONESTY.md` |

## How auditors should treat this

1. Use as a **map to artifacts**, not as test results.  
2. Request PD-1…AUD-5 closures from `04-gap-inventory.md`.  
3. Type I opinion letter is **out of scope** for Phase 6 / this story.
