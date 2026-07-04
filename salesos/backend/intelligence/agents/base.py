from enum import Enum
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class AgentTask:
    id: str
    agent_type: str
    input: dict[str, Any]
    priority: int = 0
    assigned_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    task_id: str
    agent_type: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    confidence: float = 0.5
    duration_ms: float = 0.0


class BaseAgent:
    """Base class for all specialized agents."""

    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.status = AgentStatus.IDLE
        self._task_history: list[AgentResult] = []

    async def execute(self, task: AgentTask) -> AgentResult:
        self.status = AgentStatus.RUNNING
        task.assigned_at = datetime.utcnow()
        started = datetime.utcnow()

        try:
            result = await self._run(task)
            result.started_at = started
            result.completed_at = datetime.utcnow()
            result.duration_ms = (result.completed_at - started).total_seconds() * 1000
            result.success = True
            self.status = AgentStatus.COMPLETED
        except Exception as e:
            result = AgentResult(
                task_id=task.id,
                agent_type=self.name,
                success=False,
                error=str(e),
                started_at=started,
                completed_at=datetime.utcnow(),
            )
            self.status = AgentStatus.FAILED

        self._task_history.append(result)
        return result

    async def _run(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError

    def get_history(self) -> list[AgentResult]:
        return self._task_history

    def get_stats(self) -> dict[str, Any]:
        total = len(self._task_history)
        successful = sum(1 for r in self._task_history if r.success)
        avg_confidence = sum(r.confidence for r in self._task_history if r.success) / max(successful, 1)
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "total_tasks": total,
            "successful": successful,
            "failed": total - successful,
            "avg_confidence": round(avg_confidence, 2),
            "avg_duration_ms": round(
                sum(r.duration_ms for r in self._task_history) / max(total, 1), 1
            ),
        }
