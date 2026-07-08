"""Knowledge Graph Runtime REST API.

Endpoints:
  POST /api/v1/graph/populate/{company_id}    — Populate graph from golden record
  POST /api/v1/graph/rebuild                  — Rebuild entire graph for tenant
  GET  /api/v1/graph/competitors/{company_id} — Find competitors
  GET  /api/v1/graph/path                     — Find shortest path between two entities
  GET  /api/v1/graph/network/{company_id}     — Get ego network
  GET  /api/v1/graph/decision-makers/{company_id} — Get senior contacts
  GET  /api/v1/graph/search                   — Full-text graph search
  GET  /api/v1/graph/query                    — Raw graph query
  GET  /api/v1/graph/metrics                  — Graph engine metrics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_current_tenant_id, get_db_session

router = APIRouter()


@router.post("/graph/populate/{company_id}")
async def populate_graph(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        raise HTTPException(status_code=503, detail="Knowledge Graph not initialized")
    result = await kg.populate_from_golden_record(
        {"company_id": company_id, "id": company_id}, tenant_id
    )
    return {"status": "ok", "company_id": company_id, "stats": result}


@router.post("/graph/rebuild")
async def rebuild_graph(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        raise HTTPException(status_code=503, detail="Knowledge Graph not initialized")
    result = await kg.rebuild(tenant_id)
    return {"status": "ok", "tenant_id": tenant_id, "stats": result}


@router.get("/graph/competitors/{company_id}")
async def find_competitors(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    limit: int = Query(10, ge=1, le=50),
):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        raise HTTPException(status_code=503, detail="Knowledge Graph not initialized")
    nodes = await kg.find_competitors(company_id, tenant_id, limit)
    return {"company_id": company_id, "competitors": [n.to_dict() for n in nodes]}


@router.get("/graph/path")
async def find_path(
    source: str = Query(..., description="Source entity ID"),
    target: str = Query(..., description="Target entity ID"),
    request: Request = None,
    max_depth: int = Query(6, ge=1, le=10),
    tenant_id: str = Depends(get_current_tenant_id),
):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        raise HTTPException(status_code=503, detail="Knowledge Graph not initialized")
    path = await kg.find_path(source, target, max_depth)
    if not path:
        return {"path": None, "message": "No path found"}
    return {"path": path.to_dict()}


@router.get("/graph/network/{company_id}")
async def ego_network(
    company_id: str,
    request: Request,
    depth: int = Query(2, ge=1, le=4),
    tenant_id: str = Depends(get_current_tenant_id),
):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        raise HTTPException(status_code=503, detail="Knowledge Graph not initialized")
    items = await kg.get_ego_network(company_id, depth)
    return {"company_id": company_id, "network": items}


@router.get("/graph/decision-makers/{company_id}")
async def decision_makers(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        raise HTTPException(status_code=503, detail="Knowledge Graph not initialized")
    nodes = await kg.get_decision_makers(company_id)
    return {"company_id": company_id, "decision_makers": [n.to_dict() for n in nodes]}


@router.get("/graph/search")
async def graph_search(
    q: str = Query(..., description="Search query"),
    request: Request = None,
    limit: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        raise HTTPException(status_code=503, detail="Knowledge Graph not initialized")
    nodes = await kg.search(q, limit=limit)
    return {"query": q, "results": [n.to_dict() for n in nodes]}


@router.get("/graph/query/custom")
async def custom_graph_query(
    request: Request,
    entity_type: str = Query(..., description="Entity type: company, person, opportunity, contract"),
    relation: str = Query("", description="Relation filter"),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
):
    """General-purpose graph query returning connected entities."""
    import uuid
    from sqlalchemy import text as sa_text

    result = {"entity_type": entity_type, "items": [], "total": 0}

    if entity_type == "company":
        rows = await db.execute(
            sa_text("""
                SELECT c.id, c.name_ar, c.name_en, c.cr_number, c.status, c.city, c.region,
                    (SELECT COUNT(*) FROM contacts WHERE company_id = c.id) as contact_count,
                    (SELECT COUNT(*) FROM commercial_opportunities WHERE company_id = c.id) as opp_count
                FROM companies c
                WHERE c.tenant_id = :tid AND c.is_active = true
                ORDER BY c.created_at DESC
                LIMIT :lim
            """),
            {"tid": tenant_id, "lim": limit},
        )
        items = [dict(r) for r in rows.mappings().all()]
        result["items"] = [{k: str(v) if isinstance(v, uuid.UUID) else v for k, v in item.items()} for item in items]
        result["total"] = len(items)

    elif entity_type == "opportunity":
        rows = await db.execute(
            sa_text("""
                SELECT o.id, o.name, o.value, o.stage, o.status, o.probability,
                    o.company_id, o.owner_id, o.created_at
                FROM commercial_opportunities o
                WHERE o.tenant_id = :tid
                ORDER BY o.created_at DESC
                LIMIT :lim
            """),
            {"tid": tenant_id, "lim": limit},
        )
        result["items"] = [dict(r) for r in rows.mappings().all()]
        result["total"] = len(items)

    elif entity_type == "contract":
        rows = await db.execute(
            sa_text("""
                SELECT c.id, c.title, c.status, c.effective_date, c.expiry_date,
                    c.opportunity_id, c.created_at
                FROM commercial_contracts c
                WHERE c.tenant_id = :tid
                ORDER BY c.created_at DESC
                LIMIT :lim
            """),
            {"tid": tenant_id, "lim": limit},
        )
        result["items"] = [dict(r) for r in rows.mappings().all()]
        result["total"] = len(items)

    return result


@router.get("/graph/query/companies-without-activity")
async def companies_without_activity(
    request: Request,
    days: int = Query(30, ge=1, description="Days of inactivity"),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
):
    """Find companies with no activity in N days."""
    from sqlalchemy import text as sa_text
    from datetime import datetime, timezone, timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    rows = await db.execute(
        sa_text("""
            SELECT c.id, c.name_ar, c.name_en, c.cr_number, c.status, c.city,
                (SELECT MAX(a.timestamp)
                 FROM activity_records a
                 WHERE a.entity_type = 'company' AND a.entity_id = c.id) as last_activity
            FROM companies c
            WHERE c.tenant_id = :tid
              AND c.is_active = true
              AND (
                  SELECT MAX(a.timestamp)
                  FROM activity_records a
                  WHERE a.entity_type = 'company' AND a.entity_id = c.id
              ) IS DISTINCT FROM NULL
              AND (
                  SELECT MAX(a.timestamp)
                  FROM activity_records a
                  WHERE a.entity_type = 'company' AND a.entity_id = c.id
              ) < :cutoff
            ORDER BY last_activity ASC
            LIMIT :lim
        """),
        {"tid": tenant_id, "cutoff": cutoff, "lim": limit},
    )
    items = [dict(r) for r in rows.mappings().all()]
    return {"days": days, "cutoff": cutoff.isoformat(), "items": items, "total": len(items)}


@router.get("/graph/query/employees-with-most-meetings")
async def employees_with_most_meetings(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_current_tenant_id),
    db=Depends(get_db_session),
):
    """Find employees with the most meetings."""
    from sqlalchemy import text as sa_text

    rows = await db.execute(
        sa_text("""
            SELECT a.actor as user_id, COUNT(*) as meeting_count,
                MAX(a.timestamp) as last_meeting
            FROM activity_records a
            WHERE a.tenant_id = :tid
              AND a.action LIKE 'meeting.%'
            GROUP BY a.actor
            ORDER BY meeting_count DESC
            LIMIT :lim
        """),
        {"tid": tenant_id, "lim": limit},
    )
    items = [dict(r) for r in rows.mappings().all()]
    return {"items": items, "total": len(items)}


@router.get("/graph/metrics")
async def graph_metrics(request: Request, tenant_id: str = Depends(get_current_tenant_id)):
    kg = getattr(request.app.state, "kg_engine", None)
    if not kg:
        return {"status": "not_initialized"}
    return kg.metrics.snapshot()
