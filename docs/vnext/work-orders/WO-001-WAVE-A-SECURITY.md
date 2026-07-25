# Work Order WO-001 — Wave A: Security Hardening

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Priority**: P0 — Critical

---

## Wave ID

WO-001 / WAVE-A

## Objective

Eliminate all P0 security vulnerabilities identified in the Sprint 0 verification and planning documents before any other work begins.

## Scope

Strictly limited to:

1. **SEC-001** — Webhooks router authentication (JWT)
2. **SEC-003** — GraphQL security review (verify auth enforcement)
3. **SEC-004** — JWKS endpoint: migrate from empty HS256 key to valid asymmetric RS256 keys
4. **SEC-016** — Neo4j Cypher queries: convert all f-string interpolations to parameterized queries
5. **SEC-005** — Grafana default password removal from `.env.example`
6. API key standardization assessment (document ADR if migration is not safe)

## Assigned Engineer

`backend-engineer`

## Assigned Reviewer

`security-reviewer`

## Expected Deliverables

| Deliverable | Description |
|-------------|-------------|
| Webhooks JWT auth | `Depends(verify_token)` added to webhooks router |
| GraphQL auth verified | Confirmation that Strawberry context auth is equivalent to FastAPI `Depends(verify_token)` |
| JWKS RS256 keys | Valid asymmetric key pair served at `/.well-known/jwks.json`; old empty entry removed |
| Neo4j parameterized queries | All f-string Cypher queries replaced with parameterized queries |
| Grafana default password | Default credentials removed from `.env.example` |
| API Key ADR (optional) | ADR documenting API key auth pattern if migration from JWT is proposed |
| SPRINT0_WAVE_A_REPORT.md | Final report documenting all changes, review findings, and remaining risks |

## Quality Gates

| Gate | Criteria |
|------|----------|
| G-A.1 | Webhooks endpoint returns 401 without valid JWT |
| G-A.2 | GraphQL endpoint returns 401 without valid JWT |
| G-A.3 | JWKS endpoint returns at least one valid RS256 key (non-empty) |
| G-A.4 | No f-string Neo4j queries remain (verified by grep) |
| G-A.5 | `.env.example` contains no default credentials |
| G-A.6 | Security reviewer approves all changes |

## Stop Condition

Wave A is complete when:

- All 6 deliverables are produced
- Security reviewer approves
- This work order is marked **Closed** by Engineering OS
- `SPRINT0_WAVE_A_REPORT.md` is filed in `docs/vnext/reports/`

## Constraints

- Do NOT modify the Agent Runtime (`runtime/agent_runtime/`)
- Do NOT refactor middleware chain (Wave B scope)
- Do NOT touch frontend code
- Do NOT modify pagination logic
- All changes must be backward-compatible unless explicitly documented

## Dependencies

None — Wave A is fully independent.

---

**Engineering OS Authorization**: ✅ Approved

*Next: Wave A execution begins immediately. Wave B (Backend Performance) will not start until WO-001 is closed.*
