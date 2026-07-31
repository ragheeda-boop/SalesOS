"""Second real consumer of tests/support/tenant_isolation.py (STORY-01-04),
plus this is the file used to produce the Sprint 02 "Expected Demo":
show the harness catching a deliberately-reintroduced version of the
Sprint 01 Decision Center cross-tenant IDOR (GA-P0-SEC-01).

The demo itself is not automatable as a permanent test (a test that expects
a security bug to exist can't be left in the suite — it would have to
"pass" by finding the vulnerability, which means shipping the vulnerability
to keep the test green). It was performed manually, twice, against this
same test, unchanged, both reverts undone immediately after observing the
result:

  Attempt 1 (negative result, kept here because it's informative, not
  swept under the rug): reverted `get_decision`'s filter from
  `DecisionModel.tenant_id == tenant_id` back to the original
  `DecisionModel.decision_metadata["tenant_id"].as_string() == tenant_id`.
  This test still PASSED. For well-formed metadata (which this test, and
  the legitimate write path via `service.py`, always produce), the JSONB
  path and the dedicated column happen to isolate identically — so a bare
  code-level revert to the pre-Sprint-01 query shape does not, by itself,
  reproduce a leak. The real Sprint 01 exploit condition depended on
  metadata that the JSONB path could not reliably match on (the dedicated,
  indexed, NOT NULL column closes that regardless of metadata quality —
  which is the actual architectural reason the fix is correct, not merely
  that it "looks more correct").

  Attempt 2 (the demo that matters): removed the tenant_id predicate from
  the query entirely — `select(DecisionModel).where(DecisionModel.id == uid)`,
  simulating the general regression class (someone deletes/forgets the
  tenant check) the harness exists to catch, not one specific historical
  diff. This test FAILED, with `CrossTenantIsolationViolation` raised from
  the harness (not a bare AssertionError), naming both tenants, the key,
  and the full leaked record.

What's committed here is the permanent form: this test always runs against
the current (fixed) code and must always pass in CI.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domains.decision_center.models import (
    Decision,
    DecisionDomain,
    DecisionType,
)
from domains.decision_center.postgres_repo import PostgresDecisionCenterRepository
from tests.support.schema import ensure_tables_created
from tests.support.tenant_isolation import assert_cross_tenant_read_blocked

pytestmark = pytest.mark.asyncio


def _decision(tenant_id: str) -> Decision:
    return Decision(
        id=str(uuid.uuid4()),
        domain=DecisionDomain.PIPELINE,
        type=DecisionType.DEAL_SCORING,
        entity_id="harness-demo-co",
        entity_type="company",
        decision="pursue",
        confidence=0.9,
        reasoning="tenant isolation harness demo",
        provider="rule_engine",
        timestamp=datetime.now(UTC),
        metadata={"tenant_id": tenant_id},
    )


class TestDecisionCenterHarnessDemo:
    async def test_cross_tenant_decision_read_blocked_via_harness(self, db_session: AsyncSession):
        await ensure_tables_created(db_session)
        repo = PostgresDecisionCenterRepository(db_session)

        async def create_as(tenant_id: str) -> str:
            saved = await repo.save_decision(_decision(tenant_id))
            return saved.id

        await assert_cross_tenant_read_blocked(
            create_as=create_as,
            read_as=repo.get_decision,
        )
