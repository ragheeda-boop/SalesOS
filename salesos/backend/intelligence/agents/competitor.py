from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class CompetitorAgent(BaseAgent):
    """Tracks competitor movements, positioning, and threats."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("competitor", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")
        industry = task.input.get("industry", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت محلل استراتيجي. حلل المشهد التنافسي.",
                messages=[{"role": "user", "content": f"حلل المشهد التنافسي للشركة: {company_name or company_id} في قطاع: {industry}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="competitor",
                output={"analysis": response.content, "competitors": []},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="competitor",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لتحليل المنافسين."},
            confidence=0.2,
        )
