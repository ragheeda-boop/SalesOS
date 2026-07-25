"""Decision Center repository — abstract + in-memory implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .models import (
    Decision,
    DecisionAudit,
    DecisionFeedback,
    DecisionTemplate,
    FeedbackAggregate,
    FeedbackRating,
)


class DecisionCenterRepository(ABC):
    @abstractmethod
    async def save_decision(self, decision: Decision) -> Decision: ...

    @abstractmethod
    async def get_decision(self, decision_id: str, tenant_id: str) -> Optional[Decision]: ...

    @abstractmethod
    async def list_decisions(
        self,
        tenant_id: str,
        domain: Optional[str] = None,
        decision_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        confidence_min: Optional[float] = None,
        confidence_max: Optional[float] = None,
        entity_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Decision], int]: ...

    @abstractmethod
    async def save_audit(self, audit: DecisionAudit) -> DecisionAudit: ...

    @abstractmethod
    async def get_audit(self, decision_id: str, tenant_id: str) -> Optional[DecisionAudit]: ...

    @abstractmethod
    async def save_feedback(self, feedback: DecisionFeedback) -> DecisionFeedback: ...

    @abstractmethod
    async def get_feedback_for_decision(
        self, decision_id: str, tenant_id: str
    ) -> list[DecisionFeedback]: ...

    @abstractmethod
    async def get_feedback_by_type(self, tenant_id: str) -> list[FeedbackAggregate]: ...

    @abstractmethod
    async def save_template(self, template: "DecisionTemplate") -> "DecisionTemplate": ...

    @abstractmethod
    async def get_template(self, template_id: str, tenant_id: str = "") -> Optional["DecisionTemplate"]: ...

    @abstractmethod
    async def list_templates(self, template_type: Optional[str] = None, tenant_id: str = "") -> list["DecisionTemplate"]: ...

    @abstractmethod
    async def delete_template(self, template_id: str, tenant_id: str = "") -> bool: ...

    @abstractmethod
    async def update_template(
        self, template_id: str, updates: dict, tenant_id: str = ""
    ) -> Optional["DecisionTemplate"]: ...


class InMemoryDecisionCenterRepository(DecisionCenterRepository):
    def __init__(self) -> None:
        self._decisions: dict[str, Decision] = {}
        self._decisions_by_tenant: dict[str, list[str]] = {}
        self._audits: dict[str, DecisionAudit] = {}
        self._feedbacks: dict[str, DecisionFeedback] = {}
        self._feedback_by_decision: dict[str, list[str]] = {}
        self._templates: dict[str, DecisionTemplate] = {}

    async def save_decision(self, decision: Decision) -> Decision:
        self._decisions[decision.id] = decision
        self._decisions_by_tenant.setdefault(decision.metadata.get("tenant_id", ""), []).append(
            decision.id
        )
        return decision

    async def get_decision(self, decision_id: str, tenant_id: str) -> Optional[Decision]:
        decision = self._decisions.get(decision_id)
        if not decision:
            return None
        if (decision.metadata or {}).get("tenant_id") != tenant_id:
            return None
        return decision

    async def list_decisions(
        self,
        tenant_id: str,
        domain: Optional[str] = None,
        decision_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        confidence_min: Optional[float] = None,
        confidence_max: Optional[float] = None,
        entity_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Decision], int]:
        ids = self._decisions_by_tenant.get(tenant_id, [])
        candidates = [self._decisions[did] for did in ids if did in self._decisions]

        if domain:
            candidates = [d for d in candidates if d.domain.value == domain]
        if decision_type:
            candidates = [d for d in candidates if d.type.value == decision_type]
        if entity_id:
            candidates = [d for d in candidates if d.entity_id == entity_id]
        if status:
            candidates = [d for d in candidates if d.status.value == status]
        if confidence_min is not None:
            candidates = [d for d in candidates if d.confidence >= confidence_min]
        if confidence_max is not None:
            candidates = [d for d in candidates if d.confidence <= confidence_max]
        if date_from:
            from datetime import datetime as _dt

            try:
                dt_from = _dt.fromisoformat(date_from)
                candidates = [d for d in candidates if d.timestamp >= dt_from]
            except ValueError:
                pass
        if date_to:
            from datetime import datetime as _dt

            try:
                dt_to = _dt.fromisoformat(date_to)
                candidates = [d for d in candidates if d.timestamp <= dt_to]
            except ValueError:
                pass

        candidates.sort(key=lambda d: d.timestamp, reverse=True)
        total = len(candidates)
        return candidates[offset : offset + limit], total

    async def save_audit(self, audit: DecisionAudit) -> DecisionAudit:
        self._audits[audit.decision_id] = audit
        return audit

    async def get_audit(self, decision_id: str, tenant_id: str) -> Optional[DecisionAudit]:
        if await self.get_decision(decision_id, tenant_id) is None:
            return None
        return self._audits.get(decision_id)

    async def save_feedback(self, feedback: DecisionFeedback) -> DecisionFeedback:
        self._feedbacks[feedback.id] = feedback
        self._feedback_by_decision.setdefault(feedback.decision_id, []).append(feedback.id)
        return feedback

    async def get_feedback_for_decision(
        self, decision_id: str, tenant_id: str
    ) -> list[DecisionFeedback]:
        if await self.get_decision(decision_id, tenant_id) is None:
            return []
        fb_ids = self._feedback_by_decision.get(decision_id, [])
        return [self._feedbacks[fid] for fid in fb_ids if fid in self._feedbacks]

    async def get_feedback_by_type(self, tenant_id: str) -> list[FeedbackAggregate]:
        from collections import defaultdict

        type_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"up": 0, "down": 0})
        ids = self._decisions_by_tenant.get(tenant_id, [])

        for did in ids:
            decision = self._decisions.get(did)
            if not decision:
                continue
            fb_ids = self._feedback_by_decision.get(did, [])
            for fid in fb_ids:
                fb = self._feedbacks.get(fid)
                if fb:
                    type_counts[decision.type.value][fb.rating.value] += 1

        results = []
        for dt, counts in type_counts.items():
            total = counts["up"] + counts["down"]
            results.append(
                FeedbackAggregate(
                    decision_type=dt,
                    total_feedback=total,
                    up_count=counts["up"],
                    down_count=counts["down"],
                    approval_rate=counts["up"] / total if total > 0 else 0.0,
                )
            )
        return results

    async def save_template(self, template: DecisionTemplate) -> DecisionTemplate:
        self._templates[template.id] = template
        return template

    async def get_template(self, template_id: str, tenant_id: str = "") -> Optional[DecisionTemplate]:
        template = self._templates.get(template_id)
        if not template:
            return None
        if template.tenant_id and template.tenant_id != tenant_id:
            return None
        return template

    async def list_templates(self, template_type: Optional[str] = None, tenant_id: str = "") -> list[DecisionTemplate]:
        all_templates = list(self._templates.values())
        all_templates = [t for t in all_templates if not t.tenant_id or t.tenant_id == tenant_id]
        if template_type:
            all_templates = [t for t in all_templates if t.type.value == template_type]
        return sorted(all_templates, key=lambda t: t.created_at, reverse=True)

    async def delete_template(self, template_id: str, tenant_id: str = "") -> bool:
        template = self._templates.get(template_id)
        if not template:
            return False
        if template.tenant_id and template.tenant_id != tenant_id:
            return False
        return self._templates.pop(template_id, None) is not None

    async def update_template(
        self, template_id: str, updates: dict, tenant_id: str = ""
    ) -> Optional[DecisionTemplate]:
        template = self._templates.get(template_id)
        if not template:
            return None
        if template.tenant_id and template.tenant_id != tenant_id:
            return None
        if "name" in updates:
            template.name = updates["name"]
        if "config" in updates:
            template.config = updates["config"]
        return template
