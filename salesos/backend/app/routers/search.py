"""Experimental semantic search endpoints — NOT connected to default UI.

These endpoints demonstrate pgvector capability for evaluation purposes.
To be connected to SearchPlanner only after validation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.modules.company.pgvector_repository import PgVectorCompanyRepository
from domains.search.contracts.models import SearchQuery
from domains.search.engine.planner import SearchPlanner
from domains.search.engine.strategy_matrix import detect_intent
from sdk.permissions import PermissionAction

router = APIRouter()

# Process-local search log for analytics dashboard (demo/local). Persists only
# for the lifetime of the worker; empty until searches are recorded.
_search_event_log: list[dict] = []


def record_search_event(
    *,
    query: str,
    result_count: int,
    latency_ms: float,
    tenant_id: str = "",
    strategy: str = "",
) -> None:
    """Optional hook for search callers to feed the analytics dashboard."""
    _search_event_log.append(
        {
            "query": query,
            "result_count": result_count,
            "latency_ms": latency_ms,
            "tenant_id": tenant_id,
            "strategy": strategy,
            "timestamp": datetime.now(UTC),
        }
    )
    if len(_search_event_log) > 10_000:
        del _search_event_log[: len(_search_event_log) - 10_000]


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


@router.get("/search/analytics")
async def search_analytics(
    days: int = Query(30, ge=1, le=365),
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac=Depends(require_permission_dep("search", PermissionAction.READ)),
):
    """Search analytics dashboard payload expected by FE `/search/analytics`."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    entries = [
        e
        for e in _search_event_log
        if e.get("tenant_id") in ("", tenant_id) and e["timestamp"] >= cutoff
    ]

    total = len(entries)
    zeros = sum(1 for e in entries if e["result_count"] == 0)
    latencies = sorted(e["latency_ms"] for e in entries) if entries else []

    q_counter: Counter[str] = Counter()
    q_results: dict[str, list[int]] = defaultdict(list)
    for e in entries:
        q = (e.get("query") or "").strip()
        if not q:
            continue
        q_counter[q] += 1
        q_results[q].append(e["result_count"])

    top_queries = [
        {
            "query": q,
            "count": c,
            "avg_results": round(sum(q_results[q]) / len(q_results[q]), 2) if q_results[q] else 0,
        }
        for q, c in q_counter.most_common(10)
    ]

    buckets = [
        ("<50ms", 0, 50),
        ("50-100ms", 50, 100),
        ("100-250ms", 100, 250),
        ("250-500ms", 250, 500),
        ("500ms+", 500, 10_000_000),
    ]
    latency_distribution = []
    for label, lo, hi in buckets:
        group = [v for v in latencies if lo <= v < hi]
        if not group and not latencies:
            latency_distribution.append({"label": label, "p50": 0, "p95": 0, "p99": 0})
            continue
        if not group:
            continue
        sg = sorted(group)
        n = len(sg)
        latency_distribution.append(
            {
                "label": label,
                "p50": round(sg[n // 2], 2),
                "p95": round(sg[min(n - 1, int(n * 0.95))], 2),
                "p99": round(sg[min(n - 1, int(n * 0.99))], 2),
            }
        )

    by_day: dict[str, int] = defaultdict(int)
    for e in entries:
        by_day[e["timestamp"].date().isoformat()] += 1

    now = datetime.now(UTC)
    return {
        "total_queries": total,
        "zero_result_rate": round((zeros / total) * 100, 2) if total else 0.0,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "top_queries": top_queries,
        "latency_distribution": latency_distribution,
        "volume_over_time": [{"date": d, "count": c} for d, c in sorted(by_day.items())],
        "period": {
            "from": cutoff.isoformat(),
            "to": now.isoformat(),
        },
    }


@router.get("/search/semantic")
async def semantic_search(
    q: str = Query(..., description="Natural language query"),
    page_size: int = Query(10, ge=1, le=50),
    tenant_id: str = Depends(get_current_tenant_id),
    planner: SearchPlanner = Depends(get_semantic_planner),
    _rbac=Depends(require_permission_dep("search", PermissionAction.READ)),
):
    query = SearchQuery(query=q, page_size=page_size, tenant_id=tenant_id)
    result = await planner.search(query)

    record_search_event(
        query=q,
        result_count=result.total,
        latency_ms=float(result.duration_ms or 0),
        tenant_id=tenant_id,
        strategy=result.strategy or "",
    )

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
    _rbac=Depends(require_permission_dep("search", PermissionAction.READ)),
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
