from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class ResearchAgent(BaseAgent):
    """Researches companies, markets, and topics using LLM."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("research", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")
        cr_number = task.input.get("cr_number", "")
        city = task.input.get("city", "")
        topic = task.input.get("topic", "")

        system_prompt = "أنت باحث مبيعات في السعودية. قدم معلومات دقيقة ومفيدة عن الشركات."
        user_prompt = f"""الرجاء البحث عن معلومات عن الشركة التالية:
- الاسم: {company_name}
- السجل التجاري: {cr_number}
- المدينة: {city}
- الموضوع: {topic or 'عام'}

قدم باللغة العربية:
1. معلومات أساسية (النشاط، الحجم المتوقع، السوق)
2. فرص بيع محتملة
3. توصيات للتواصل"""

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.7,
                max_tokens=2048,
            )
            return AgentResult(
                task_id=task.id, agent_type="research",
                output={"summary": response.content, "sources": [], "research_depth": "llm"},
                confidence=0.7,
            )

        # Fallback if no LLM available
        return AgentResult(
            task_id=task.id, agent_type="research",
            output={
                "company_id": company_id,
                "summary": f"معلومات عن {company_name or company_id} — يتطلب تكوين مفتاح OpenAI لتوليد تحليل كامل.",
                "research_depth": "minimal",
            },
            confidence=0.3,
        )
