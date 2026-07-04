from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


class ForecastAgent(BaseAgent):
    """Generates revenue forecasts based on signals, pipeline, and market data."""

    def __init__(self, llm: LLMService | None = None):
        super().__init__("forecast", "2.0")
        self._llm = llm

    async def _run(self, task: AgentTask) -> AgentResult:
        context = task.input
        pipeline_value = context.get("pipeline_value", 0)
        win_rate = context.get("win_rate", 0)
        avg_deal_size = context.get("avg_deal_size", 0)

        if self._llm and self._llm.client:
            response = await self._llm.chat(
                system="أنت محلل مالي. قدم توقعات إيرادات بناءً على البيانات.",
                messages=[{"role": "user", "content": f"حلل التوقعات: قيمة الأنابيب={pipeline_value}, معدل الفوز={win_rate}, متوسط الصفقة={avg_deal_size}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="forecast",
                output={"analysis": response.content},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="forecast",
            output={"message": "يتطلب بيانات الأنابيب ومفتاح OpenAI للتوقعات."},
            confidence=0.2,
        )
