from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from .base import BaseAgent, AgentTask, AgentResult


@dataclass
class WorkflowPlan:
    id: str
    goal: str
    steps: list[dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.utcnow)


class AgentCoordinator(BaseAgent):
    """
    The coordinator agent - receives requests and distributes to specialized agents.
    AI Assistant doesn't execute. It coordinates.
    """

    def __init__(self, agents: Optional[dict[str, BaseAgent]] = None):
        super().__init__("coordinator", "2.0")
        self._agents: dict[str, BaseAgent] = agents or {}

    def register_agent(self, agent: BaseAgent):
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    async def _run(self, task: AgentTask) -> AgentResult:
        goal = task.input.get("goal", "")
        context = task.input.get("context", {})

        plan = self._create_plan(goal, context)

        step_results = []
        for step in plan.steps:
            agent = self._agents.get(step["agent"])
            if not agent:
                step_results.append({"step": step["name"], "error": f"Agent {step['agent']} not found"})
                continue

            subtask = AgentTask(
                id=f"{task.id}_{step['name']}",
                agent_type=step["agent"],
                input={**step["input"], **context},
                priority=step.get("priority", 0),
                context=context,
            )
            result = await agent.execute(subtask)
            step_results.append({
                "step": step["name"],
                "agent": step["agent"],
                "success": result.success,
                "output": result.output,
                "confidence": result.confidence,
            })

        return AgentResult(
            task_id=task.id,
            agent_type="coordinator",
            success=all(r["success"] for r in step_results),
            output={
                "goal": goal,
                "plan_id": plan.id,
                "steps": len(plan.steps),
                "results": step_results,
                "summary": self._summarize(step_results),
            },
            confidence=min(
                sum(r.get("confidence", 0) for r in step_results if r.get("success")) / max(len(step_results), 1) + 0.1,
                1.0
            ),
        )

    def _create_plan(self, goal: str, context: dict[str, Any]) -> WorkflowPlan:
        """Generate execution plan based on goal."""
        goal_lower = goal.lower()
        steps = []

        if "meeting" in goal_lower or "prepare" in goal_lower or "اجتماع" in goal:
            steps.append({"name": "research", "agent": "research", "input": {"company_id": context.get("company_id")}, "priority": 1})
            steps.append({"name": "meeting", "agent": "meeting", "input": {"company_id": context.get("company_id"), "goal": goal}, "priority": 2})
            steps.append({"name": "relationship", "agent": "relationship", "input": {"company_id": context.get("company_id")}, "priority": 3})

        elif "proposal" in goal_lower or "عرض" in goal:
            steps.append({"name": "research", "agent": "research", "input": {"company_id": context.get("company_id")}, "priority": 1})
            steps.append({"name": "pricing", "agent": "pricing", "input": {"company_id": context.get("company_id")}, "priority": 2})
            steps.append({"name": "proposal", "agent": "proposal", "input": {"company_id": context.get("company_id"), "goal": goal}, "priority": 3})

        elif "contract" in goal_lower or "عقد" in goal:
            steps.append({"name": "contract", "agent": "contract", "input": {"company_id": context.get("company_id")}, "priority": 1})
            steps.append({"name": "competitor", "agent": "competitor", "input": {"company_id": context.get("company_id")}, "priority": 2})

        elif "forecast" in goal_lower or "توقع" in goal or "توقعات" in goal:
            steps.append({"name": "forecast", "agent": "forecast", "input": context, "priority": 1})

        elif "competitor" in goal_lower or "منافس" in goal:
            steps.append({"name": "competitor", "agent": "competitor", "input": {"company_id": context.get("company_id")}, "priority": 1})
            steps.append({"name": "research", "agent": "research", "input": {"company_id": context.get("company_id")}, "priority": 2})

        elif "renew" in goal_lower or "تجديد" in goal:
            steps.append({"name": "renewal", "agent": "renewal", "input": {"company_id": context.get("company_id")}, "priority": 1})
            steps.append({"name": "pricing", "agent": "pricing", "input": {"company_id": context.get("company_id")}, "priority": 2})

        elif "tender" in goal_lower or "مناقصة" in goal:
            steps.append({"name": "tender", "agent": "tender", "input": {"company_id": context.get("company_id")}, "priority": 1})
            steps.append({"name": "competitor", "agent": "competitor", "input": {"company_id": context.get("company_id")}, "priority": 2})

        elif "news" in goal_lower or "أخبار" in goal:
            steps.append({"name": "news", "agent": "news", "input": {"company_id": context.get("company_id")}, "priority": 1})

        else:
            steps.append({"name": "research", "agent": "research", "input": {"company_id": context.get("company_id"), "topic": goal}, "priority": 1})
            steps.append({"name": "competitor", "agent": "competitor", "input": {"company_id": context.get("company_id")}, "priority": 2})
            steps.append({"name": "relationship", "agent": "relationship", "input": {"company_id": context.get("company_id")}, "priority": 3})

        return WorkflowPlan(
            id=f"plan_{int(datetime.utcnow().timestamp())}",
            goal=goal,
            steps=steps,
        )

    def _summarize(self, results: list[dict[str, Any]]) -> str:
        success = sum(1 for r in results if r.get("success"))
        total = len(results)
        if success == total:
            return f"تم تنفيذ جميع الخطوات بنجاح ({success}/{total})"
        return f"تم تنفيذ {success} من {total} خطوة"

    def get_all_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())
