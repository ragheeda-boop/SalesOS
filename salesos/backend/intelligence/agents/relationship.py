from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class RelationshipAgent(BaseAgent):
    """Maps and analyzes business relationships, finds decision makers."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("relationship", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت محلل علاقات أعمال. حدد صناع القرار وشبكة العلاقات.",
                messages=[{"role": "user", "content": f"حلل شبكة العلاقات وصناع القرار في {company_name or company_id}."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="relationship",
                output={"analysis": response.content},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="relationship",
            output={"message": "يتطلب تكوين مفتاح OpenAI ومصادر بيانات التواصل."},
            confidence=0.2,
        )
