from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConditionOperator(str, Enum):
    equals = "equals"
    not_equals = "not_equals"
    greater_than = "greater_than"
    less_than = "less_than"
    contains = "contains"
    in_ = "in"
    not_in = "not_in"


class ConditionGroupType(str, Enum):
    and_ = "and"
    or_ = "or"
    not_ = "not"


class ActionType(str, Enum):
    update_field = "update_field"
    send_notification = "send_notification"
    trigger_workflow = "trigger_workflow"
    create_task = "create_task"
    score_adjustment = "score_adjustment"
    flag_company = "flag_company"
    assign_owner = "assign_owner"


DomainType = Literal["company", "opportunity", "scoring", "workflow"]


class Condition(BaseModel):
    field: str
    operator: ConditionOperator
    value: Any


class ConditionGroup(BaseModel):
    type: ConditionGroupType = ConditionGroupType.and_
    conditions: list[Condition | ConditionGroup] = Field(default_factory=list)


class Action(BaseModel):
    type: ActionType
    params: dict[str, Any] = Field(default_factory=dict)


class Rule(BaseModel):
    id: str
    name: str
    description: str = ""
    enabled: bool = True
    domain: DomainType = "company"
    conditions: ConditionGroup = Field(
        default_factory=lambda: ConditionGroup(type=ConditionGroupType.and_)
    )
    actions: list[Action] = Field(default_factory=list)
    priority: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class RuleEvaluationContext(BaseModel):
    entity_id: str
    entity_type: DomainType = "company"
    data: dict[str, Any] = Field(default_factory=dict)


class RuleEvaluationResult(BaseModel):
    rule_id: str
    rule_name: str
    matched: bool
    actions_executed: list[dict[str, Any]] = Field(default_factory=list)


class BatchEvaluationResult(BaseModel):
    results: list[RuleEvaluationResult]
    total_rules: int
    matched_count: int
    execution_time_ms: float
