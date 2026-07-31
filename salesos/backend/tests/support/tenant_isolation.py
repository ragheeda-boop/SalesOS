"""Reusable cross-tenant isolation assertions.

STORY-01-04 (Sprint 02, Phase 0): "cross-tenant regression template ... every
future epic reuses." Extracted from the pattern every domain currently
hand-writes for itself (see e.g.
domains/decision_center/tests/test_postgres_repo.py::test_get_decision_cross_tenant_blocked,
written in Sprint 01/02 to close GA-P0-SEC-01, the Decision Center IDOR) —
this module is that pattern, generalized once, so the next domain doesn't
re-derive it.

Not a pytest fixture: these are plain async functions you call from inside a
test, because the "thing to isolate" differs per domain (a repository
method, a service method, an HTTP call through a router) and there's no
single fixture shape that covers all of them without hiding what's actually
being asserted. See TEST_STRATEGY.md §11 "Tenant Isolation Testing" for the
policy this module implements.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Sequence

TENANT_A_DEFAULT = "tenant-a"
TENANT_B_DEFAULT = "tenant-b"


class CrossTenantIsolationViolation(AssertionError):
    """Raised instead of a bare AssertionError so a CI failure here is
    immediately legible as a security regression, not an ordinary test
    failure, without needing to open the test file."""


async def assert_cross_tenant_read_blocked(
    *,
    create_as: Callable[[str], Awaitable[Any]],
    read_as: Callable[[Any, str], Awaitable[Any]],
    tenant_a: str = TENANT_A_DEFAULT,
    tenant_b: str = TENANT_B_DEFAULT,
) -> None:
    """Create a record as `tenant_a`, then assert `tenant_b` cannot read it.

    `create_as(tenant_id)` must create exactly one record scoped to
    `tenant_id` and return whatever key `read_as` needs (typically an id).
    `read_as(key, tenant_id)` must return a falsy value (None, [], 0, "")
    when the record isn't visible to `tenant_id` — this is already every
    `get_x(id, tenant_id) -> X | None` method's own convention in this
    codebase, so wiring an existing repository method straight in is
    normally a one-liner:

        await assert_cross_tenant_read_blocked(
            create_as=lambda t: repo.save_decision(_decision(t)).then(lambda d: d.id),
            read_as=repo.get_decision,
        )

    or, more plainly, with small local wrapper coroutines when the create
    call's return value isn't directly the key `read_as` needs:

        async def create(tenant_id):
            dec = await repo.save_decision(_decision(tenant_id))
            return dec.id

        await assert_cross_tenant_read_blocked(create_as=create, read_as=repo.get_decision)

    Raises CrossTenantIsolationViolation (not a bare AssertionError) if
    tenant_b can read tenant_a's record, or if tenant_a itself cannot read
    its own record back — the latter guards against a helper that "passes"
    only because it hides everything from everyone, which is isolation
    failing in the wrong direction, not a fix.
    """
    key = await create_as(tenant_a)

    leaked = await read_as(key, tenant_b)
    if leaked:
        raise CrossTenantIsolationViolation(
            f"cross-tenant isolation violated: a record created for tenant {tenant_a!r} "
            f"(key={key!r}) was readable by tenant {tenant_b!r} (returned: {leaked!r}). "
            f"This is the same bug class as GA-P0-SEC-01 (Decision Center cross-tenant "
            f"IDOR, Sprint 01) — see docs/program/RISK_REGISTER.md R-01."
        )

    own = await read_as(key, tenant_a)
    if not own:
        raise CrossTenantIsolationViolation(
            f"tenant {tenant_a!r} could not read back its own record (key={key!r}) after "
            f"creating it. Either create_as/read_as are mismatched, or isolation is "
            f"failing open in the *other* direction (hiding everything, not just other "
            f"tenants) — that is not a passing result, it is a different bug."
        )


async def assert_cross_tenant_listing_excludes(
    *,
    create_as: Callable[[str], Awaitable[Any]],
    list_as: Callable[[str], Awaitable[Sequence[Any]]],
    identify: Callable[[Any], Any] = lambda created: created,
    tenant_a: str = TENANT_A_DEFAULT,
    tenant_b: str = TENANT_B_DEFAULT,
) -> None:
    """Create a record as `tenant_a`, then assert it never appears in
    `tenant_b`'s listing — and does appear in `tenant_a`'s own listing.

    `list_as(tenant_id)` must return a sequence of records (or of whatever
    `identify()` is given — pass `identify=lambda d: d.id` if `create_as`
    returns an id but `list_as` returns full records). Two-sided by design,
    same rationale as `assert_cross_tenant_read_blocked`.
    """
    created = await create_as(tenant_a)
    marker = identify(created)

    b_items = [identify(item) for item in await list_as(tenant_b)]
    if marker in b_items:
        raise CrossTenantIsolationViolation(
            f"cross-tenant isolation violated: tenant {tenant_b!r}'s listing included a "
            f"record created for tenant {tenant_a!r} (marker={marker!r})."
        )

    a_items = [identify(item) for item in await list_as(tenant_a)]
    if marker not in a_items:
        raise CrossTenantIsolationViolation(
            f"tenant {tenant_a!r}'s own listing did not include the record it just "
            f"created (marker={marker!r}) — isolation is failing open in the other "
            f"direction, not a passing result."
        )
