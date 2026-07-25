# ADR-0034: Repository Pattern Compliance

**Status**: Proposed
**Date**: 2026-07-17
**Author**: Architecture Review Board (Sprint 0)

---

## Context

The Engineering Constitution Article 3.3 (ARC-3.3) mandates:

> "Every Domain Service depends on Repository Interface. The Implementation is in Infrastructure Layer Only. Domain Layer doesn't know about the database."

This is a foundational pattern for testability, domain isolation, and infrastructure decoupling. All domain services must depend on repository interfaces (ABCs), with PostgreSQL implementations in the infrastructure layer and `InMemoryRepository` implementations for testing.

**Sprint 0 Architecture Reconciliation discovered:**

The Identity domain — documented as 100% compliant with zero debt — violates this pattern directly:

- `app/modules/identity/service.py` uses `db.execute(select(...))` and raw SQLAlchemy `AsyncSession` directly
- `UserRepository` and `TenantRepository` **exist** in `app/modules/identity/repositories.py` but are **not used** by the service
- The service handles DB queries, audit logging, event publishing, token creation, AND business logic — violating Single Responsibility Principle

This is significant because:
1. Identity is a **frozen interface** (requires ADR to modify)
2. Identity is documented as the 100% compliance benchmark
3. Other developers may use Identity as a reference implementation and replicate the violation
4. Testing requires mocking `AsyncSession` instead of using `InMemoryUserRepository`, making tests more brittle

---

## Decision

1. **Refactor Identity Service** to use `UserRepository` and `TenantRepository` interfaces within 1 sprint of approval (Sprint 2).

2. **No exceptions to Repository Pattern.** The mandate in ENGINEERING_CONSTITUTION Art. 3.3 is absolute. Any future service that bypasses repository interfaces on any domain must be rejected at PR review.

3. **Document the pattern** in the domain README or Architecture Book: "Identity domain was refactored in ADR-0034 to use repository interfaces. Future services in this domain must follow the same pattern."

4. **Add automated checking** — the compliance script (`scripts/arch-compliance.ps1`) should scan for direct `db.execute()` usage in service files and flag them.

---

## Migration Plan

### Step 1: Audit
- List all `db.execute()`, `session.execute()`, `select()` calls in `identity/service.py`
- Map each to the corresponding `UserRepository` or `TenantRepository` method

### Step 2: Refactor
- Inject `UserRepository` and `TenantRepository` into `IdentityService` constructor
- Replace raw queries with repository method calls
- Verify all 12 Identity endpoints still return identical responses

### Step 3: Test
- Replace `AsyncSession` mocks with `InMemoryUserRepository` in unit tests
- Verify all existing Identity tests pass without modification to test logic
- Add any missing tests for repository-level concerns

### Step 4: Verify
- Run full Identity test suite (current: 88% coverage)
- Run architecture compliance check
- Run security audit (Identity touches auth — regression risk is critical)

---

## Consequences

### Positive
- Identity domain genuinely achieves 100% compliance
- Removes the "false benchmark" problem (other domains learning from Identity's violation)
- More maintainable, testable Identity service
- Clean separation of concerns (business logic vs data access)

### Negative
- 1 day of engineering effort
- Auth regression risk — Identity is the most security-sensitive domain
- Existing tests using `AsyncSession` mocks must be updated

### Neutral
- Repository interfaces already exist — no new abstractions needed
- No API contract changes
- No database schema changes

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Auth regression (critical) | Full auth test suite before/after refactor; manual review of every changed line |
| Behavioral differences | Repository methods must be 1:1 with current queries; response comparison tests |
| Test gaps | Existing tests already cover service logic; only mock setup changes |

---

## Compliance

| Check | Enforcement | Sprint |
|-------|-------------|--------|
| `identity/service.py` no longer calls `db.execute()` directly | CI scan for `db.execute` in `app/modules/identity/` | S2 |
| `UserRepository` and `TenantRepository` injected | Type check in `IdentityService.__init__` | S2 |
| `InMemoryUserRepository` used in tests | Code review | S2 |
| All existing Identity tests pass | CI test run | S2 |

---

## References

- ENGINEERING_CONSTITUTION.md Art. 3.3: Repository Pattern
- TD-S0-04: Identity service bypasses own repositories
- SES_CHANGELOG.md Change 004: Repository Pattern — Identity Domain Exception
- MIGRATION_MATRIX.md §1: Backend Architecture Gaps
