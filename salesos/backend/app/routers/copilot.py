"""AI Copilot — coordinates agents to answer user queries.

Phase 11 additions:
- B-1: search_companies tool integrated with Search domain
- B-2: Feedback endpoints (submit + stats)
- B-3: Tool telemetry logging + aggregation endpoints
- B-4: Arabic copilot engine (NLP detection, RTL, Saudi context)

GA honesty (Wave 6–7 + Completion Program Stream B / AIGOV-01):
product mutate/detect endpoints require settings.feature_ai_copilot.
Arabic detect/prompts + telemetry/log gated (EAB residual closure).
Read-only status/telemetry remain readable for honest empty dashboards.
Registration ≠ GA; see docs/audit/ga-engineering-audit/AI_HONESTY.md
"""

import time as _time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.config import settings
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    require_permission_dep,
    verify_token,
)
from domains.copilot.arabic import ArabicCopilotEngine
from domains.copilot.feedback_service import CopilotFeedbackService
from domains.copilot.models import CopilotMode, ToolTelemetryStats
from domains.copilot.schemas import (
    ArabicDetectRequest,
    ArabicDetectResponse,
    CopilotFeedbackResponse,
    CopilotFeedbackStatsResponse,
    CopilotFeedbackSubmit,
    CopilotModeRequest,
    CopilotModeResponse,
    SearchCompaniesRequest,
    ToolTelemetryBreakdownResponse,
    ToolTelemetryLogRequest,
    ToolTelemetryStatsResponse,
)
from domains.copilot.telemetry_service import ToolTelemetryService
from domains.copilot.tools import SearchCompaniesTool
from intelligence.agents import AgentCoordinator, AgentTask
from intelligence.agents.competitor import CompetitorAgent
from intelligence.agents.contract import ContractAgent
from intelligence.agents.forecast import ForecastAgent
from intelligence.agents.icp import ICPAgent
from intelligence.agents.llm import LLMService
from intelligence.agents.meeting import MeetingAgent
from intelligence.agents.news import NewsAgent
from intelligence.agents.pricing import PricingAgent
from intelligence.agents.proposal import ProposalAgent
from intelligence.agents.recommendation import RecommendationAgent
from intelligence.agents.relationship import RelationshipAgent
from intelligence.agents.renewal import RenewalAgent
from intelligence.agents.research import ResearchAgent
from intelligence.agents.tender import TenderAgent
from sdk.permissions import PermissionAction
from sdk.telemetry import StructuredLogger

router = APIRouter()

# ── Singleton services ──────────────────────────────────────────
_feedback_service = CopilotFeedbackService()
_telemetry_service = ToolTelemetryService()
_arabic_engine = ArabicCopilotEngine()

_COPILOT_DISABLED_DETAIL = (
    "AI Copilot is disabled (feature_ai_copilot=False). "
    "Experimental only — not GA. See AI_HONESTY.md."
)


def require_ai_copilot_enabled() -> None:
    """Block product use while Settings.feature_ai_copilot remains False."""
    if not settings.feature_ai_copilot:
        raise HTTPException(status_code=403, detail=_COPILOT_DISABLED_DETAIL)


class CopilotStatusResponse(BaseModel):
    feature_ai_copilot: bool
    classification: str
    ga_ready: bool = False


@router.get("/copilot/status", response_model=CopilotStatusResponse)
async def copilot_status(_auth=Depends(verify_token)):
    """Honest flag surface for FE gating — always readable when authenticated."""
    enabled = bool(settings.feature_ai_copilot)
    return CopilotStatusResponse(
        feature_ai_copilot=enabled,
        classification="experimental" if enabled else "disabled",
        ga_ready=False,
    )


class CopilotQuery(BaseModel):
    query: str
    company_id: str | None = None
    company_name: str | None = None
    cr_number: str | None = None
    city: str | None = None
    industry: str | None = None
    goal: str | None = None


class CopilotResponse(BaseModel):
    response: str
    confidence: float
    agent_used: str
    sources: list[str] = []
    conversation_id: str = ""


