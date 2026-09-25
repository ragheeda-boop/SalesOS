"""Tenant-scoped read API for persisted commercial insight evidence chains."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

router = APIRouter()


@router.get("/evidence/insights")
async def list_evidence_insights(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    target_type: str | None = Query(None, max_length=50),
    target_id: str | None = Query(None, max_length=64),
    category: str | None = Query(None, max_length=50),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("analytics", PermissionAction.READ)),
) -> dict:
    """Read persisted insights and their source metadata without exposing data payloads."""
    conditions = ["tenant_id = :tenant_id"]
    params: dict[str, object] = {"tenant_id": tenant_id}
    if target_type:
        conditions.append("target_type = :target_type")
        params["target_type"] = target_type
    if target_id:
        conditions.append("target_id = :target_id")
        params["target_id"] = target_id
    if category:
        conditions.append("category = :category")
        params["category"] = category
    where_sql = " AND ".join(conditions)

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM commercial_insights WHERE {where_sql}"), params
    )
    total = int(count_result.scalar_one() or 0)
    offset = (page - 1) * page_size
    insights_result = await db.execute(
        text(f"""
            SELECT id, category, title, description, target_id, target_type,
                   overall_confidence, confidence_level, created_at, updated_at
            FROM commercial_insights
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :page_size OFFSET :offset
        """),
        {**params, "page_size": page_size, "offset": offset},
    )
    insights = insights_result.mappings().all()
    insight_ids = [str(row["id"]) for row in insights]
    evidence_by_insight: dict[str, list[dict]] = {insight_id: [] for insight_id in insight_ids}

    if insight_ids:
        evidence_statement = text("""
            SELECT id, insight_id, evidence_type, source_domain, source_type,
                   source_id, source_name, description, confidence,
                   confidence_level, data->>'evidence_kind' AS evidence_kind,
                   created_at
            FROM commercial_evidence_items
            WHERE tenant_id = :tenant_id AND insight_id IN :insight_ids
            ORDER BY created_at ASC, id ASC
        """).bindparams(bindparam("insight_ids", expanding=True))
        evidence_result = await db.execute(
            evidence_statement, {"tenant_id": tenant_id, "insight_ids": insight_ids}
        )
        for item in evidence_result.mappings().all():
            evidence_by_insight[str(item["insight_id"])].append(
                {
                    "id": str(item["id"]),
                    "evidence_type": item["evidence_type"],
                    "source_domain": item["source_domain"],
                    "source_type": item["source_type"],
                    "source_id": item["source_id"] or "",
                    "source_name": item["source_name"] or "",
                    "description": item["description"],
                    "confidence": float(item["confidence"] or 0),
                    "confidence_level": item["confidence_level"] or "unknown",
                    "evidence_kind": item["evidence_kind"],
                    "recorded_at": item["created_at"].isoformat()
                    if isinstance(item["created_at"], datetime)
                    else None,
                }
            )

    return {
        "items": [
            {
                "id": str(row["id"]),
                "category": row["category"],
                "title": row["title"],
                "description": row["description"] or "",
                "target_id": row["target_id"],
                "target_type": row["target_type"],
                "overall_confidence": float(row["overall_confidence"] or 0),
                "confidence_level": row["confidence_level"] or "unknown",
                "created_at": row["created_at"].isoformat()
                if isinstance(row["created_at"], datetime)
                else None,
                "updated_at": row["updated_at"].isoformat()
                if isinstance(row["updated_at"], datetime)
                else None,
                "evidence_items": evidence_by_insight[str(row["id"])],
            }
            for row in insights
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "read_only": True,
    }
