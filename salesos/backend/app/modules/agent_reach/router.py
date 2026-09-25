"""Agent Reach REST API — hardened SalesOS integration endpoints.

Security:
- SSRF protection on all URL inputs
- Allowlisted operations only (no shell passthrough)
- Rate limiting per channel
- Audit trail logging
- Input validation + length limits
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.common.rate_limit import rate_limit_dep
from app.config import settings
from app.database import async_session
from app.dependencies import get_current_tenant_id, require_permission_dep
from sdk.permissions import PermissionAction

from .models import ChannelType, EvidenceItem, EvidenceType
from .persistence import PostgresEvidenceStore
from .service import AgentReachService, classify_signals_from_evidence

router = APIRouter(
    prefix="/api/v1/agent-reach",
    tags=["Agent Reach"],
    dependencies=[
        Depends(rate_limit_dep("agent_reach", settings.rate_limit_search, 60))
    ],
)

# Postgres-backed store (singleton)
_pg_store = PostgresEvidenceStore(async_session)


# ── Request Models ───────────────────────────────────────────────


class WebReadRequest(BaseModel):
    url: str = Field(..., max_length=2048, description="URL to read (SSRF-protected)")
    format: str = Field(default="markdown", pattern="^(markdown|text|html)$")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(default=10, ge=1, le=50)


class RSSRequest(BaseModel):
    feed_url: str = Field(..., max_length=2048, description="RSS/Atom feed URL")
    max_entries: int = Field(default=10, ge=1, le=100)


class LinkedInRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class GenericRequest(BaseModel):
    channel: str = Field(..., description="Channel: web, twitter, youtube, github, rss, bilibili, web_search, linkedin")
    action: str = Field(..., description="Action: read, search, subtitles, company, profile, jobs")
    query: str | None = Field(default=None, max_length=500)
    url: str | None = Field(default=None, max_length=2048)
    max_results: int = Field(default=10, ge=1, le=50)


class ResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    channels: list[str] = Field(default_factory=lambda: ["web", "github", "linkedin"])

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, channels: list[str]) -> list[str]:
        allowed = {"web", "github", "linkedin", "twitter", "youtube"}
        if not channels or len(channels) > len(allowed):
            raise ValueError("Select between 1 and 5 research channels")
        if len(set(channels)) != len(channels):
            raise ValueError("Research channels must be unique")
        unknown = sorted(set(channels) - allowed)
        if unknown:
            raise ValueError(f"Unsupported research channels: {', '.join(unknown)}")
        return channels


# ── Endpoints ────────────────────────────────────────────────────


@router.get("/status", summary="Check channel status", description="Check the status of all Agent Reach channels (web, Twitter, YouTube, GitHub, RSS, LinkedIn).")
async def get_status(
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.READ)),
):
    """Check status of all Agent Reach channels."""
    svc = AgentReachService()
    channels = await svc.check_status()
    return {
        "channels": [
            {
                "channel": ch.channel.value,
                "status": ch.status.value,
                "backend": ch.backend,
                "message": ch.message,
            }
            for ch in channels
        ]
    }


# ── Web ──────────────────────────────────────────────────────────


@router.post("/web/read", summary="Read a web page", description="Read a web page via Jina Reader with SSRF protection.")
async def read_web_page(
    body: WebReadRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Read a web page via Jina Reader (SSRF-protected)."""
    svc = AgentReachService()
    try:
        result = await svc.read_web_page(body.url, body.format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── Twitter ──────────────────────────────────────────────────────


@router.post("/twitter/search", summary="Search Twitter/X", description="Search Twitter/X for tweets matching a query.")
async def search_twitter(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Search Twitter/X."""
    svc = AgentReachService()
    try:
        result = await svc.search_twitter(body.query, body.max_results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


@router.post("/twitter/read", summary="Read a tweet", description="Read a single tweet by URL or ID.")
async def read_tweet(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Read a single tweet."""
    svc = AgentReachService()
    try:
        result = await svc.read_tweet(body.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── YouTube ──────────────────────────────────────────────────────


@router.post("/youtube/search", summary="Search YouTube", description="Search YouTube videos matching a query.")
async def search_youtube(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Search YouTube videos."""
    svc = AgentReachService()
    try:
        result = await svc.search_youtube(body.query, body.max_results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


@router.post("/youtube/subtitles", summary="Get YouTube subtitles", description="Get subtitles/captions for a YouTube video.")
async def get_youtube_subtitles(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Get YouTube video subtitles."""
    svc = AgentReachService()
    try:
        result = await svc.get_youtube_subtitles(body.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── GitHub ───────────────────────────────────────────────────────


@router.post("/github/search", summary="Search GitHub repos", description="Search GitHub repositories matching a query.")
async def search_github(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Search GitHub repositories."""
    svc = AgentReachService()
    try:
        result = await svc.search_github(body.query, body.max_results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


@router.post("/github/read", summary="Read GitHub repo info", description="Read detailed information about a GitHub repository.")
async def read_github_repo(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Read GitHub repo info."""
    svc = AgentReachService()
    try:
        result = await svc.read_github_repo(body.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── RSS ──────────────────────────────────────────────────────────


@router.post("/rss/read", summary="Read RSS/Atom feed", description="Read and parse an RSS or Atom feed URL.")
async def read_rss_feed(
    body: RSSRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Read RSS/Atom feed."""
    svc = AgentReachService()
    try:
        result = await svc.read_rss_feed(body.feed_url, body.max_entries)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── Bilibili ─────────────────────────────────────────────────────


@router.post("/bilibili/search", summary="Search Bilibili", description="Search Bilibili videos matching a query.")
async def search_bilibili(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Search Bilibili videos."""
    svc = AgentReachService()
    try:
        result = await svc.search_bilibili(body.query, body.max_results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── Web Search (Exa) ─────────────────────────────────────────────


@router.post("/web/search", summary="Semantic web search", description="Semantic web search via Exa with vector similarity matching.")
async def search_web(
    body: SearchRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Semantic web search via Exa."""
    svc = AgentReachService()
    try:
        result = await svc.search_web(body.query, body.max_results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── LinkedIn (dedicated) ─────────────────────────────────────────


@router.post("/linkedin/company", summary="Read LinkedIn company", description="Read a LinkedIn company page via Jina Reader.")
async def linkedin_company(
    body: LinkedInRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Read LinkedIn company page via Jina Reader."""
    svc = AgentReachService()
    try:
        result = await svc.linkedin_company(body.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


@router.post("/linkedin/profile", summary="Read LinkedIn profile", description="Read a LinkedIn profile via Jina Reader.")
async def linkedin_profile(
    body: LinkedInRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Read LinkedIn profile via Jina Reader."""
    svc = AgentReachService()
    try:
        result = await svc.linkedin_profile(body.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


@router.post("/linkedin/jobs", summary="Search LinkedIn jobs", description="Search LinkedIn job postings via Jina Reader.")
async def linkedin_jobs(
    body: LinkedInRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Search LinkedIn jobs via Jina Reader."""
    svc = AgentReachService()
    try:
        result = await svc.linkedin_jobs(body.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── Unified Research ─────────────────────────────────────────────


@router.post("/research/company", summary="Research a company", description="Research a company across multiple channels (web, GitHub, LinkedIn, Twitter, YouTube) in parallel. Stores evidence and extracts signals into Postgres.")
async def research_company(
    body: ResearchRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Research a company across multiple channels (parallel).

    Stores evidence + extracts signals into Postgres (RLS-scoped).
    Channels: web, github, linkedin, twitter, youtube
    """
    svc = AgentReachService()
    results = await svc.research_company(body.company_name, body.channels)

    # Persist tenant-owned evidence and derived signals under the same RLS scope.
    ch_type_map = {
        "web": (EvidenceType.WEB_SEARCH, ChannelType.WEB),
        "github": (EvidenceType.GITHUB_SEARCH, ChannelType.GITHUB),
        "linkedin": (EvidenceType.LINKEDIN_COMPANY, ChannelType.LINKEDIN),
        "twitter": (EvidenceType.TWEET, ChannelType.TWITTER),
        "youtube": (EvidenceType.VIDEO, ChannelType.YOUTUBE),
    }
    stored = 0
    evidence_items: list[EvidenceItem] = []
    for ch_name, res in results.items():
        if res.success and res.data:
            title = summary = source_url = ""
            if isinstance(res.data, dict):
                title = res.data.get("title") or res.data.get("name") or ""
                summary = res.data.get("description") or res.data.get("content") or ""
                source_url = res.data.get("url") or res.data.get("html_url") or ""
            elif isinstance(res.data, list) and res.data:
                first = res.data[0] if isinstance(res.data[0], dict) else {}
                title = first.get("title") or first.get("name") or ""
                summary = first.get("description") or ""
                source_url = first.get("url") or first.get("html_url") or ""
            elif isinstance(res.data, str):
                summary = res.data[:500]
            ev_type, ch_enum = ch_type_map.get(ch_name, (EvidenceType.WEB_SEARCH, ChannelType.WEB))
            item = EvidenceItem(
                company_name=body.company_name,
                evidence_type=ev_type,
                channel=ch_enum,
                source_url=source_url,
                title=title,
                summary=summary,
                raw_data=res.data,
                confidence=0.8 if ch_name == "github" else 0.5,
                metadata={"channel": ch_name, "action": "research"},
            )
            persisted = await _pg_store.save_evidence(tenant_id, item)
            item.id = persisted.evidence_id
            evidence_items.append(item)
            if persisted.inserted:
                stored += 1

    signals_stored = 0
    for signal in classify_signals_from_evidence(evidence_items):
        if await _pg_store.add_signal(tenant_id, signal):
            signals_stored += 1

    return {
        "success": True,
        "company": body.company_name,
        "evidence_stored": stored,
        "signals_stored": signals_stored,
        "channels": {
            ch: {
                "success": r.success,
                "data": r.data,
                "error": r.error,
                "metadata": r.metadata,
            }
            for ch, r in results.items()
        },
    }


# ── Generic Execute (allowlisted only) ───────────────────────────


@router.post("/execute", summary="Execute generic request", description="Execute a generic Agent Reach request. Allowed channels and actions are validated server-side.")
async def execute_generic(
    body: GenericRequest,
    _tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.CREATE)),
):
    """Execute a generic Agent Reach request (allowlisted operations only).

    Allowed channels: web, twitter, youtube, github, rss, bilibili, web_search, linkedin
    Allowed actions per channel are validated server-side.
    """
    svc = AgentReachService()
    try:
        channel = ChannelType(body.channel)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {body.channel}")

    from .models import AgentReachRequest

    request = AgentReachRequest(
        channel=channel,
        action=body.action,
        query=body.query,
        url=body.url,
        max_results=body.max_results,
    )
    try:
        result = await svc.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "data": result.data, "metadata": result.metadata}


# ── Evidence / Signals Storage (Postgres-backed) ─────────────────


@router.get("/evidence/{company_name}", summary="Get company evidence", description="Get all stored evidence for a company (RLS-scoped).")
async def get_evidence(
    company_name: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.READ)),
):
    """Get all stored evidence for a company (RLS-scoped)."""
    items = await _pg_store.get_evidence(tenant_id, company_name)
    return {
        "company": company_name,
        "count": len(items),
        "evidence": [item.to_dict() for item in items],
    }


@router.get("/signals/{company_name}", summary="Get company signals", description="Get all stored signals for a company (RLS-scoped).")
async def get_signals(
    company_name: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.READ)),
):
    """Get all stored signals for a company (RLS-scoped)."""
    sigs = await _pg_store.get_signals(tenant_id, company_name)
    return {
        "company": company_name,
        "count": len(sigs),
        "signals": [s.to_dict() for s in sigs],
    }


@router.get("/intel/{company_name}", summary="Get company intelligence summary", description="Get aggregated intelligence summary for a company with evidence and signals.")
async def get_intel_summary(
    company_name: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.READ)),
):
    """Get aggregated intelligence summary for a company (RLS-scoped)."""
    summary = await _pg_store.get_summary(tenant_id, company_name)
    return {
        "company": summary.company_name,
        "evidence_count": summary.evidence_count,
        "signal_count": summary.signal_count,
        "channels_searched": summary.channels_searched,
        "last_researched": summary.last_researched.isoformat() if summary.last_researched else None,
        "evidence": [e.to_dict() for e in summary.evidence],
        "signals": [s.to_dict() for s in summary.signals],
    }


@router.get("/intel", summary="List companies with intelligence", description="List all companies with stored intelligence (RLS-scoped).")
async def list_intel_companies(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.READ)),
):
    """List all companies with stored intelligence (RLS-scoped)."""
    companies = await _pg_store.list_companies(tenant_id)
    return {"count": len(companies), "companies": companies}


@router.delete("/intel/{company_name}", summary="Clear company intelligence", description="Clear all evidence and signals for a company (RLS-scoped).")
async def clear_intel(
    company_name: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.DELETE)),
):
    """Clear all evidence/signals for a company (RLS-scoped)."""
    removed = await _pg_store.clear(tenant_id, company_name)
    return {"company": company_name, "removed": removed}


@router.post("/intel/prune", summary="Prune expired intelligence", description="Prune expired evidence and signals based on TTL (time-to-live) cleanup.")
async def prune_expired(
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("agent_reach", PermissionAction.DELETE)),
):
    """Prune expired evidence and signals (TTL cleanup)."""
    ev = await _pg_store.prune_expired(tenant_id)
    sig = await _pg_store.prune_expired_signals(tenant_id)
    return {"evidence_pruned": ev, "signals_pruned": sig}
