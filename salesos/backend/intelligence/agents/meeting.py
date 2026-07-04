from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class MeetingAgent(BaseAgent):
    """Prepares for meetings with research, agenda, and talking points."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("meeting", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")
        goal = task.input.get("goal", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت مساعد تحضير اجتماعات مبيعات.",
                messages=[{"role": "user", "content": f"حضر لاجتماع مع {company_name or company_id}. الهدف: {goal}. قدم جدول أعمال ونقاط نقاش."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="meeting",
                output={"preparation": response.content},
                confidence=0.7,
            )

        return AgentResult(
            task_id=task.id, agent_type="meeting",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لتحضير الاجتماع."},
            confidence=0.2,
        )
