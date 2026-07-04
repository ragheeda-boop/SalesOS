from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class NewsAgent(BaseAgent):
    """Monitors news for companies, industries, and competitors."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("news", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت محلل أخبار تجاري. قدم ملخصاً للأخبار والتوجهات.",
                messages=[{"role": "user", "content": f"ابحث عن آخر الأخبار والتوجهات للشركة: {company_name or company_id}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="news",
                output={"summary": response.content, "articles": []},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="news",
            output={"company_id": company_id, "articles": [], "message": "يتطلب تكوين مفتاح OpenAI ومصدر أخبار."},
            confidence=0.2,
        )
