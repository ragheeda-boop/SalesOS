from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class ProposalAgent(BaseAgent):
    """Generates business proposals based on company research and pricing."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("proposal", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")
        goal = task.input.get("goal", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت كاتب مقترحات تجارية محترف.",
                messages=[{"role": "user", "content": f"اكتب مقترحاً تجارياً لـ {company_name or company_id}. الهدف: {goal}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="proposal",
                output={"proposal": response.content, "status": "draft"},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="proposal",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لإنشاء المقترح."},
            confidence=0.2,
        )
