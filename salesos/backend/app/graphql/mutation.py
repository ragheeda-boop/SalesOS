from datetime import date

import strawberry
from strawberry.types import Info

from app.graphql.types import (
    CompanyType,
    CompanyUpdateInput,
    CreateOpportunityInput,
    EnrichmentResultType,
    OpportunityType,
)


async def _create_opportunity(
    info: Info,
    input: CreateOpportunityInput,
) -> OpportunityType:
    from app.database import async_session
    from domains.commercial.infrastructure.postgres_repositories import (
        PostgresOpportunityRepository,
    )
    from domains.commercial.opportunity.engine.service import OpportunityService

    tenant_id = info.context.get("tenant_id", "")
    async with async_session() as db:
        svc = OpportunityService(PostgresOpportunityRepository(db))
        expected_close = None
        if input.expected_close_date:
            expected_close = date.fromisoformat(input.expected_close_date)
        opp = await svc.create_opportunity(
            tenant_id=tenant_id,
            company_id=input.company_id,
            name=input.name,
            value=input.value,
            owner_id=input.owner_id,
            expected_close_date=expected_close,
            description=input.description,
        )
        return OpportunityType(
            id=opp.id,
            company_id=opp.company_id,
            name=opp.name,
            stage=opp.stage,
            value=opp.value,
            currency=getattr(opp, "currency", "SAR"),
            probability=opp.probability,
            health=getattr(opp, "health", "healthy"),
            expected_close_date=(
                opp.expected_close_date.isoformat()
                if opp.expected_close_date
                else None
            ),
            owner_id=opp.owner_id,
            status=(
                opp.status.value
                if hasattr(opp.status, "value")
                else str(opp.status)
            ),
            description=getattr(opp, "description", ""),
            created_at=(
                opp.created_at.isoformat()
                if hasattr(opp.created_at, "isoformat")
                else str(opp.created_at)
            ),
            updated_at=(
                opp.updated_at.isoformat()
                if hasattr(opp.updated_at, "isoformat")
                else str(opp.updated_at)
            ),
        )


async def _update_company(
    info: Info,
    company_id: str,
    input: CompanyUpdateInput,
) -> CompanyType | None:
    from app.database import async_session
    from app.modules.company.service import CompanyService

    async with async_session() as db:
        svc = CompanyService(db=db)
        updates = {}
        for field_name in (
            "name_ar",
            "name_en",
            "status",
            "city",
            "region",
            "phone",
            "email",
            "website",
            "address",
            "activity_description",
            "tags",
        ):
            val = getattr(input, field_name, None)
            if val is not None:
                updates[field_name] = val
        try:
            company = await svc.update_company(company_id, updates)
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
                float(company.confidence_score)
                if company.confidence_score is not None
                else None
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


async def _enrich_company(
    info: Info,
    company_id: str,
) -> EnrichmentResultType:
    from app.tasks import enrich_company_task

    tenant_id = info.context.get("tenant_id", "")
    task = enrich_company_task.delay(company_id, tenant_id)
    return EnrichmentResultType(
        task_id=task.id,
        status="pending",
        company_id=company_id,
    )


@strawberry.type
class Mutation:
    create_opportunity: OpportunityType = strawberry.field(
        resolver=_create_opportunity,
        description="Create a new sales opportunity",
    )
    update_company: CompanyType | None = strawberry.field(
        resolver=_update_company,
        description="Update company fields",
    )
    enrich_company: EnrichmentResultType = strawberry.field(
        resolver=_enrich_company,
        description="Trigger async company enrichment",
    )
