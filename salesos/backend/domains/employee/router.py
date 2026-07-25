from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import CursorResponse
from app.common.exceptions import NotFoundError
from app.dependencies import (
    get_current_tenant_id, get_current_user_id,
    get_db_session, require_permission_dep,
)
from sdk.pagination import CursorPage
from sdk.permissions import PermissionAction

from .postgres_repo import PostgresEmployeeSignalRepository
from .scoring import EmployeeScoringEngine
from .schemas import (
    BulkDeleteEmployeesRequest, BulkDeleteEmployeesResponse,
    BulkEditEmployeesRequest, BulkEditEmployeesResponse,
    EmployeeScoreResponse, EmployeeSignalResponse,
    EmployeeSignalSummaryResponse,
    EmployeeSignalsSummaryResponse, SignalTypeBreakdown, SignalSourceBreakdown,
    SignalTrendPoint, SOURCE_LABELS, SIGNAL_TYPE_LABELS,
    EmployeeScoreDetailResponse, ScoreFactor,
    EmployeeTimelineDataResponse, EmployeeTimelineEvent,
    EmployeePerformanceResponse, ScoreTrendPoint, PeerComparisonItem,
    RiskFlagResponse,
)
from .signals import SignalPipeline
from .audit import EmployeeAuditLogger

router = APIRouter()


def _get_repo(db: AsyncSession) -> PostgresEmployeeSignalRepository:
    return PostgresEmployeeSignalRepository(db)


def _get_audit(db: AsyncSession) -> EmployeeAuditLogger:
    return EmployeeAuditLogger(db)


def _get_pipeline(request: Request, db: AsyncSession) -> SignalPipeline:
    repo = _get_repo(db)
    return SignalPipeline(
        repository=repo,
        activity_runtime=getattr(request.app.state, "activity_runtime", None),
        timeline_recorder=getattr(request.app.state, "timeline_recorder", None),
        workflow_service=getattr(request.app.state, "workflow_service", None),
        logger=getattr(request.app.state, "logger", None),
    )


def _get_scorer(db: AsyncSession) -> EmployeeScoringEngine:
    repo = _get_repo(db)
    return EmployeeScoringEngine(repository=repo)


def _signal_to_timeline_event(s: EmployeeSignal) -> dict[str, Any]:
    meta = s.metadata or {}
    title = meta.get("title") or meta.get("description") or s.signal_type.replace("_", " ").title()
    actor = meta.get("actor", "")
    return {
        "id": s.id,
        "action": s.signal_type,
        "title": title,
        "source": s.source,
        "source_label": SOURCE_LABELS.get(s.source, s.source),
        "timestamp": s.timestamp.isoformat() if hasattr(s.timestamp, "isoformat") else str(s.timestamp),
        "actor": actor,
        "entity_type": meta.get("entity_type"),
        "entity_id": meta.get("entity_id"),
        "metadata": meta,
    }


# ── B-1: Signals Pipeline ──────────────────────────────────────────


