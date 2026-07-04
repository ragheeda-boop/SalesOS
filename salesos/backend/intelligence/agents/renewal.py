from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class RenewalAgent(BaseAgent):
    """Manages customer renewals, identifies at-risk accounts, and suggests retention."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("renewal", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت مدير نجاح عملاء. حلل مخاطر التجديد وقدم استراتيجيات الاحتفاظ.",
                messages=[{"role": "user", "content": f"حلل مخاطر تجديد العقد لـ {company_name or company_id}."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="renewal",
                output={"analysis": response.content},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="renewal",
            output={"message": "يتطلب تكوين مفتاح OpenAI لتحليل التجديد."},
            confidence=0.2,
        )
