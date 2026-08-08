# ADR-107: Data Residency — Use Existing Tenant.region Field

**Status**: ACCEPTED
**Date**: 2026-08-07
**Author**: STAR Audit / Architecture
**Related**: W-03, ADR-101, ADR-102
**Supersedes**: nothing

---

## Context

CANONICAL_ARCHITECTURE.md documents data residency as a requirement: "Tenant.region field" for Saudi data sovereignty. The STAR audit (W-03) found the **field exists but is unused** — `Tenant.region` is defined in the model but never read or enforced.

Current state:
- `Tenant.region` field exists in SQLAlchemy model
- No enforcement logic
- No data routing based on region
- No compliance documentation

## Decision

**Use the existing Tenant.region field.** Implement basic enforcement in v1.0.

### Rationale
1. **Field already exists** — No migration needed; just add enforcement logic
2. **Saudi market requirement** — Data residency is a regulatory expectation for Saudi B2B SaaS
3. **Low effort** — Basic enforcement (validate region, log region, route to regional DB) is a small feature
4. **Foundation** — Establishes the pattern for future multi-region expansion

### What stays in v1.0
- `Tenant.region` field (already exists)
- Region validation on tenant creation
- Region logging in audit trail
- Documentation of data residency policy

### What moves to v2.0
- Multi-region DB routing
- Cross-region data transfer controls
- Compliance reporting
- GDPR-style data subject requests

## Consequences

- **Positive:** Saudi regulatory requirement met; foundation for multi-region
- **Negative:** Adds small feature to v1.0 scope
- **Risk:** If regulation changes, enforcement logic may need updating

## Evidence

- W-03: STAR Audit found field exists but unused
- `salesos/backend/app/domains/identity/models.py` — `Tenant.region` field
- No enforcement logic in `salesos/backend/app/`
