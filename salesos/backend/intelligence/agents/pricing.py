from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class PricingAgent(BaseAgent):
    """Analyzes pricing strategies and market positioning."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("pricing", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت محلل تسعير استراتيجي.",
                messages=[{"role": "user", "content": f"حلل استراتيجية التسعير المثلى لـ {company_name or company_id}."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="pricing",
                output={"analysis": response.content},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="pricing",
            output={"message": "يتطلب تكوين مفتاح OpenAI لتحليل التسعير."},
            confidence=0.2,
        )
