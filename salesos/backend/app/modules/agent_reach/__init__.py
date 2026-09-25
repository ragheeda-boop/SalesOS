"""Agent Reach Integration — SalesOS ↔ Agent Reach bridge.

Provides async wrappers around Agent Reach CLI channels for:
- Web page reading (Jina Reader)
- Twitter/X search & reading
- YouTube subtitles & search
- GitHub repo reading & search
- RSS feed reading
- Bilibili search & reading
- Web semantic search (Exa)
- LinkedIn company/profile/jobs (via Jina)
- Evidence + Signals persistent storage (Postgres + RLS)

Usage:
    from app.modules.agent_reach import AgentReachService, PostgresEvidenceStore
    svc = AgentReachService()
    results = await svc.research_company("Microsoft")
    store = PostgresEvidenceStore(async_session)
    summary = await store.get_summary(tenant_id, "Microsoft")
"""

from .service import AgentReachService, evidence_store, EvidenceStore
from .persistence import PostgresEvidenceStore
from .models import (
    AgentReachRequest,
    AgentReachResult,
    ChannelType,
    ChannelStatus,
    EvidenceItem,
    EvidenceType,
    Signal,
    SignalConfidence,
    SignalType,
    CompanyIntelSummary,
)

__all__ = [
    "AgentReachService",
    "AgentReachRequest",
    "AgentReachResult",
    "ChannelType",
    "ChannelStatus",
    "EvidenceItem",
    "EvidenceType",
    "EvidenceStore",
    "PostgresEvidenceStore",
    "Signal",
    "SignalConfidence",
    "SignalType",
    "CompanyIntelSummary",
    "evidence_store",
]
