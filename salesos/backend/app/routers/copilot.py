"""AI Copilot — coordinates agents to answer user queries."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.config import settings
from app.dependencies import get_current_tenant_id, get_current_user_id
from intelligence.agents import AgentCoordinator, AgentTask
from intelligence.agents.llm import LLMService
from intelligence.agents.research import ResearchAgent
from intelligence.agents.meeting import MeetingAgent
from intelligence.agents.proposal import ProposalAgent
from intelligence.agents.contract import ContractAgent
from intelligence.agents.pricing import PricingAgent
from intelligence.agents.forecast import ForecastAgent
from intelligence.agents.renewal import RenewalAgent
from intelligence.agents.competitor import CompetitorAgent
from intelligence.agents.tender import TenderAgent
from intelligence.agents.news import NewsAgent
from intelligence.agents.relationship import RelationshipAgent
from sdk.telemetry import StructuredLogger

router = APIRouter()


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


def _build_coordinator() -> AgentCoordinator:
    llm = None
    if settings.openai_api_key:
        llm = LLMService(api_key=settings.openai_api_key, model=settings.openai_model)

    coordinator = AgentCoordinator()
    coordinator.register_agent(ResearchAgent(llm))
    coordinator.register_agent(NewsAgent(llm))
    coordinator.register_agent(CompetitorAgent(llm))
    coordinator.register_agent(ForecastAgent(llm))
    coordinator.register_agent(MeetingAgent(llm))
    coordinator.register_agent(ProposalAgent(llm))
    coordinator.register_agent(ContractAgent(llm))
    coordinator.register_agent(PricingAgent(llm))
    coordinator.register_agent(RenewalAgent(llm))
    coordinator.register_agent(TenderAgent(llm))
    coordinator.register_agent(RelationshipAgent(llm))
    return coordinator


@router.post("/copilot/query", response_model=CopilotResponse)
async def copilot_query(
    body: CopilotQuery,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
):
    logger: StructuredLogger = getattr(request.app.state, "logger", None)

    context = {
        "company_id": body.company_id,
        "company_name": body.company_name,
        "cr_number": body.cr_number,
        "city": body.city,
        "industry": body.industry,
    }

    coordinator = _build_coordinator()
    task = AgentTask(
        id=f"copilot_{user_id}_{int(__import__('time').time())}",
        agent_type="coordinator",
        input={"goal": body.goal or body.query, "context": {**context, "tenant_id": tenant_id}},
    )

    result = await coordinator.execute(task)

    # Extract text response
    steps = result.output.get("results", [])
    texts = []
    for step in steps:
        out = step.get("output", {})
        text = out.get("summary") or out.get("analysis") or out.get("proposal") or out.get("preparation") or out.get("message") or ""
        if text:
            texts.append(text)

    response_text = "\n\n".join(texts) if texts else "لم يتم العثور على معلومات كافية."
    if not settings.openai_api_key:
        response_text = "⚠️ لم يتم تكوين مفتاح OpenAI. يرجى ضبط `OPENAI_API_KEY` في الإعدادات لتفعيل المساعد الذكي."

    if logger:
        logger.info("Copilot query: user=%s goal=%s confidence=%.2f", user_id, body.goal or body.query[:50], result.confidence)

    return CopilotResponse(
        response=response_text,
        confidence=result.confidence,
        agent_used="coordinator",
        sources=[],
    )