def _make_company_evidence_loader():
    """Async loader binding the ResearchAgent to real SalesOS records
    (Grounded Phase 1). Retrieval is (tenant_id, company_id)-scoped inside
    research_evidence.build_company_evidence; PII is stripped there."""

    async def _load(tenant_id: str, company_id: str):
        from intelligence.agents.research_evidence import build_company_evidence

        from app.database import async_session

        return await build_company_evidence(async_session, tenant_id, company_id)

    return _load


def _build_coordinator(
    tenant_id: str | None = None, user_id: str | None = None
) -> AgentCoordinator:
    llm = None
    if settings.openai_api_key:
        # Central ai_tokens quota accounting: bind the request's tenant/user to
        # the single LLMService instance all agents share, and hand it the
        # canonical async session factory for usage_meters recording.
        try:
            from app.database import async_session as _meter_session_factory
        except Exception:
            _meter_session_factory = None
        llm = LLMService(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url or None,
            default_tenant_id=tenant_id,
            default_user_id=user_id,
            usage_meter_factory=_meter_session_factory,
        )

    coordinator = AgentCoordinator()
    coordinator.register_agent(ResearchAgent(llm, evidence_loader=_make_company_evidence_loader()))
    # Grounded Phase 3B: all remaining agents share the same Phase-1
    # EvidencePack loader; identity is (tenant_id, company_id), never name.
    coordinator.register_agent(NewsAgent(llm, evidence_loader=_make_company_evidence_loader()))
    # Grounded Phase 2: competitor + relationship share the same Phase 1
    # EvidencePack loader; identity is (tenant_id, company_id), never name.
    coordinator.register_agent(CompetitorAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(ForecastAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(MeetingAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(ProposalAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(ContractAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(PricingAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(RenewalAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(TenderAgent(llm, evidence_loader=_make_company_evidence_loader()))
    coordinator.register_agent(RelationshipAgent(llm, evidence_loader=_make_company_evidence_loader()))
    # Grounded Phase 3A: ICP evaluation → recommendation share the same
    # Phase-1 EvidencePack loader; ICP uses the real runtime store only.
    # Phase 4B (ADR-0109 Option A): Postgres-backed store via sync adapter;
    # agents stay untouched — adapter satisfies the frozen MemICPStore shape.
    from app.modules.gtm.icp_persistence import get_sync_icp_store

    _icp_store = get_sync_icp_store()
    coordinator.register_agent(
        ICPAgent(llm, evidence_loader=_make_company_evidence_loader(), icp_store=_icp_store)
    )
    coordinator.register_agent(
        RecommendationAgent(
            llm, evidence_loader=_make_company_evidence_loader(), icp_store=_icp_store
        )
    )
    return coordinator


# ── B-1: search_companies tool ────────────────────────────────


@router.post("/copilot/search-companies")
async def copilot_search_companies(
    body: SearchCompaniesRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
    _flag=Depends(require_ai_copilot_enabled),
):
    """Search companies via copilot tool — structured results with < 1s latency."""
    search_repo = None
    try:
        from app.database import async_session
        from domains.search.engine.postgres_repo import PostgresSearchRepository

        search_repo = PostgresSearchRepository(session_factory=async_session)
    except Exception:
        pass

    tool = SearchCompaniesTool(search_repo=search_repo)
    result = await tool.execute(
        params={
            "query": body.query,
            "city": body.city,
            "industry": body.industry,
            "limit": body.limit,
        },
        context={"tenant_id": tenant_id, "user_id": user_id},
    )

    _telemetry_service.log(
        tool_name=tool.name,
        tenant_id=tenant_id,
        user_id=user_id,
        success=result.success,
        latency_ms=result.latency_ms,
        result_count=len(result.data),
        error_message=result.error,
    )

    return {
        "success": result.success,
        "data": result.data,
        "total": result.total,
        "latency_ms": round(result.latency_ms, 2),
        "tool_name": result.tool_name,
        "error": result.error,
    }


# ── Copilot Query (existing + enhanced) ──────────────────────


@router.post("/copilot/query", response_model=CopilotResponse)
async def copilot_query(
    body: CopilotQuery,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
    _flag=Depends(require_ai_copilot_enabled),
):
    logger: StructuredLogger | None = getattr(request.app.state, "logger", None)
    conversation_id = f"conv_{user_id}_{int(_time.time())}"

    # B-4: Detect Arabic and enrich context
    detection = _arabic_engine.detect(body.query)
    context = {
        "company_id": body.company_id,
        "company_name": body.company_name,
        "cr_number": body.cr_number,
        "city": body.city,
        "industry": body.industry,
    }
    context = _arabic_engine.enrich_saudi_context(body.query, context)
    context["tenant_id"] = tenant_id

    coordinator = _build_coordinator(tenant_id=tenant_id, user_id=user_id)
    task = AgentTask(
        id=f"copilot_{user_id}_{int(_time.time())}",
        agent_type="coordinator",
        input={"goal": body.goal or body.query, "context": context},
    )

    t0 = _time.monotonic()
    result = await coordinator.execute(task)
    latency_ms = (_time.monotonic() - t0) * 1000

    # Extract text response
    steps = result.output.get("results", [])
    texts = []
    for step in steps:
        out = step.get("output", {})
        text = (
            out.get("summary")
            or out.get("analysis")
            or out.get("proposal")
            or out.get("preparation")
            or out.get("message")
            or ""
        )
        if text:
            texts.append(text)

    response_text = "\n\n".join(texts) if texts else "لم يتم العثور على معلومات كافية."
    if not settings.openai_api_key:
        response_text = (
            "⚠️ لم يتم تكوين مفتاح OpenAI."
            " يرجى ضبط `OPENAI_API_KEY` في الإعدادات"
            " لتفعيل المساعد الذكي."
        )

    # B-4: Apply RTL markers if Arabic
    if detection.is_arabic:
        response_text = _arabic_engine.add_rtl_markers(response_text)

    # B-3: Log telemetry for coordinator
    _telemetry_service.log(
        tool_name="copilot_coordinator",
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        success=result.success,
        latency_ms=latency_ms,
        result_count=len(steps),
    )

    # P0-8: AI audit logging
    try:
        from app.database import async_session as _audit_session
        from app.modules.audit.ai_audit_service import AIAuditService
        from app.modules.audit.service import AuditService, PostgresAuditRepository

        async with _audit_session() as _s:
            _audit_repo = PostgresAuditRepository(_s)
            _audit_svc = AuditService(_audit_repo)
            _ai_audit = AIAuditService(_audit_svc)
            await _ai_audit.log_agent_call(
                tenant_id=tenant_id,
                user_id=user_id,
                agent_name="copilot_coordinator",
                metadata={
                    "conversation_id": conversation_id,
                    "confidence": result.confidence,
                    "query": body.query[:200],
                    "goal": body.goal[:200] if body.goal else None,
                    "latency_ms": latency_ms,
                    "num_steps": len(steps),
                },
            )
    except Exception:
        pass

    if logger:
        logger.info(
            "Copilot query: user=%s goal=%s confidence=%.2f lang=%s latency=%.0fms",
            user_id,
            (body.goal or body.query)[:50],
            result.confidence,
            "ar" if detection.is_arabic else "en",
            latency_ms,
        )

    return CopilotResponse(
        response=response_text,
        confidence=result.confidence,
        agent_used="coordinator",
        sources=[],
        conversation_id=conversation_id,
    )


# ── P3-1: Mode-aware copilot endpoint ─────────────────────────


@router.post("/copilot/mode", response_model=CopilotModeResponse)
async def copilot_mode(
    body: CopilotModeRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
    _flag=Depends(require_ai_copilot_enabled),
):
    """P3-1: Mode-aware copilot — Ask/Explain/Summarize/Investigate/Recommend.

    Recommend mode creates an approval request (HITL gate) — no auto-execute.
    """
    from domains.approval.contracts.models import (
        ApprovalLevel,
        ApprovalTargetType,
    )
    from domains.approval.in_memory_repo import InMemoryApprovalRepository
    from domains.approval.engine.service import ApprovalService

    logger: StructuredLogger | None = getattr(request.app.state, "logger", None)
    conversation_id = f"conv_{user_id}_{int(_time.time())}"
    mode = body.mode

    # Detect Arabic
    detection = _arabic_engine.detect(body.query)
    context = {**body.context, "tenant_id": tenant_id, "user_id": user_id}

    # Build coordinator
    coordinator = _build_coordinator(tenant_id=tenant_id, user_id=user_id)
    task = AgentTask(
        id=f"copilot_{mode}_{user_id}_{int(_time.time())}",
        agent_type="coordinator",
        input={"goal": body.query, "context": context},
    )

    t0 = _time.monotonic()
    result = await coordinator.execute(task)
    latency_ms = (_time.monotonic() - t0) * 1000

    # Extract text
    steps = result.output.get("results", [])
    texts = []
    evidence_items = []
    for step in steps:
        out = step.get("output", {})
        text = (
            out.get("summary")
            or out.get("analysis")
            or out.get("proposal")
            or out.get("preparation")
            or out.get("message")
            or ""
        )
        if text:
            texts.append(text)
        # Collect evidence
        if "evidence" in out:
            evidence_items.extend(out["evidence"])

    response_text = "\n\n".join(texts) if texts else "لم يتم العثور على معلومات كافية."
    if not settings.openai_api_key:
        response_text = (
            "⚠️ لم يتم تكوين مفتاح OpenAI."
            " يرجى ضبط `OPENAI_API_KEY` في الإعدادات لتفعيل المساعد الذكي."
        )

    if detection.is_arabic:
        response_text = _arabic_engine.add_rtl_markers(response_text)

    # Log telemetry
    _telemetry_service.log(
        tool_name=f"copilot_{mode}",
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        success=result.success,
        latency_ms=latency_ms,
        result_count=len(steps),
    )

    # P3-1: Recommend mode → HITL approval gate (no auto-execute)
    approval_id = None
    requires_approval = False
    if mode == CopilotMode.RECOMMEND:
        requires_approval = True
        approval_svc = ApprovalService(repository=InMemoryApprovalRepository())
        approval_req = await approval_svc.create_request(
            tenant_id=tenant_id,
            target_type=ApprovalTargetType.NBA_RECOMMENDATION,
            target_id=f"copilot_{conversation_id}",
            requested_by=user_id,
            action_summary=response_text[:500],
            action_evidence=[e.get("description", str(e)) for e in evidence_items[:5]],
            required_level=ApprovalLevel.MANAGER,
            assigned_to="",
            metadata={
                "conversation_id": conversation_id,
                "mode": mode,
                "confidence": result.confidence,
            },
        )
        approval_id = approval_req.id

    if logger:
        logger.info(
            "Copilot mode=%s: user=%s confidence=%.2f lang=%s latency=%.0fms approval=%s",
            mode,
            user_id,
            result.confidence,
            "ar" if detection.is_arabic else "en",
            latency_ms,
            approval_id or "none",
        )

    return CopilotModeResponse(
        mode=mode,
        response=response_text,
        confidence=result.confidence,
        sources=[],
        evidence=evidence_items,
        approval_id=approval_id,
        requires_approval=requires_approval,
        conversation_id=conversation_id,
    )


# ── B-2: Feedback endpoints ──────────────────────────────────


@router.post("/copilot/feedback", response_model=CopilotFeedbackResponse, status_code=201)
async def submit_feedback(
    body: CopilotFeedbackSubmit,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.CREATE)),
    _flag=Depends(require_ai_copilot_enabled),
):
    """Submit thumbs up/down feedback for a copilot response."""
    feedback = _feedback_service.submit(
        conversation_id=body.conversation_id,
        message_id=body.message_id,
        user_id=user_id,
        tenant_id=tenant_id,
        rating=body.rating,
        comment=body.comment,
        tool_name=body.tool_name,
    )
    return CopilotFeedbackResponse(
        id=feedback.id,
        conversation_id=feedback.conversation_id,
        message_id=feedback.message_id,
        rating=feedback.rating.value,
        comment=feedback.comment,
        tool_name=feedback.tool_name,
        created_at=feedback.created_at.isoformat(),
    )


@router.get("/copilot/feedback/stats", response_model=CopilotFeedbackStatsResponse)
async def feedback_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
):
    """Get aggregated feedback statistics (satisfaction rate, per-tool breakdown)."""
    stats = _feedback_service.get_stats(tenant_id=tenant_id)
    return CopilotFeedbackStatsResponse(
        total_feedback=stats.total_feedback,
        positive_count=stats.positive_count,
        negative_count=stats.negative_count,
        satisfaction_rate=stats.satisfaction_rate,
        by_tool=stats.by_tool,
    )


# ── B-3: Tool Telemetry endpoints ────────────────────────────


@router.get("/copilot/telemetry")
async def telemetry_dashboard(
    days: int = Query(30, ge=1, le=365),
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
):
    """Aggregate telemetry payload for FE `/copilot/telemetry` page.

    Read-only dashboard; does not require feature_ai_copilot (honest empty OK).
    """
    period_hours = float(days * 24)
    overall = _telemetry_service.get_stats(tenant_id=tenant_id, period_hours=period_hours)
    by_tool = _telemetry_service.get_tool_breakdown(tenant_id=tenant_id, period_hours=period_hours)
    volume_raw = _telemetry_service.get_volume_over_time(
        tenant_id=tenant_id,
        period_hours=period_hours,
        bucket_minutes=1440 if days > 7 else 60,
    )

    tools: list[dict[str, Any]] = [
        {
            "tool_name": s.tool_name,
            "total_calls": s.total_calls,
            "success_count": s.success_count,
            "failure_count": s.failure_count,
            "success_rate": s.success_rate,
            "latency_p50_ms": s.latency_p50_ms,
            "latency_p95_ms": s.latency_p95_ms,
            "latency_p99_ms": s.latency_p99_ms,
            "avg_result_count": s.result_count_avg,
        }
        for s in by_tool.values()
    ]
    tools.sort(key=lambda t: int(t["total_calls"]), reverse=True)

    latency_distribution = [
        {
            "label": s.tool_name,
            "p50": s.latency_p50_ms,
            "p95": s.latency_p95_ms,
            "p99": s.latency_p99_ms,
        }
        for s in by_tool.values()
    ] or [{"label": "overall", "p50": 0, "p95": 0, "p99": 0}]

    # Result-count histogram from overall buckets
    result_histogram: list[dict[str, Any]] = [
        {"label": "0", "count": 0},
        {"label": "1-5", "count": 0},
        {"label": "6-20", "count": 0},
        {"label": "20+", "count": 0},
    ]
    cutoff_hours = period_hours
    from datetime import UTC, datetime, timedelta

    cutoff = datetime.now(UTC) - timedelta(hours=cutoff_hours)
    for r in _telemetry_service._records:
        if r.tenant_id and r.tenant_id != tenant_id:
            continue
        if r.timestamp < cutoff:
            continue
        c = r.result_count
        if c <= 0:
            result_histogram[0]["count"] += 1
        elif c <= 5:
            result_histogram[1]["count"] += 1
        elif c <= 20:
            result_histogram[2]["count"] += 1
        else:
            result_histogram[3]["count"] += 1

    volume_over_time = [
        {
            "date": v.get("timestamp", "")[:10],
            "calls": v.get("total", 0),
            "successes": v.get("success", 0),
            "failures": v.get("failure", 0),
        }
        for v in volume_raw
    ]

    return {
        "summary": {
            "total_calls": overall.total_calls,
            "success_rate": overall.success_rate,
            "avg_latency_ms": overall.latency_avg_ms,
            "p95_latency_ms": overall.latency_p95_ms,
        },
        "tools": tools,
        "latency_distribution": latency_distribution,
        "result_histogram": result_histogram,
        "volume_over_time": volume_over_time,
        "period_days": days,
    }


@router.get("/copilot/telemetry/stats", response_model=ToolTelemetryStatsResponse)
async def telemetry_stats(
    tool_name: str | None = Query(None, description="Filter by tool name"),
    period_hours: float = Query(24.0, ge=1, le=168),
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
):
    """Get tool telemetry: success rate, p50/p95/p99 latency, result counts."""
    stats = _telemetry_service.get_stats(
        tool_name=tool_name,
        tenant_id=tenant_id,
        period_hours=period_hours,
    )
    return ToolTelemetryStatsResponse(
        tool_name=stats.tool_name,
        total_calls=stats.total_calls,
        success_count=stats.success_count,
        failure_count=stats.failure_count,
        success_rate=stats.success_rate,
        latency_p50_ms=stats.latency_p50_ms,
        latency_p95_ms=stats.latency_p95_ms,
        latency_p99_ms=stats.latency_p99_ms,
        latency_avg_ms=stats.latency_avg_ms,
        result_count_avg=stats.result_count_avg,
        calls_per_hour=stats.calls_per_hour,
        period_hours=stats.period_hours,
    )


@router.get("/copilot/telemetry/breakdown", response_model=ToolTelemetryBreakdownResponse)
async def telemetry_breakdown(
    period_hours: float = Query(24.0, ge=1, le=168),
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
):
    """Get per-tool telemetry breakdown with overall stats."""
    overall = _telemetry_service.get_stats(tenant_id=tenant_id, period_hours=period_hours)
    by_tool_raw = _telemetry_service.get_tool_breakdown(
        tenant_id=tenant_id, period_hours=period_hours
    )

    def _to_response(s: "ToolTelemetryStats") -> ToolTelemetryStatsResponse:
        return ToolTelemetryStatsResponse(
            tool_name=s.tool_name,
            total_calls=s.total_calls,
            success_count=s.success_count,
            failure_count=s.failure_count,
            success_rate=s.success_rate,
            latency_p50_ms=s.latency_p50_ms,
            latency_p95_ms=s.latency_p95_ms,
            latency_p99_ms=s.latency_p99_ms,
            latency_avg_ms=s.latency_avg_ms,
            result_count_avg=s.result_count_avg,
            calls_per_hour=s.calls_per_hour,
            period_hours=s.period_hours,
        )

    return ToolTelemetryBreakdownResponse(
        overall=_to_response(overall),
        by_tool={name: _to_response(s) for name, s in by_tool_raw.items()},
    )


@router.get("/copilot/telemetry/volume")
async def telemetry_volume(
    tool_name: str | None = Query(None),
    period_hours: float = Query(24.0, ge=1, le=168),
    bucket_minutes: int = Query(60, ge=5, le=1440),
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
):
    """Get call volume over time (bucketed)."""
    volume = _telemetry_service.get_volume_over_time(
        tool_name=tool_name,
        tenant_id=tenant_id,
        period_hours=period_hours,
        bucket_minutes=bucket_minutes,
    )
    return {"data": volume, "period_hours": period_hours, "bucket_minutes": bucket_minutes}


@router.post("/copilot/telemetry/log", status_code=201)
async def telemetry_log(
    body: ToolTelemetryLogRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.CREATE)),
    _flag=Depends(require_ai_copilot_enabled),
):
    """Manually log a tool call (for testing or external integrations).

    Gated: write path must not invent live copilot activity while flag is False.
    """
    record = _telemetry_service.log(
        tool_name=body.tool_name,
        tenant_id=tenant_id,
        user_id=user_id,
        success=body.success,
        latency_ms=body.latency_ms,
        result_count=body.result_count,
        error_message=body.error_message,
    )
    return {"id": record.id, "tool_name": record.tool_name, "logged": True}


# ── B-4: Arabic Copilot endpoints ────────────────────────────


@router.post("/copilot/arabic/detect", response_model=ArabicDetectResponse)
async def arabic_detect(
    body: ArabicDetectRequest,
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
    _flag=Depends(require_ai_copilot_enabled),
):
    """Detect Arabic content and extract Saudi business entities.

    AIGOV-01: gated with feature_ai_copilot (was ungated residual).
    """
    detection = _arabic_engine.detect(body.text)
    return ArabicDetectResponse(
        is_arabic=detection.is_arabic,
        arabic_ratio=detection.arabic_ratio,
        contains_diacritics=detection.contains_diacritics,
        detected_entities=detection.detected_entities,
        language=_arabic_engine.detect_language(body.text),
    )


@router.get("/copilot/arabic/prompts")
async def arabic_prompts(
    intent: str = Query(
        "default",
        description="Prompt intent: research, proposal, meeting, search, default",
    ),
    _rbac=Depends(require_permission_dep("copilot", PermissionAction.READ)),
    _flag=Depends(require_ai_copilot_enabled),
):
    """Get Arabic or English prompt template for a given intent.

    AIGOV-01: gated with feature_ai_copilot (was ungated residual).
    """
    ar_template = _arabic_engine.get_prompt_template(intent, "ar")
    en_template = _arabic_engine.get_prompt_template(intent, "en")
    return {
        "intent": intent,
        "arabic": ar_template,
        "english": en_template,
    }
