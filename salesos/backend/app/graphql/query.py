import strawberry
from strawberry.types import Info

from app.graphql.types import (
    CompanyType,
    OpportunityFiltersInput,
    OpportunityType,
    PipelineSummaryType,
    SearchResultItemType,
    SearchResultType,
)


async def _get_company(info: Info, company_id: str) -> CompanyType | None:
    from app.database import async_session
    from app.modules.company.service import CompanyService

    async with async_session() as db:
        svc = CompanyService(db=db)
        try:
            company = await svc.get_company(company_id)
        except Exception:
            return None
        return CompanyType(
            id=str(company.id),
            name_ar=company.name_ar,
            name_en=company.name_en,
            cr_number=company.cr_number,
            status=company.status,
            city=company.city,
            region=company.region,
            phone=company.phone,
            email=company.email,
            website=company.website,
            address=company.address,
            activity_description=company.activity_description,
            activity_code=company.activity_code,
            industry=company.industry,
            legal_form=company.legal_form,
            employees_count=company.employees_count,
            confidence_score=(
                float(company.confidence_score) if company.confidence_score is not None else None
            ),
            is_golden_record=company.is_golden_record,
            tags=company.tags,
            created_at=(
                company.created_at.isoformat()
                if hasattr(company.created_at, "isoformat")
                else str(company.created_at)
            ),
            updated_at=(
                company.updated_at.isoformat()
                if hasattr(company.updated_at, "isoformat")
                else str(company.updated_at)
            ),
        )


async def _search_companies(info: Info, query: str, limit: int = 20) -> SearchResultType:
    from app.database import async_session
    from app.modules.company.search_repository import CompanySearchRepository
    from domains.search.contracts.models import SearchQuery
    from domains.search.engine.planner import SearchPlanner
    from domains.search.ranking.pipeline import RankingPipeline

    async with async_session() as db:
        repo = CompanySearchRepository(db)
        ranking = RankingPipeline.default(
            exact_fields=["name_ar", "name_en", "cr_number"],
            partial_fields=[
                "name_ar",
                "name_en",
                "cr_number",
                "city",
                "activity_description",
            ],
        )
        planner = SearchPlanner(repository=repo, ranking_pipeline=ranking)
        search_query = SearchQuery(query=query, page_size=limit)
        result = await planner.search(search_query)

        items = [
            SearchResultItemType(
                id=str(item.id),
                name_ar=item.name_ar,
                name_en=item.name_en,
                cr_number=item.cr_number,
                city=item.city,
                confidence_score=(
                    float(item.confidence_score)
                    if getattr(item, "confidence_score", None) is not None
                    else None
                ),
            )
            for item in result.items
        ]
        return SearchResultType(
            query=query,
            total=result.total,
            duration_ms=result.duration_ms,
            items=items,
        )


async def _opportunities(
    info: Info,
    filters: OpportunityFiltersInput | None = None,
) -> list[OpportunityType]:
    from app.database import async_session
    from domains.commercial.infrastructure.postgres_repositories import (
        PostgresOpportunityRepository,
    )
    from domains.commercial.opportunity.contracts.models import OpportunityStatus
    from domains.commercial.opportunity.contracts.repository import OpportunityQuery
    from domains.commercial.opportunity.engine.service import OpportunityService

    tenant_id = info.context.get("tenant_id", "")
    async with async_session() as db:
        svc = OpportunityService(PostgresOpportunityRepository(db))
        page = 1
        if filters and filters.offset and filters.limit:
            page = (filters.offset // filters.limit) + 1
        q = OpportunityQuery(
            tenant_id=tenant_id,
            stage=filters.stage if filters else None,
            company_id=filters.company_id if filters else None,
            owner_id=filters.owner_id if filters else None,
            page=page,
            page_size=filters.limit if filters else 20,
        )
        if filters and filters.status:
            q.status = OpportunityStatus(filters.status)
        if filters and filters.min_value is not None:
            q.min_value = filters.min_value
        if filters and filters.max_value is not None:
            q.max_value = filters.max_value
        result = await svc.query(q)
        return [
            OpportunityType(
                id=o.id,
                company_id=o.company_id,
                name=o.name,
                stage=o.stage,
                value=o.value,
                currency=o.currency,
                probability=o.probability,
                health=getattr(o, "health", "healthy"),
                expected_close_date=(
                    o.expected_close_date.isoformat() if o.expected_close_date else None
                ),
                owner_id=o.owner_id,
                status=(o.status.value if hasattr(o.status, "value") else str(o.status)),
                description=o.description,
                created_at=(
                    o.created_at.isoformat()
                    if hasattr(o.created_at, "isoformat")
                    else str(o.created_at)
                ),
                updated_at=(
                    o.updated_at.isoformat()
                    if hasattr(o.updated_at, "isoformat")
                    else str(o.updated_at)
                ),
            )
            for o in result.items
        ]


async def _pipeline(info: Info) -> PipelineSummaryType | None:
    from app.database import async_session
    from domains.commercial.infrastructure.postgres_repositories import (
        PostgresPipelineRepository,
    )
    from domains.commercial.pipeline.engine.service import PipelineService

    tenant_id = info.context.get("tenant_id", "")
    async with async_session() as db:
        svc = PipelineService(PostgresPipelineRepository(db))
        try:
            pipes = await svc.list_pipelines(tenant_id)
            if not pipes:
                return PipelineSummaryType(
                    pipeline_value=0.0,
                    weighted_pipeline=0.0,
                    win_rate=0.0,
                )
            pipeline_id = pipes[0].id
            from domains.commercial.infrastructure.postgres_repositories import (
                PostgresOpportunityRepository,
            )
            from domains.commercial.opportunity.contracts.repository import OpportunityQuery
            from domains.commercial.opportunity.engine.service import OpportunityService

            opp_svc = OpportunityService(PostgresOpportunityRepository(db))
            opps = await opp_svc.query(OpportunityQuery(tenant_id=tenant_id))
            kpis = await svc.compute_kpis(pipeline_id, opps.items)
            return PipelineSummaryType(
                pipeline_value=kpis.pipeline_value,
                weighted_pipeline=kpis.weighted_pipeline,
                win_rate=kpis.win_rate,
            )
        except Exception:
            return None


@strawberry.type
class Query:
    company: CompanyType | None = strawberry.field(
        resolver=_get_company,
        description="Get a company by ID",
    )
    search: SearchResultType = strawberry.field(
        resolver=_search_companies,
        description="Search companies by query string",
    )
    opportunities: list[OpportunityType] = strawberry.field(
        resolver=_opportunities,
        description="List opportunities with optional filters",
    )
    pipeline: PipelineSummaryType | None = strawberry.field(
        resolver=_pipeline,
        description="Get pipeline KPIs summary",
    )
