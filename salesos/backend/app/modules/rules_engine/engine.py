from __future__ import annotations

import time
from typing import Any

from app.modules.rules_engine.models import (
    Action,
    ActionType,
    BatchEvaluationResult,
    Condition,
    ConditionGroup,
    ConditionGroupType,
    ConditionOperator,
    DomainType,
    Rule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)


def _evaluate_condition(cond: Condition, data: dict[str, Any]) -> bool:
    field_value = data.get(cond.field)
    target = cond.value

    try:
        if cond.operator == ConditionOperator.equals:
            return bool(field_value == target)
        elif cond.operator == ConditionOperator.not_equals:
            return bool(field_value != target)
        elif cond.operator == ConditionOperator.greater_than:
            return field_value is not None and target is not None and field_value > target
        elif cond.operator == ConditionOperator.less_than:
            return field_value is not None and target is not None and field_value < target
        elif cond.operator == ConditionOperator.contains:
            if isinstance(field_value, str) and isinstance(target, str):
                return target in field_value
            if isinstance(field_value, list):
                return target in field_value
            return False
        elif cond.operator == ConditionOperator.in_:
            if isinstance(target, list):
                return field_value in target
            return False
        elif cond.operator == ConditionOperator.not_in:
            if isinstance(target, list):
                return field_value not in target
            return True
    except (TypeError, ValueError):
        return False
    return False


def _evaluate_condition_group(group: ConditionGroup, data: dict[str, Any]) -> bool:
    results: list[bool] = []
    for item in group.conditions:
        if isinstance(item, ConditionGroup):
            result = _evaluate_condition_group(item, data)
        else:
            result = _evaluate_condition(item, data)
        results.append(result)

    if group.type == ConditionGroupType.and_:
        return all(results)
    elif group.type == ConditionGroupType.or_:
        return any(results)
    elif group.type == ConditionGroupType.not_:
        return not all(results) if results else True
    return True


def _execute_action(action: Action, context: RuleEvaluationContext) -> dict[str, Any]:
    result: dict[str, Any] = {"action_type": action.type.value, "status": "executed"}

    if action.type == ActionType.update_field:
        field = action.params.get("field")
        value = action.params.get("value")
        result.update({"field": field, "value": value})

    elif action.type == ActionType.send_notification:
        result.update(
            {
                "channel": action.params.get("channel", "in_app"),
                "message": action.params.get("message", ""),
            }
        )

    elif action.type == ActionType.trigger_workflow:
        result.update(
            {
                "workflow_id": action.params.get("workflow_id"),
                "trigger_data": action.params.get("trigger_data", {}),
            }
        )

    elif action.type == ActionType.create_task:
        result.update(
            {
                "title": action.params.get("title", ""),
                "assignee": action.params.get("assignee"),
                "priority": action.params.get("priority", "medium"),
            }
        )

    elif action.type == ActionType.score_adjustment:
        result.update(
            {
                "score_type": action.params.get("score_type", "confidence"),
                "adjustment": action.params.get("adjustment", 0),
            }
        )

    elif action.type == ActionType.flag_company:
        result.update(
            {
                "flag": action.params.get("flag", "review"),
                "reason": action.params.get("reason", ""),
            }
        )

    elif action.type == ActionType.assign_owner:
        result.update(
            {
                "owner_id": action.params.get("owner_id"),
                "owner_type": action.params.get("owner_type", "user"),
            }
        )

    return result


def evaluate_rule(rule: Rule, context: RuleEvaluationContext) -> RuleEvaluationResult:
    matched = _evaluate_condition_group(rule.conditions, context.data)
    actions_executed: list[dict[str, Any]] = []

    if matched and rule.enabled:
        for action in rule.actions:
            result = _execute_action(action, context)
            actions_executed.append(result)

    return RuleEvaluationResult(
        rule_id=rule.id,
        rule_name=rule.name,
        matched=matched,
        actions_executed=actions_executed,
    )


def evaluate_rules_batch(
    rules: list[Rule],
    context: RuleEvaluationContext,
) -> BatchEvaluationResult:
    start = time.perf_counter()
    results: list[RuleEvaluationResult] = []

    for rule in rules:
        if rule.domain != context.entity_type and rule.domain != "workflow":
            continue
        result = evaluate_rule(rule, context)
        results.append(result)

    matched_count = sum(1 for r in results if r.matched)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return BatchEvaluationResult(
        results=results,
        total_rules=len(results),
        matched_count=matched_count,
        execution_time_ms=elapsed_ms,
    )


class RulesEngine:
    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def list_rules(self, domain: DomainType | None = None) -> list[Rule]:
        all_rules = list(self._rules.values())
        if domain:
            all_rules = [r for r in all_rules if r.domain == domain]
        return sorted(all_rules, key=lambda r: r.priority, reverse=True)

    def get_rule(self, rule_id: str) -> Rule | None:
        return self._rules.get(rule_id)

    def create_rule(self, rule: Rule) -> Rule:
        if rule.id in self._rules:
            raise ValueError(f"Rule '{rule.id}' already exists")
        self._rules[rule.id] = rule
        return rule

    def update_rule(self, rule_id: str, updates: dict[str, Any]) -> Rule:
        existing = self._rules.get(rule_id)
        if not existing:
            raise ValueError(f"Rule '{rule_id}' not found")

        import copy

        updated = copy.deepcopy(existing)

        for key, value in updates.items():
            if hasattr(updated, key) and key not in ("id", "created_at"):
                setattr(updated, key, value)

        updated.updated_at = updated.updated_at
        self._rules[rule_id] = updated
        return updated

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id not in self._rules:
            return False
        del self._rules[rule_id]
        return True

    def evaluate(self, rule_id: str, context: RuleEvaluationContext) -> RuleEvaluationResult:
        rule = self._rules.get(rule_id)
        if not rule:
            raise ValueError(f"Rule '{rule_id}' not found")
        return evaluate_rule(rule, context)

    def evaluate_batch(self, context: RuleEvaluationContext) -> BatchEvaluationResult:
        return evaluate_rules_batch(list(self._rules.values()), context)


_rules_engine = RulesEngine()
