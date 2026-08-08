# `@salesos/decision-platform-lab` (full twin — lab)

**Status:** Full implementation twin under `salesos/packages/`. **Not** wired as the frontend resolve path.

- Package name **renamed** (EAB-2026-08-06-003 structural): was `@salesos/decision-platform` — now `@salesos/decision-platform-lab` to end the name-collision residual with the FE STUB.
- FE app resolves `@salesos/decision-platform` → `salesos/frontend/packages/platform/decision` (**STUB**).
- Product clients: use Decision Center HTTP (`/api/v1/decisions*`), not this package as GA AI.

### Honesty / EAB

- [AI_HONESTY.md](../../../../docs/audit/ga-engineering-audit/AI_HONESTY.md)
- [DECISION-API-SOT.md](../../../../docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-001/DECISION-API-SOT.md)
- [REMEDIATION-STRUCTURAL.md](../../../../docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md)