@router.post("/employees/{employee_id}/signals/collect", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def collect_employee_signals(
    employee_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    pipeline = _get_pipeline(request, db)
    signals = await pipeline.collect_for_employee(employee_id, tenant_id)
    try:
        audit = _get_audit(db)
        await audit.log_collect_signals(employee_id, len(signals), user_id, tenant_id)
    except Exception:
        pass
    return {"collected": len(signals), "employee_id": employee_id}


@router.get("/employees/{employee_id}/signals", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def list_employee_signals(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    source: str | None = Query(None),
    signal_type: str | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
):
    repo = _get_repo(db)
    items, total, next_cursor = await repo.get_by_employee(
        employee_id, tenant_id,
        since=since, until=until,
        source=source, signal_type=signal_type,
        limit=limit, cursor=cursor,
    )

    summary = await repo.get_summary(employee_id, tenant_id)
    by_type_raw: dict[str, int] = summary.get("by_type", {})
    by_source_raw: dict[str, int] = summary.get("by_source", {})

    by_type = [
        SignalTypeBreakdown(
            type=t, count=c,
            label=SIGNAL_TYPE_LABELS.get(t, t.replace("_", " ").title()),
        )
        for t, c in sorted(by_type_raw.items(), key=lambda x: -x[1])
    ]
    by_source = [
        SignalSourceBreakdown(
            source=s, count=c,
            label=SOURCE_LABELS.get(s, s.title()),
        )
        for s, c in sorted(by_source_raw.items(), key=lambda x: -x[1])
    ]

    trend = _compute_signal_trend(items)

    return EmployeeSignalsSummaryResponse(
        by_type=by_type,
        by_source=by_source,
        trend=trend,
        total=summary.get("total_signals", 0),
    )


def _compute_signal_trend(signals: list) -> list[SignalTrendPoint]:
    from collections import Counter
    now = datetime.now(timezone.utc)
    day_counts: Counter[str] = Counter()
    for s in signals:
        ts = s.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if (now - ts).total_seconds() <= 30 * 86400:
            day_key = ts.strftime("%Y-%m-%d")
            day_counts[day_key] += 1
    trend = []
    for i in range(29, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append(SignalTrendPoint(date=d, count=day_counts.get(d, 0)))
    return trend


# ── B-2: Employee Scoring ─────────────────────────────────────────


@router.post("/employees/{employee_id}/score", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def compute_employee_score(
    employee_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    scorer = _get_scorer(db)
    score = await scorer.compute_score(employee_id, tenant_id)
    repo = _get_repo(db)
    all_signals, _, _ = await repo.get_by_employee(employee_id, tenant_id, limit=500)
    try:
        audit = _get_audit(db)
        await audit.log_score_compute(employee_id, round(score.overall_score * 100, 1), user_id, tenant_id)
    except Exception:
        pass
    return _build_score_detail(score, all_signals, repo)


@router.get("/employees/{employee_id}/score", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def get_employee_score(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    repo = _get_repo(db)
    score = await repo.get_latest_score(employee_id, tenant_id)
    if not score:
        return EmployeeScoreDetailResponse(score=0, trend="stable", confidence=0, factors=[])
    all_signals, _, _ = await repo.get_by_employee(employee_id, tenant_id, limit=500)
    return _build_score_detail(score, all_signals, repo)


def _build_score_detail(score, signals, repo=None) -> EmployeeScoreDetailResponse:
    ci_width = score.confidence_interval_high - score.confidence_interval_low
    confidence = max(0, min(100, round((1 - ci_width) * 100)))

    from .performance import EmployeePerformanceEngine
    engine = EmployeePerformanceEngine(repository=repo)
    old_signals_30d = [
        s for s in signals
        if s.timestamp and (datetime.now(timezone.utc) - s.timestamp).total_seconds() >= 30 * 86400
    ]
    prev_score = 0.0
    if old_signals_30d:
        from .scoring import EmployeeScoringEngine
        scorer = EmployeeScoringEngine(repository=repo)
        old_volume = scorer._compute_signal_volume(old_signals_30d)
        prev_score = round(
            0.30 * old_volume +
            0.25 * scorer._compute_recency(old_signals_30d) +
            0.20 * scorer._compute_diversity(old_signals_30d) +
            0.25 * scorer._compute_completion_rate(old_signals_30d), 4,
        )
    delta = score.overall_score - prev_score
    if delta > 0.02:
        trend = "up"
    elif delta < -0.02:
        trend = "down"
    else:
        trend = "stable"

    factors = [
        ScoreFactor(
            name="signal_volume", contribution=round(score.signal_volume_score * 100, 1),
            signal_type="system", label="Signal Volume",
        ),
        ScoreFactor(
            name="recency", contribution=round(score.recency_score * 100, 1),
            signal_type="system", label="Recency",
        ),
        ScoreFactor(
            name="diversity", contribution=round(score.diversity_score * 100, 1),
            signal_type="system", label="Diversity",
        ),
        ScoreFactor(
            name="completion", contribution=round(score.completion_rate * 100, 1),
            signal_type="system", label="Completion Rate",
        ),
    ]

    return EmployeeScoreDetailResponse(
        score=round(score.overall_score * 100, 1),
        trend=trend,
        confidence=confidence,
        factors=factors,
    )


# ── B-3: Employee Timeline ────────────────────────────────────────


@router.get("/employees/{employee_id}/timeline", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def employee_timeline(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    source: str | None = Query(None),
    signal_type: str | None = Query(None),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
):
    repo = _get_repo(db)
    items, total, next_cursor = await repo.get_by_employee(
        employee_id, tenant_id,
        since=from_date, until=to_date,
        source=source, signal_type=signal_type,
        limit=limit, cursor=cursor,
    )
    events = [_signal_to_timeline_event(s) for s in items]
    return EmployeeTimelineDataResponse(
        events=[EmployeeTimelineEvent(**e) for e in events],
        next_cursor=next_cursor,
        has_next=next_cursor is not None,
        total=total,
    )


# ── B-4: Employee Performance ─────────────────────────────────────


@router.get("/employees/{employee_id}/performance", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def get_employee_performance(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from sqlalchemy import select
    from app.modules.identity.models import User

    repo = _get_repo(db)
    all_signals, _, _ = await repo.get_by_employee(employee_id, tenant_id, limit=500)
    current_score = await repo.get_latest_score(employee_id, tenant_id)

    user_result = await db.execute(
        select(User).where(User.id == employee_id, User.tenant_id == tenant_id)
    )
    user = user_result.scalar_one_or_none()
    department = user.department if user else None

    score_trend = _build_score_trend(all_signals)
    current = round(current_score.overall_score * 100, 1) if current_score else 0.0

    if score_trend and len(score_trend) >= 2:
        first_half = sum(p.score for p in score_trend[:len(score_trend) // 2]) / max(1, len(score_trend) // 2)
        second_half = sum(p.score for p in score_trend[len(score_trend) // 2:]) / max(1, len(score_trend) - len(score_trend) // 2)
        delta = second_half - first_half
        if delta > 2:
            direction = "up"
        elif delta < -2:
            direction = "down"
        else:
            direction = "stable"
    else:
        direction = "stable"

    peer_comparison = await _build_peer_comparison(repo, employee_id, tenant_id, current_score)
    risk_flags = _build_risk_flags(all_signals, current_score, direction)
    factors = _build_performance_factors(current_score)

    return EmployeePerformanceResponse(
        score_trend=score_trend,
        peer_comparison=peer_comparison,
        risk_flags=risk_flags,
        factors=factors,
        current_score=current,
        score_trend_direction=direction,
        department=department,
    )


def _build_score_trend(signals: list) -> list[ScoreTrendPoint]:
    from collections import defaultdict
    now = datetime.now(timezone.utc)
    daily: dict[str, list[float]] = defaultdict(list)

    for s in signals:
        ts = s.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        days_ago = (now - ts).total_seconds() / 86400
        if days_ago <= 30:
            day_key = ts.strftime("%Y-%m-%d")
            daily[day_key].append(1.0)

    trend = []
    cumulative = 0.0
    for i in range(29, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        count = len(daily.get(d, []))
        cumulative = cumulative * 0.85 + count * 0.15
        trend.append(ScoreTrendPoint(date=d, score=round(cumulative * 100, 1)))

    return trend


async def _build_peer_comparison(
    repo: PostgresEmployeeSignalRepository,
    employee_id: str,
    tenant_id: str,
    current_score,
) -> list[PeerComparisonItem]:
    if not current_score:
        return []

    from sqlalchemy import select
    from app.modules.identity.models import User
    from .db_models import EmployeeScoreModel

    try:
        db_session = repo.db
        user_result = await db_session.execute(
            select(User).where(User.id == employee_id, User.tenant_id == tenant_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []

        peers_result = await db_session.execute(
            select(User.id).where(
                User.tenant_id == tenant_id,
                User.role == user.role,
                User.is_active == True,
                User.id != employee_id,
            ).limit(50)
        )
        peer_ids = [row[0] for row in peers_result.fetchall()]

        if not peer_ids:
            return []

        import uuid as uuid_mod
        scores_result = await db_session.execute(
            select(EmployeeScoreModel).where(
                EmployeeScoreModel.employee_id.in_([uuid_mod.UUID(str(pid)) for pid in peer_ids]),
                EmployeeScoreModel.tenant_id == uuid_mod.UUID(str(tenant_id)),
            )
        )
        peer_scores = scores_result.scalars().all()

        metrics = [
            ("overall", "Overall Score", current_score.overall_score,
             sum(s.overall_score for s in peer_scores) / max(1, len(peer_scores))),
            ("volume", "Signal Volume", current_score.signal_volume_score,
             sum(s.signal_volume_score for s in peer_scores) / max(1, len(peer_scores))),
            ("diversity", "Diversity", current_score.diversity_score,
             sum(s.diversity_score for s in peer_scores) / max(1, len(peer_scores))),
            ("completion", "Completion Rate", current_score.completion_rate,
             sum(s.completion_rate for s in peer_scores) / max(1, len(peer_scores))),
        ]

        return [
            PeerComparisonItem(
                metric=name,
                employee_value=round(val * 100, 1),
                department_avg=round(avg * 100, 1),
                label=label,
            )
            for name, label, val, avg in metrics
        ]
    except Exception:
        return []


def _build_risk_flags(signals, current_score, direction: str) -> list[RiskFlagResponse]:
    flags = []
    now = datetime.now(timezone.utc)

    if len(signals) >= 2:
        sorted_signals = sorted(signals, key=lambda s: s.timestamp, reverse=True)
        recent_14d = [s for s in sorted_signals if (now - s.timestamp).total_seconds() < 14 * 86400]
        older_14d = [s for s in sorted_signals if 14 * 86400 <= (now - s.timestamp).total_seconds() < 28 * 86400]
        if older_14d and len(recent_14d) < len(older_14d) * 0.5:
            drop_pct = round((1 - len(recent_14d) / len(older_14d)) * 100, 1)
            flags.append(RiskFlagResponse(
                type="declining_signals",
                label="Declining Activity",
                severity="high",
                description=f"Signal volume dropped {drop_pct}% in last 14 days",
            ))

    last_7d = [s for s in signals if (now - s.timestamp).total_seconds() < 7 * 86400]
    if len(last_7d) < 3:
        flags.append(RiskFlagResponse(
            type="low_engagement",
            label="Low Engagement",
            severity="medium" if len(last_7d) > 0 else "high",
            description=f"Only {len(last_7d)} signals in last 7 days (threshold: 3)",
        ))

    if direction == "down":
        flags.append(RiskFlagResponse(
            type="declining_score",
            label="Declining Score",
            severity="high",
            description="Performance score trend is declining over the last 30 days",
        ))

    return flags


def _build_performance_factors(current_score) -> list[ScoreFactor]:
    if not current_score:
        return []
    return [
        ScoreFactor(
            name="signal_volume", contribution=round(current_score.signal_volume_score * 100, 1),
            signal_type="system", label="Signal Volume",
        ),
        ScoreFactor(
            name="recency", contribution=round(current_score.recency_score * 100, 1),
            signal_type="system", label="Recency",
        ),
        ScoreFactor(
            name="diversity", contribution=round(current_score.diversity_score * 100, 1),
            signal_type="system", label="Diversity",
        ),
        ScoreFactor(
            name="completion", contribution=round(current_score.completion_rate * 100, 1),
            signal_type="system", label="Completion Rate",
        ),
    ]


# ── B-5: Bulk Operations ──────────────────────────────────────────


@router.patch("/employees/bulk", response_model=BulkEditEmployeesResponse,
              dependencies=[Depends(require_permission_dep("employee", PermissionAction.UPDATE))])
async def bulk_update_employees(
    body: BulkEditEmployeesRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from app.modules.identity.models import User
    from sqlalchemy import select

    allowed_fields = {"role", "is_active", "department"}
    field_updates = {k: v for k, v in body.updates.items() if k in allowed_fields}

    updated = 0
    failed = 0
    errors = []

    for eid in body.employee_ids:
        try:
            result = await db.execute(
                select(User).where(User.id == eid, User.tenant_id == tenant_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                failed += 1
                errors.append({"employee_id": eid, "error": "Not found"})
                continue

            for key, value in field_updates.items():
                if key == "is_active":
                    setattr(user, key, bool(value))
                elif value is not None:
                    setattr(user, key, value)

            await db.flush()
            updated += 1
        except Exception as e:
            failed += 1
            errors.append({"employee_id": eid, "error": str(e)})

    try:
        audit = _get_audit(db)
        await audit.log_bulk_edit(body.employee_ids, body.updates, user_id, tenant_id)
    except Exception:
        pass

    return BulkEditEmployeesResponse(updated=updated, failed=failed, errors=errors)


@router.delete("/employees/bulk", response_model=BulkDeleteEmployeesResponse,
               dependencies=[Depends(require_permission_dep("employee", PermissionAction.DELETE))])
async def bulk_delete_employees(
    body: BulkDeleteEmployeesRequest,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from app.modules.identity.models import User
    from sqlalchemy import select

    deleted = 0
    for eid in body.employee_ids:
        try:
            result = await db.execute(
                select(User).where(User.id == eid, User.tenant_id == tenant_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                continue
            user.is_active = False
            user.deleted_at = datetime.now(timezone.utc)
            await db.flush()
            deleted += 1
        except Exception:
            pass

    try:
        audit = _get_audit(db)
        await audit.log_bulk_delete(body.employee_ids, user_id, tenant_id)
    except Exception:
        pass

    return BulkDeleteEmployeesResponse(deleted=deleted)


@router.get("/employees/export", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def export_employees(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    format: str = Query("csv", pattern="^(csv)$"),
    fields: str = Query("id,full_name,email,role,is_active,created_at"),
    employee_ids: str | None = Query(None, description="Comma-separated UUIDs"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from app.modules.identity.models import User
    from sqlalchemy import select

    field_list = [f.strip() for f in fields.split(",") if f.strip()]
    allowed = {"id", "full_name", "full_name_ar", "email", "role",
               "department", "is_active", "phone", "created_at", "last_login_at"}

    field_map = {}
    model_fields = [field_map.get(f, f) for f in field_list if f in allowed or field_map.get(f) in allowed]
    cols = [getattr(User, mf) for mf in model_fields]

    stmt = select(*cols).where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
    if employee_ids:
        import uuid
        ids = [uuid.UUID(cid.strip()) for cid in employee_ids.split(",") if cid.strip()]
        stmt = stmt.where(User.id.in_(ids))
    result = await db.execute(stmt)
    rows = result.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(field_list)
    for row_data in rows:
        writer.writerow(
            str(v.isoformat() if isinstance(v, datetime) else v) if v is not None else ""
            for v in row_data
        )

    content = output.getvalue()
    try:
        audit = _get_audit(db)
        ids_list = [cid.strip() for cid in employee_ids.split(",") if cid.strip()] if employee_ids else None
        await audit.log_export(field_list, ids_list, user_id, tenant_id)
    except Exception:
        pass
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=employees_export_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


# ── B-6: Employees List — Keyset Cursor Pagination ────────────────


@router.get("/employees", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def list_employees(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    q: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
):
    from app.modules.identity.models import User
    from sqlalchemy import select, func, or_

    query = select(User).where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
    count_query = select(func.count()).select_from(User).where(User.tenant_id == tenant_id, User.deleted_at.is_(None))

    if q:
        like = f"%{q}%"
        condition = or_(
            User.full_name.ilike(like),
            User.email.ilike(like),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total = await db.scalar(count_query) or 0

    if cursor:
        from sdk.pagination import build_keyset_condition, decode_cursor
        cursor_id, cursor_sort = decode_cursor(cursor)
        condition = build_keyset_condition(
            User, cursor_id, cursor_sort,
            sort_by="created_at", sort_dir="desc",
        )
        query = query.where(condition)

    query = query.order_by(User.created_at.desc()).limit(limit + 1)
    rows = (await db.execute(query)).scalars().all()

    next_cursor: str | None = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        from sdk.pagination import encode_cursor
        next_cursor = encode_cursor(str(last.id), last.created_at)

    items = [
        {
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "department": u.department,
            "is_active": u.is_active,
            "phone": u.phone,
            "avatar_url": u.avatar_url,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in rows
    ]

    return CursorResponse(
        data=items,
        next_cursor=next_cursor,
        has_next=next_cursor is not None,
        total=total,
    )
