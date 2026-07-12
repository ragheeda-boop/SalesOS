from __future__ import annotations

from typing import Any, Protocol

from .schemas import AgentAnalysis, EvidenceItem
from .agents.llm import LLMResponse


class LLMBackend(Protocol):
    async def chat(
        self,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        ...


class ReasoningPipeline:
    def __init__(self, llm: LLMBackend):
        self._llm = llm

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        system = (
            "أنت محلل بيانات خبير. قم بتحليل البيانات المتاحة واستخرج "
            "المعلومات الرئيسية والحقائق والأنماط منها."
        )
        user = (
            "قم بتحليل البيانات التالية واستخرج:\n"
            "1. المعلومات الرئيسية\n"
            "2. الحقائق المؤكدة\n"
            "3. الأنماط الملحوظة\n"
            "4. الفجوات في البيانات\n\n"
            f"البيانات:\n{self._format_data(data)}"
        )
        response = await self._llm.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=0.2,
        )
        return {"analysis": response.content, "usage": response.usage}

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        analysis = context.get("analysis", "")
        data = context.get("raw_data", {})
        system = (
            "أنت خبير تفكير تحليلي. بناءً على التحليل الأولي، قم بالاستدلال "
            "خطوة بخطوة للوصول إلى استنتاجات منطقية."
        )
        user = (
            "التحليل الأولي:\n"
            f"{analysis}\n\n"
            "المطلوب:\n"
            "1. قم بالاستدلال خطوة بخطوة\n"
            "2. اربط النتائج بالبيانات الأصلية\n"
            "3. حدد الثقة في كل استنتاج\n"
            "4. استخرج الأدلة الداعمة\n\n"
            f"البيانات الأصلية:\n{self._format_data(data)}"
        )
        response = await self._llm.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=0.3,
        )
        return {"reasoning": response.content, "usage": response.usage}

    async def conclude(self, reasoning: dict[str, Any]) -> AgentAnalysis:
        reasoning_text = reasoning.get("reasoning", "")
        system = (
            "أنت خبير في صياغة الاستنتاجات النهائية. بناءً على التحليل والاستدلال، "
            "قدم استنتاجاً شاملاً مع الأدلة ومستوى الثقة."
        )
        user = (
            "بناءً على الاستدلال التالي، قدم استنتاجاً نهائياً:\n\n"
            f"{reasoning_text}\n\n"
            "يجب أن يتضمن:\n"
            "1. الاستنتاج النهائي\n"
            "2. الأدلة المستخدمة مع مصادرها\n"
            "3. مستوى الثقة (0-1)\n"
            "4. قائمة المصادر"
        )
        response = await self._llm.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=0.2,
        )
        return AgentAnalysis(
            analysis=response.content,
            confidence=0.8,
            evidence=[EvidenceItem(fact=response.content, source="reasoning", confidence=0.8)],
            sources=["llm_reasoning"],
        )

    async def full_pipeline(self, data: dict[str, Any]) -> AgentAnalysis:
        analysis = await self.analyze({"raw_data": data, **data})
        reasoning = await self.reason({"raw_data": data, "analysis": analysis.get("analysis", "")})
        return await self.conclude(reasoning)

    def _format_data(self, data: dict[str, Any]) -> str:
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"{key}: [{len(value)} items]")
                if value and isinstance(value[0], dict):
                    for i, item in enumerate(value[:5]):
                        lines.append(f"  [{i}]: {item}")
                elif value:
                    lines.append(f"  {', '.join(str(v) for v in value[:5])}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
