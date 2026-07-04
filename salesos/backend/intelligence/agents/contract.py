from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class ContractAgent(BaseAgent):
    """Reviews, analyzes, and manages contracts."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("contract", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت مستشار قانوني متخصص في العقود التجارية.",
                messages=[{"role": "user", "content": f"حلل معلومات العقود للشركة {company_id} وقدم توصيات."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="contract",
                output={"analysis": response.content},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="contract",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لتحليل العقود."},
            confidence=0.2,
        )
