"""Phase 1 Product Core — smoke tests for gate exit criteria.

Covers:
  P1-1 Domain Model (Company owner_id/segment, UBOM deprecation)
  P1-2 CRM (ownership assignment)
  P1-3 Deals (opportunity owner_id wiring)
  P1-4 Pipeline (qualification criteria with full context)
  P1-5 Activities (FK links)
  P1-6 Revenue (no demo fallback)
  P1-7 Proposals (complete API surface)
  P1-8 Reviews (domain model + service)
  P1-9 Approvals (RBAC enforcement + audit trail)

Validation label: build validated (unit tests, no DB required).
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


# ── P1-1: Domain Model ──


class TestP1DomainModel:
    def test_company_model_has_owner_id(self):
        from app.modules.company.models import Company
        cols = {c.name for c in Company.__table__.columns}
        assert "owner_id" in cols, "Company model must have owner_id column"

    def test_company_model_has_segment(self):
        from app.modules.company.models import Company
        cols = {c.name for c in Company.__table__.columns}
        assert "segment" in cols, "Company model must have segment column"

    def test_company_tenant_segment_index_exists(self):
        from app.modules.company.models import Company
        index_names = {idx.name for idx in Company.__table__.indexes}
        assert "ix_companies_tenant_segment" in index_names

    def test_ubom_is_deprecated(self):
        import domains.ubom as ubom
        docstring = ubom.__doc__ or ""
        assert "DEPRECATED" in docstring, "UBOM module must be marked DEPRECATED"


# ── P1-2: CRM Ownership ──


class TestP1CRMOwnership:
    def test_company_assignment_endpoint_exists(self):
        from app.modules.company.router import router
        routes = [(r.methods, r.path) for r in router.routes]
        assign_routes = [
            (m, p) for m, p in routes if "/{company_id}/assign" in p
        ]
        assert len(assign_routes) > 0, "Company assignment endpoint must exist"


# ── P1-3: Deals owner_id wiring ──


class TestP1DealsOwnership:
    def test_create_opportunity_accepts_owner_id(self):
        import inspect
        from app.routers.commercial import create_opportunity
        sig = inspect.signature(create_opportunity)
        assert "owner_id" in sig.parameters, "create_opportunity must accept owner_id"

    def test_opportunity_assign_endpoint_exists(self):
        from app.routers.commercial import router
        routes = [(r.methods, r.path) for r in router.routes]
        assign_routes = [
            (m, p) for m, p in routes if "/opportunities/{opportunity_id}/assign" in p
        ]
        assert len(assign_routes) > 0, "Opportunity assign endpoint must exist"


# ── P1-4: Pipeline qualification criteria ──


class TestP1PipelineQualification:
    def test_enter_stage_accepts_opportunity_context(self):
        import inspect
        from domains.commercial.pipeline.engine.service import PipelineService
        sig = inspect.signature(PipelineService.enter_stage)
        assert "opportunity_context" in sig.parameters, \
            "enter_stage must accept opportunity_context parameter"

    def test_check_criteria_with_full_context(self):
        from domains.commercial.pipeline.engine.service import PipelineService
        from domains.commercial.pipeline.contracts.models import Criterion
        criteria = [Criterion(field="value", operator="gte", value=1000)]
        # With sufficient value — should pass
        violation = PipelineService._check_criteria(
            criteria, {"stage": "proposal", "value": 5000}
        )
        assert violation is None, "Criteria should pass with value=5000"

    def test_check_criteria_fails_with_insufficient_value(self):
        from domains.commercial.pipeline.engine.service import PipelineService
        from domains.commercial.pipeline.contracts.models import Criterion
        criteria = [Criterion(field="value", operator="gte", value=1000,
                              label="Value >= 1000")]
        # With insufficient value — should fail
        violation = PipelineService._check_criteria(
            criteria, {"stage": "proposal", "value": 500}
        )
        assert violation is not None, "Criteria should fail with value=500"

    def test_check_criteria_fails_with_empty_context(self):
        """P1-4 fix: before the fix, only {"stage": to_stage} was passed,
        so value criteria always failed (None < 1000). Now full context is passed."""
        from domains.commercial.pipeline.engine.service import PipelineService
        from domains.commercial.pipeline.contracts.models import Criterion
        criteria = [Criterion(field="contact_id", operator="exists",
                              label="Contact identified")]
        # With no contact_id — should fail
        violation = PipelineService._check_criteria(
            criteria, {"stage": "qualification"}
        )
        assert violation is not None, "Exists criteria should fail when field absent"

    def test_check_criteria_passes_with_contact(self):
        from domains.commercial.pipeline.engine.service import PipelineService
        from domains.commercial.pipeline.contracts.models import Criterion
        criteria = [Criterion(field="contact_id", operator="exists")]
        violation = PipelineService._check_criteria(
            criteria, {"stage": "qualification", "contact_id": "contact-123"}
        )
        assert violation is None, "Exists criteria should pass when field present"


# ── P1-5: Activities FK links ──


class TestP1ActivitiesFK:
    def test_activity_session_model_has_company_id(self):
        from domains.commercial.infrastructure.models import ActivitySessionModel
        cols = {c.name for c in ActivitySessionModel.__table__.columns}
        assert "company_id" in cols, "ActivitySession must have company_id"

    def test_activity_session_model_has_contact_id(self):
        from domains.commercial.infrastructure.models import ActivitySessionModel
        cols = {c.name for c in ActivitySessionModel.__table__.columns}
        assert "contact_id" in cols, "ActivitySession must have contact_id"

    def test_activity_session_model_has_deal_id(self):
        from domains.commercial.infrastructure.models import ActivitySessionModel
        cols = {c.name for c in ActivitySessionModel.__table__.columns}
        assert "deal_id" in cols, "ActivitySession must have deal_id"


# ── P1-6: Revenue no demo fallback ──


class TestP1RevenueNoDemoFallback:
    def test_revenue_brain_has_no_hardcoded_base(self):
        import inspect
        from intelligence.revenue_brain import RevenueBrain
        source = inspect.getsource(RevenueBrain._generate_forecasts)
        assert "1000000.0" not in source, \
            "RevenueBrain must not have hardcoded $1M demo fallback"
        assert "base_revenue = 0.0" in source, \
            "RevenueBrain should initialize base_revenue to 0.0"


# ── P1-7: Proposals complete API ──


class TestP1ProposalsAPI:
    def _get_commercial_routes(self):
        from app.routers.commercial import router
        return {r.path for r in router.routes}

    def test_proposal_list_endpoint_exists(self):
        routes = self._get_commercial_routes()
        assert "/proposals" in routes, "GET /proposals (list) must exist"

    def test_proposal_detail_endpoint_exists(self):
        routes = self._get_commercial_routes()
        assert "/proposals/{proposal_id}" in routes, "GET /proposals/{id} must exist"

    def test_proposal_approve_endpoint_exists(self):
        routes = self._get_commercial_routes()
        assert "/proposals/{proposal_id}/approve" in routes, \
            "POST /proposals/{id}/approve must exist (was auto-approve before)"

    def test_proposal_reject_endpoint_exists(self):
        routes = self._get_commercial_routes()
        assert "/proposals/{proposal_id}/reject" in routes, \
            "POST /proposals/{id}/reject must exist"

    def test_proposal_expire_endpoint_exists(self):
        routes = self._get_commercial_routes()
        assert "/proposals/{proposal_id}/expire" in routes, \
            "POST /proposals/{id}/expire must exist"

    def test_proposal_deliver_does_not_auto_approve(self):
        """P1-7 fix: deliver_proposal must NOT call svc.approve(proposal_id, 'auto')"""
        import inspect
        from app.routers.commercial import deliver_proposal
        source = inspect.getsource(deliver_proposal)
        assert 'approve(proposal_id, "auto")' not in source, \
            "deliver_proposal must not auto-approve with 'auto'"
        assert 'svc.approve' not in source, \
            "deliver_proposal must not call approve at all"

    def test_proposal_accept_does_not_auto_approve(self):
        """P1-7 fix: accept_proposal must NOT chain auto-approve+deliver+view+accept"""
        import inspect
        from app.routers.commercial import accept_proposal
        source = inspect.getsource(accept_proposal)
        assert 'approve(proposal_id, "auto")' not in source, \
            "accept_proposal must not auto-approve"


# ── P1-8: Reviews domain ──


class TestP1ReviewsDomain:
    def test_review_model_exists(self):
        from domains.commercial.review.contracts.models import Review, ReviewStatus, ReviewType
        assert Review is not None
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewType.DEAL_REVIEW.value == "deal_review"

    def test_review_service_create(self):
        from domains.commercial.review.engine.service import ReviewService
        from domains.commercial.review.engine.in_memory_repo import InMemoryReviewRepository
        from domains.commercial.review.contracts.models import ReviewType

        svc = ReviewService(InMemoryReviewRepository())
        # Run async test
        import asyncio
        review = asyncio.get_event_loop().run_until_complete(
            svc.create_review("tenant-1", ReviewType.DEAL_REVIEW, "opp-1", "opportunity")
        )
        assert review.id is not None
        assert review.status.value == "pending"
        assert review.target_id == "opp-1"

    def test_review_service_decide(self):
        from domains.commercial.review.engine.service import ReviewService
        from domains.commercial.review.engine.in_memory_repo import InMemoryReviewRepository
        from domains.commercial.review.contracts.models import ReviewType, ReviewStatus

        svc = ReviewService(InMemoryReviewRepository())
        import asyncio

        async def run():
            review = await svc.create_review("t1", ReviewType.DEAL_REVIEW, "o1", "opportunity")
            decided = await svc.decide(review.id, "user-1", "approve", "looks good")
            return decided
        result = asyncio.get_event_loop().run_until_complete(run())
        assert result.status == ReviewStatus.APPROVED
        assert result.decision_count == 1

    def test_review_api_endpoints_exist(self):
        from app.routers.commercial import router
        routes = {r.path for r in router.routes}
        assert "/reviews" in routes, "POST/GET /reviews must exist"
        assert "/reviews/{review_id}" in routes, "GET /reviews/{id} must exist"
        assert "/reviews/{review_id}/assign" in routes, "POST /reviews/{id}/assign must exist"
        assert "/reviews/{review_id}/decide" in routes, "POST /reviews/{id}/decide must exist"

    def test_review_orm_model_exists(self):
        from domains.commercial.infrastructure.models import ReviewModel
        assert ReviewModel.__tablename__ == "commercial_reviews"

    def test_review_postgres_repo_exists(self):
        from domains.commercial.infrastructure.postgres_repositories import PostgresReviewRepository
        assert PostgresReviewRepository is not None


# ── P1-9: Approvals RBAC + audit ──


class TestP1Approvals:
    def test_quote_reject_endpoint_exists(self):
        from app.routers.commercial import router
        routes = {r.path for r in router.routes}
        assert "/quotes/{quote_id}/reject" in routes, \
            "POST /quotes/{id}/reject must exist"

    def test_quote_revise_endpoint_exists(self):
        from app.routers.commercial import router
        routes = {r.path for r in router.routes}
        assert "/quotes/{quote_id}/revise" in routes, \
            "POST /quotes/{id}/revise must exist"

    def test_quote_list_endpoint_exists(self):
        from app.routers.commercial import router
        routes = {r.path for r in router.routes}
        assert "/quotes" in routes, "GET /quotes must exist"

    def test_quote_detail_endpoint_exists(self):
        from app.routers.commercial import router
        routes = {r.path for r in router.routes}
        assert "/quotes/{quote_id}" in routes, "GET /quotes/{id} must exist"

    def test_quote_approve_has_approval_level_param(self):
        import inspect
        from app.routers.commercial import approve_quote
        sig = inspect.signature(approve_quote)
        assert "approval_level" in sig.parameters, \
            "approve_quote must accept approval_level parameter (RBAC enforcement)"

    def test_quote_approve_requires_approved_by(self):
        """P1-9: approved_by must be required (no default 'manager')."""
        import inspect
        from app.routers.commercial import approve_quote
        sig = inspect.signature(approve_quote)
        approved_by_param = sig.parameters.get("approved_by")
        assert approved_by_param is not None
        # Query(...) makes it required — the default will be a Query object, not a str
        default = approved_by_param.default
        default_str = str(default)
        assert default != "manager", \
            "approved_by must not default to 'manager'"
        assert "required=True" in default_str or "Query" in default_str or default is inspect.Parameter.empty, \
            "approved_by must be required via Query(...)"

    def test_quote_service_has_audit_trail(self):
        """P1-9: QuoteService must have _record_approval_audit method."""
        from domains.commercial.quote.engine.service import QuoteService
        assert hasattr(QuoteService, "_record_approval_audit"), \
            "QuoteService must have _record_approval_audit method"


# ── Alembic migrations exist ──


class TestP1Migrations:
    def test_domain_migration_exists(self):
        import os
        from app.alembic.versions import a1b2c3d4e5f6_phase1_product_core_domain as m
        assert m.revision == "a1b2c3d4e5f6"

    def test_reviews_migration_exists(self):
        from app.alembic.versions import b2c3d4e5f6a7_phase1_reviews_domain as m
        assert m.revision == "b2c3d4e5f6a7"

    def test_activities_fk_migration_exists(self):
        from app.alembic.versions import c3d4e5f6a7b8_phase1_activities_fk_links as m
        assert m.revision == "c3d4e5f6a7b8"


# ── P1-6a: Revenue domain router mounted + forecast Postgres ──


class TestP1RevenueRouter:
    def test_revenue_planning_router_mounted(self):
        """P1-6a: revenue planning router must be mounted in boot/routers.py."""
        import app.boot.routers as boot
        import inspect
        source = inspect.getsource(boot.register_routers)
        assert "revenue_planning_router" in source, \
            "boot/routers.py must mount revenue_planning_router"
        assert "/api/v1/revenue-planning" in source, \
            "revenue planning router must be mounted at /api/v1/revenue-planning"

    def test_revenue_router_uses_di_for_forecast(self):
        """P1-6a: forecast service must use DI (not module-level singleton)."""
        from domains.revenue.router import _forecast_svc
        assert callable(_forecast_svc), \
            "_forecast_svc must be a function (DI factory)"


# ── P1-6b: Analytics cubes wired to real queries ──


class TestP1AnalyticsCubes:
    def test_pipeline_cube_not_stub(self):
        """P1-6b: PipelineCube.query must not be a stub returning []."""
        import inspect
        from domains.analytics.cubes import PipelineCube
        source = inspect.getsource(PipelineCube.query)
        assert "return []" not in source or "rows" in source, \
            "PipelineCube.query must not be a stub returning []"

    def test_team_cube_not_stub(self):
        """P1-6b: TeamCube.query must not be a stub returning []."""
        import inspect
        from domains.analytics.cubes import TeamCube
        source = inspect.getsource(TeamCube.query)
        assert "return []" not in source or "rows" in source, \
            "TeamCube.query must not be a stub returning []"

    def test_activity_cube_not_stub(self):
        """P1-6b: ActivityCube.query must not be a stub returning []."""
        import inspect
        from domains.analytics.cubes import ActivityCube
        source = inspect.getsource(ActivityCube.query)
        assert "return []" not in source or "rows" in source, \
            "ActivityCube.query must not be a stub returning []"


# ── P1-7a/P1-8a: Frontend pages exist ──

_FE_BASE = None


def _fe_base():
    """Find the frontend root (salesos/frontend)."""
    global _FE_BASE
    if _FE_BASE:
        return _FE_BASE
    import os
    # From salesos/backend/tests/unit/ → go up to salesos/frontend
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "..", "..", "frontend"),
        os.path.join(here, "..", "..", "..", "..", "salesos", "frontend"),
    ]
    for c in candidates:
        p = os.path.abspath(c)
        if os.path.isdir(p):
            _FE_BASE = p
            return p
    return None


class TestP1FrontendPages:
    def test_proposals_list_page_exists(self):
        import os
        fe = _fe_base()
        assert fe, "frontend root not found"
        path = os.path.join(fe, "src", "app", "v3", "proposals", "page.tsx")
        assert os.path.exists(path), f"FE proposals list page must exist at {path}"

    def test_proposals_detail_page_exists(self):
        import os
        fe = _fe_base()
        assert fe, "frontend root not found"
        path = os.path.join(fe, "src", "app", "v3", "proposals", "[id]", "page.tsx")
        assert os.path.exists(path), f"FE proposals detail page must exist at {path}"

    def test_reviews_list_page_exists(self):
        import os
        fe = _fe_base()
        assert fe, "frontend root not found"
        path = os.path.join(fe, "src", "app", "v3", "reviews", "page.tsx")
        assert os.path.exists(path), f"FE reviews list page must exist at {path}"

    def test_reviews_detail_page_exists(self):
        import os
        fe = _fe_base()
        assert fe, "frontend root not found"
        path = os.path.join(fe, "src", "app", "v3", "reviews", "[id]", "page.tsx")
        assert os.path.exists(path), f"FE reviews detail page must exist at {path}"

    def test_proposals_nav_item_exists(self):
        import os
        fe = _fe_base()
        assert fe, "frontend root not found"
        path = os.path.join(fe, "src", "components", "v3", "nav.ts")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "/v3/proposals" in content, "Proposals nav item must exist"
        assert "/v3/reviews" in content, "Reviews nav item must exist"
