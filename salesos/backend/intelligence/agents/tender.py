from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class TenderAgent(BaseAgent):
    """Monitors and analyzes government and private sector tenders."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("tender", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")
        industry = task.input.get("industry", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت مستشار مناقصات حكومية.",
                messages=[{"role": "user", "content": f"ابحث عن فرص المناقصات المناسبة لـ {company_name or company_id} في قطاع {industry}."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="tender",
                output={"analysis": response.content},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="tender",
            output={"message": "يتطلب تكوين مفتاح OpenAI ومصدر مناقصات حكومية."},
            confidence=0.2,
        )
