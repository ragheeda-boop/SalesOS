"""Experimental semantic search endpoints — NOT connected to default UI.

These endpoints demonstrate pgvector capability for evaluation purposes.
To be connected to SearchPlanner only after validation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session
from app.modules.company.pgvector_repository import PgVectorCompanyRepository
from domains.search.contracts.models import SearchQuery
from domains.search.engine.planner import SearchPlanner
from domains.search.engine.strategy_matrix import detect_intent

router = APIRouter()


def get_semantic_planner(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    repo = PgVectorCompanyRepository(db=db)
    planner = SearchPlanner(repository=repo)
    return planner


def get_pgvector_repo(
    db: AsyncSession = Depends(get_db_session),
):
    return PgVectorCompanyRepository(db=db)


@router.get("/search/semantic")
async def semantic_search(
    q: str = Query(..., description="Natural language query"),
    page_size: int = Query(10, ge=1, le=50),
    tenant_id: str = Depends(get_current_tenant_id),
    planner: SearchPlanner = Depends(get_semantic_planner),
):
    query = SearchQuery(query=q, page_size=page_size, tenant_id=tenant_id)
    result = await planner.search(query)

    return {
        "query": q,
        "intent": detect_intent(q).intent.name,
        "strategy": result.strategy,
        "total": result.total,
        "duration_ms": result.duration_ms,
        "items": [
            {
                "id": str(item.id),
                "name_ar": item.name_ar,
                "name_en": item.name_en,
                "cr_number": item.cr_number,
                "city": item.city,
            }
            for item in result.items
        ],
        "ranking": result.ranking[:5],
    }


@router.post("/search/similar")
async def similar_companies(
    company_id: str = Query(..., description="Source company ID"),
    top_k: int = Query(10, ge=1, le=50),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    repo: PgVectorCompanyRepository = Depends(get_pgvector_repo),
):
    result = await repo.similar_to(company_id, top_k=top_k)

    return {
        "source_company_id": company_id,
        "total": result.total,
        "duration_ms": result.duration_ms,
        "items": [
            {
                "id": str(item.id),
                "name_ar": item.name_ar,
                "name_en": item.name_en,
                "cr_number": item.cr_number,
                "city": item.city,
                "similarity_score": next(
                    (r["score"] for r in result.ranking if r.get("id") == str(item.id)),
                    None,
                ),
            }
            for item in result.items
        ],
    }
