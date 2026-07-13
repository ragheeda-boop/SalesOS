"""Grounded base agent — retrieve-then-generate pattern for all AI agents."""

import json
from typing import Any, Optional
from datetime import datetime

from .agents.base import BaseAgent, AgentTask, AgentResult, AgentStatus
from .agents.llm import LLMService
from .grounding import AgentContext, GroundingService
from .guardrails import add_input_moderation, extract_json_from_llm_output, sanitize_input, validate_output
from .schemas import AgentAnalysis


class GroundedBaseAgent(BaseAgent):
    """Base agent with built-in data grounding and output schema validation.

    Subclasses must implement _agent_type(), _system_prompt(), and _output_schema().
    """

    def __init__(self, name: str, version: str, llm: Optional[LLMService] = None,
                 grounding: Optional[GroundingService] = None):
        super().__init__(name, version)
        self._llm = llm
        self._grounding = grounding

    def _agent_type(self) -> str:
        return self.name

    def _system_prompt(self, context: AgentContext) -> str:
        raise NotImplementedError

    def _user_prompt(self, task: AgentTask, context: AgentContext) -> str:
        raise NotImplementedError

    def _output_schema(self) -> dict[str, Any]:
        return {"analysis": str, "confidence": float, "evidence": list, "sources": list}

    async def execute_grounded(self, task: AgentTask) -> AgentResult:
        self.status = AgentStatus.RUNNING
        task.assigned_at = datetime.utcnow()
        started = datetime.utcnow()

        try:
            company_id = task.input.get("company_id", "unknown")
            context = AgentContext()
            if self._grounding:
                context = await self._grounding.get_context(company_id, self._agent_type())

            system = self._system_prompt(context)
            user = self._user_prompt(task, context)

            if self._llm and self._llm.client:
                user = sanitize_input(user)
                if add_input_moderation(user):
                    result = AgentResult(
                        task_id=task.id,
                        agent_type=self._agent_type(),
                        success=False,
                        output={"error": "Input rejected by content moderation"},
                        confidence=0.0,
                    )
                    self.status = AgentStatus.COMPLETED
                    self._task_history.append(result)
                    return result

                schema_guide = ""
                if self._output_schema():
                    schema_guide = (
                        "\n\nيجب أن يكون الرد بصيغة JSON فقط:\n"
                        f"{json.dumps(self._output_schema(), ensure_ascii=False, indent=2)}"
                    )

                response = await self._llm.chat(
                    system=system + schema_guide,
                    messages=[{"role": "user", "content": user}],
                )

                raw = response.content
                parsed = extract_json_from_llm_output(raw)

                if parsed and validate_output(raw, self._output_schema()):
                    result = AgentResult(
                        task_id=task.id,
                        agent_type=self._agent_type(),
                        success=True,
                        output=parsed,
                        confidence=parsed.get("confidence", 0.5),
                    )
                else:
                    evidence_count = 0
                    if context and not context.is_empty():
                        evidence_count = (
                            len(context.contacts) +
                            len(context.opportunities) +
                            len(context.signals)
                        )
                    fallback_confidence = min(0.3 + evidence_count * 0.05, 0.7)
                    result = AgentResult(
                        task_id=task.id,
                        agent_type=self._agent_type(),
                        success=True,
                        output={"analysis": raw, "sources": [], "evidence": []},
                        confidence=fallback_confidence,
                    )
            else:
                result = AgentResult(
                    task_id=task.id,
                    agent_type=self._agent_type(),
                    success=True,
                    output={
                        "analysis": f"التحليل غير متاح — يتطلب تكوين مفتاح OpenAI.",
                        "confidence": 0.1,
                        "evidence": [],
                        "sources": [],
                    },
                    confidence=0.1,
                )

            result.started_at = started
            result.completed_at = datetime.utcnow()
            result.duration_ms = (result.completed_at - started).total_seconds() * 1000
            self.status = AgentStatus.COMPLETED

        except Exception as e:
            result = AgentResult(
                task_id=task.id,
                agent_type=self._agent_type(),
                success=False,
                error=str(e),
                started_at=started,
                completed_at=datetime.utcnow(),
            )
            self.status = AgentStatus.FAILED

        self._task_history.append(result)
        return result

    async def _run(self, task: AgentTask) -> AgentResult:
        return await self.execute_grounded(task)
