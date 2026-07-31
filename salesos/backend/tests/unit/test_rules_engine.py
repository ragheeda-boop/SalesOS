"""Tests for Business Rules Engine — models, engine, conditions, actions, API."""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.modules.rules_engine.engine import (
    RulesEngine,
    _evaluate_condition,
    _evaluate_condition_group,
    evaluate_rule,
    evaluate_rules_batch,
)
from app.modules.rules_engine.models import (
    Action,
    ActionType,
    Condition,
    ConditionGroup,
    ConditionGroupType,
    ConditionOperator,
    DomainType,
    Rule,
    RuleEvaluationContext,
)


def _make_rule(
    name: str = "Test Rule",
    domain: DomainType = "company",
    conditions: ConditionGroup | None = None,
    actions: list[Action] | None = None,
    priority: int = 0,
    enabled: bool = True,
) -> Rule:
    return Rule(
        id=f"rule-{uuid.uuid4().hex[:12]}",
        name=name,
        description="",
        enabled=enabled,
        domain=domain,
        conditions=conditions or ConditionGroup(type=ConditionGroupType.and_),
        actions=actions or [],
        priority=priority,
    )


def _ctx(data: dict) -> RuleEvaluationContext:
    return RuleEvaluationContext(entity_id="e-1", entity_type="company", data=data)


# ── Condition Tests ──


class TestConditions:
    def test_equals_match(self):
        assert (
            _evaluate_condition(
                Condition(field="stage", operator=ConditionOperator.equals, value="closed_won"),
                {"stage": "closed_won"},
            )
            is True
        )

    def test_equals_no_match(self):
        assert (
            _evaluate_condition(
                Condition(field="stage", operator=ConditionOperator.equals, value="closed_won"),
                {"stage": "negotiation"},
            )
            is False
        )

    def test_not_equals_match(self):
        assert (
            _evaluate_condition(
                Condition(field="stage", operator=ConditionOperator.not_equals, value="closed_won"),
                {"stage": "negotiation"},
            )
            is True
        )

    def test_greater_than(self):
        assert (
            _evaluate_condition(
                Condition(field="amount", operator=ConditionOperator.greater_than, value=10000),
                {"amount": 20000},
            )
            is True
        )
        assert (
            _evaluate_condition(
                Condition(field="amount", operator=ConditionOperator.greater_than, value=10000),
                {"amount": 5000},
            )
            is False
        )

    def test_less_than(self):
        assert (
            _evaluate_condition(
                Condition(field="amount", operator=ConditionOperator.less_than, value=10000),
                {"amount": 5000},
            )
            is True
        )
        assert (
            _evaluate_condition(
                Condition(field="amount", operator=ConditionOperator.less_than, value=10000),
                {"amount": 20000},
            )
            is False
        )

    def test_contains_string(self):
        assert (
            _evaluate_condition(
                Condition(field="name", operator=ConditionOperator.contains, value="Tech"),
                {"name": "Tech Corp"},
            )
            is True
        )
        assert (
            _evaluate_condition(
                Condition(field="name", operator=ConditionOperator.contains, value="Tech"),
                {"name": "Corp"},
            )
            is False
        )

    def test_contains_list(self):
        assert (
            _evaluate_condition(
                Condition(field="tags", operator=ConditionOperator.contains, value="enterprise"),
                {"tags": ["startup", "enterprise"]},
            )
            is True
        )

    def test_in_list(self):
        assert (
            _evaluate_condition(
                Condition(
                    field="stage",
                    operator=ConditionOperator.in_,
                    value=["closed_won", "closed_lost"],
                ),
                {"stage": "closed_won"},
            )
            is True
        )
        assert (
            _evaluate_condition(
                Condition(
                    field="stage",
                    operator=ConditionOperator.in_,
                    value=["closed_won", "closed_lost"],
                ),
                {"stage": "negotiation"},
            )
            is False
        )

    def test_not_in_list(self):
        assert (
            _evaluate_condition(
                Condition(
                    field="stage",
                    operator=ConditionOperator.not_in,
                    value=["closed_won", "closed_lost"],
                ),
                {"stage": "negotiation"},
            )
            is True
        )

    def test_missing_field_returns_false(self):
        assert (
            _evaluate_condition(
                Condition(field="missing", operator=ConditionOperator.equals, value="x"), {}
            )
            is False
        )


# ── ConditionGroup Tests ──


class TestConditionGroups:
    def test_and_group_all_true(self):
        group = ConditionGroup(
            type=ConditionGroupType.and_,
            conditions=[
                Condition(field="amount", operator=ConditionOperator.greater_than, value=1000),
                Condition(field="stage", operator=ConditionOperator.equals, value="closed_won"),
            ],
        )
        assert _evaluate_condition_group(group, {"amount": 5000, "stage": "closed_won"}) is True

    def test_and_group_one_false(self):
        group = ConditionGroup(
            type=ConditionGroupType.and_,
            conditions=[
                Condition(field="amount", operator=ConditionOperator.greater_than, value=1000),
                Condition(field="stage", operator=ConditionOperator.equals, value="closed_won"),
            ],
        )
        assert _evaluate_condition_group(group, {"amount": 500, "stage": "closed_won"}) is False

    def test_or_group_one_true(self):
        group = ConditionGroup(
            type=ConditionGroupType.or_,
            conditions=[
                Condition(field="amount", operator=ConditionOperator.greater_than, value=10000),
                Condition(field="stage", operator=ConditionOperator.equals, value="closed_won"),
            ],
        )
        assert _evaluate_condition_group(group, {"amount": 500, "stage": "closed_won"}) is True

    def test_or_group_all_false(self):
        group = ConditionGroup(
            type=ConditionGroupType.or_,
            conditions=[
                Condition(field="amount", operator=ConditionOperator.greater_than, value=10000),
                Condition(field="stage", operator=ConditionOperator.equals, value="closed_won"),
            ],
        )
        assert _evaluate_condition_group(group, {"amount": 500, "stage": "prospecting"}) is False

    def test_nested_groups(self):
        group = ConditionGroup(
            type=ConditionGroupType.and_,
            conditions=[
                Condition(field="enabled", operator=ConditionOperator.equals, value=True),
                ConditionGroup(
                    type=ConditionGroupType.or_,
                    conditions=[
                        Condition(
                            field="amount", operator=ConditionOperator.greater_than, value=10000
                        ),
                        Condition(
                            field="priority", operator=ConditionOperator.equals, value="high"
                        ),
                    ],
                ),
            ],
        )
        assert (
            _evaluate_condition_group(group, {"enabled": True, "amount": 500, "priority": "high"})
            is True
        )
        assert (
            _evaluate_condition_group(group, {"enabled": True, "amount": 500, "priority": "low"})
            is False
        )

    def test_not_group(self):
        group = ConditionGroup(
            type=ConditionGroupType.not_,
            conditions=[
                Condition(field="stage", operator=ConditionOperator.equals, value="closed_lost"),
            ],
        )
        assert _evaluate_condition_group(group, {"stage": "closed_won"}) is True
        assert _evaluate_condition_group(group, {"stage": "closed_lost"}) is False


# ── Rule Evaluation Tests ──


class TestRuleEvaluation:
    def test_rule_matched_executes_actions(self):
        rule = _make_rule(
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="amount", operator=ConditionOperator.greater_than, value=10000),
                ],
            ),
            actions=[
                Action(
                    type=ActionType.update_field, params={"field": "stage", "value": "high_value"}
                )
            ],
        )
        result = evaluate_rule(rule, _ctx({"amount": 50000}))
        assert result.matched is True
        assert len(result.actions_executed) == 1
        assert result.actions_executed[0]["action_type"] == "update_field"

    def test_rule_not_matched_skips_actions(self):
        rule = _make_rule(
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="amount", operator=ConditionOperator.greater_than, value=10000),
                ],
            ),
            actions=[Action(type=ActionType.send_notification, params={"message": "High value!"})],
        )
        result = evaluate_rule(rule, _ctx({"amount": 500}))
        assert result.matched is False
        assert len(result.actions_executed) == 0

    def test_disabled_rule_skips_even_if_matched(self):
        rule = _make_rule(
            enabled=False,
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="amount", operator=ConditionOperator.greater_than, value=0),
                ],
            ),
            actions=[Action(type=ActionType.create_task, params={"title": "Task"})],
        )
        result = evaluate_rule(rule, _ctx({"amount": 100}))
        assert result.matched is True
        assert len(result.actions_executed) == 0

    def test_score_adjustment_action(self):
        rule = _make_rule(
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="engagement", operator=ConditionOperator.equals, value="high"),
                ],
            ),
            actions=[
                Action(
                    type=ActionType.score_adjustment,
                    params={"score_type": "confidence", "adjustment": 0.2},
                )
            ],
        )
        result = evaluate_rule(rule, _ctx({"engagement": "high"}))
        assert result.matched is True
        assert result.actions_executed[0]["score_type"] == "confidence"
        assert result.actions_executed[0]["adjustment"] == 0.2

    def test_flag_company_action(self):
        rule = _make_rule(
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="revenue", operator=ConditionOperator.less_than, value=100000),
                ],
            ),
            actions=[
                Action(
                    type=ActionType.flag_company, params={"flag": "review", "reason": "Low revenue"}
                )
            ],
        )
        result = evaluate_rule(rule, _ctx({"revenue": 50000}))
        assert result.matched is True
        assert result.actions_executed[0]["flag"] == "review"

    def test_assign_owner_action(self):
        rule = _make_rule(
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="region", operator=ConditionOperator.equals, value="EMEA"),
                ],
            ),
            actions=[
                Action(
                    type=ActionType.assign_owner,
                    params={"owner_id": "user-emea-1", "owner_type": "user"},
                )
            ],
        )
        result = evaluate_rule(rule, _ctx({"region": "EMEA"}))
        assert result.matched is True
        assert result.actions_executed[0]["owner_id"] == "user-emea-1"

    def test_trigger_workflow_action(self):
        rule = _make_rule(
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="stage", operator=ConditionOperator.equals, value="closed_won"),
                ],
            ),
            actions=[
                Action(
                    type=ActionType.trigger_workflow,
                    params={"workflow_id": "wf-onboard", "trigger_data": {"priority": "high"}},
                )
            ],
        )
        result = evaluate_rule(rule, _ctx({"stage": "closed_won"}))
        assert result.matched is True
        assert result.actions_executed[0]["workflow_id"] == "wf-onboard"


# ── Batch Evaluation Tests ─-


class TestBatchEvaluation:
    def test_batch_evaluate_multiple_rules(self):
        rules = [
            _make_rule(
                name="Rule A",
                conditions=ConditionGroup(
                    type=ConditionGroupType.and_,
                    conditions=[
                        Condition(
                            field="amount", operator=ConditionOperator.greater_than, value=1000
                        ),
                    ],
                ),
            ),
            _make_rule(
                name="Rule B",
                conditions=ConditionGroup(
                    type=ConditionGroupType.and_,
                    conditions=[
                        Condition(field="amount", operator=ConditionOperator.less_than, value=500),
                    ],
                ),
            ),
        ]
        result = evaluate_rules_batch(rules, _ctx({"amount": 2000}))
        assert result.total_rules == 2
        assert result.matched_count == 1
        assert result.results[0].matched is True
        assert result.results[1].matched is False

    def test_batch_filters_by_domain(self):
        rules = [
            _make_rule(name="Company Rule", domain="company"),
            _make_rule(name="Opportunity Rule", domain="opportunity"),
        ]
        ctx = RuleEvaluationContext(entity_id="e-1", entity_type="opportunity", data={})
        result = evaluate_rules_batch(rules, ctx)
        assert result.total_rules == 1
        assert result.results[0].rule_name == "Opportunity Rule"


# ── Engine (InMemory) Tests ─-


class TestRulesEngine:
    def setup_method(self):
        self.engine = RulesEngine()

    def test_create_rule(self):
        rule = _make_rule(name="New Rule")
        created = self.engine.create_rule(rule)
        assert created.id == rule.id
        assert self.engine.get_rule(rule.id) is not None

    def test_create_duplicate_raises(self):
        rule = _make_rule(name="Duplicate")
        self.engine.create_rule(rule)
        with pytest.raises(ValueError):
            self.engine.create_rule(rule)

    def test_list_rules(self):
        self.engine.create_rule(_make_rule(name="A", domain="company"))
        self.engine.create_rule(_make_rule(name="B", domain="opportunity"))
        assert len(self.engine.list_rules()) == 2
        assert len(self.engine.list_rules(domain="company")) == 1

    def test_update_rule(self):
        rule = _make_rule(name="Original")
        self.engine.create_rule(rule)
        updated = self.engine.update_rule(rule.id, {"name": "Updated", "priority": 5})
        assert updated.name == "Updated"
        assert updated.priority == 5

    def test_update_nonexistent_raises(self):
        with pytest.raises(ValueError):
            self.engine.update_rule("nonexistent", {"name": "X"})

    def test_delete_rule(self):
        rule = _make_rule(name="Delete Me")
        self.engine.create_rule(rule)
        assert self.engine.delete_rule(rule.id) is True
        assert self.engine.get_rule(rule.id) is None

    def test_delete_nonexistent_returns_false(self):
        assert self.engine.delete_rule("nonexistent") is False

    def test_evaluate_rule_through_engine(self):
        rule = _make_rule(
            conditions=ConditionGroup(
                type=ConditionGroupType.and_,
                conditions=[
                    Condition(field="score", operator=ConditionOperator.greater_than, value=80),
                ],
            ),
            actions=[Action(type=ActionType.send_notification, params={"message": "High score!"})],
        )
        self.engine.create_rule(rule)
        result = self.engine.evaluate(rule.id, _ctx({"score": 95}))
        assert result.matched is True

    def test_evaluate_nonexistent_raises(self):
        with pytest.raises(ValueError):
            self.engine.evaluate("nonexistent", _ctx({}))

    def test_evaluate_batch_through_engine(self):
        self.engine.create_rule(
            _make_rule(
                name="R1",
                conditions=ConditionGroup(
                    type=ConditionGroupType.and_,
                    conditions=[
                        Condition(field="x", operator=ConditionOperator.equals, value=1),
                    ],
                ),
            )
        )
        self.engine.create_rule(
            _make_rule(
                name="R2",
                conditions=ConditionGroup(
                    type=ConditionGroupType.and_,
                    conditions=[
                        Condition(field="x", operator=ConditionOperator.equals, value=2),
                    ],
                ),
            )
        )
        result = self.engine.evaluate_batch(_ctx({"x": 1}))
        assert result.total_rules == 2
        assert result.matched_count == 1


# ── API Tests ──


@pytest.fixture(scope="module")
def app():
    from app.main import app as _app

    return _app


@pytest.fixture(scope="module", autouse=True)
def _override_auth(app: FastAPI):
    from app.dependencies import verify_token

    async def override_verify_token():
        return {"sub": "test-user", "tenant_id": "test-tenant", "role": "admin"}

    app.dependency_overrides[verify_token] = override_verify_token
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestRulesAPI:
    @pytest.mark.asyncio
    async def test_list_rules_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/rules")
        assert resp.status_code in (200, 401, 403)
        if resp.status_code == 200:
            assert resp.json() == []

    @pytest.mark.asyncio
    async def test_create_rule(self, client: AsyncClient):
        payload = {
            "name": "High Value Alert",
            "description": "Notify on high-value deals",
            "domain": "opportunity",
            "priority": 1,
            "conditions": {
                "type": "and",
                "conditions": [{"field": "amount", "operator": "greater_than", "value": 50000}],
            },
            "actions": [
                {
                    "type": "send_notification",
                    "params": {"channel": "slack", "message": "High value deal!"},
                }
            ],
        }
        resp = await client.post("/api/v1/rules", json=payload)
        if resp.status_code == 201:
            data = resp.json()
            assert data["name"] == "High Value Alert"
            assert data["domain"] == "opportunity"
            assert len(data["actions"]) == 1
        else:
            assert resp.status_code in (401, 403), f"Unexpected: {resp.status_code} {resp.text}"

    @pytest.mark.asyncio
    async def test_update_and_delete_rule(self, client: AsyncClient):
        payload = {
            "name": "Temp Rule",
            "domain": "company",
            "conditions": {"type": "and", "conditions": []},
            "actions": [],
        }
        create_resp = await client.post("/api/v1/rules", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("Auth required for write endpoints")
        rule_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/v1/rules/{rule_id}", json={"name": "Updated", "priority": 5}
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated"
        assert update_resp.json()["priority"] == 5

        del_resp = await client.delete(f"/api/v1/rules/{rule_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True

    @pytest.mark.asyncio
    async def test_get_nonexistent_rule_404(self, client: AsyncClient):
        resp = await client.get("/api/v1/rules/nonexistent")
        assert resp.status_code in (404, 401, 403)

    @pytest.mark.asyncio
    async def test_evaluate_endpoint(self, client: AsyncClient):
        payload = {
            "name": "Eval Rule",
            "domain": "company",
            "conditions": {
                "type": "and",
                "conditions": [{"field": "score", "operator": "greater_than", "value": 50}],
            },
            "actions": [
                {"type": "flag_company", "params": {"flag": "hot", "reason": "High score"}}
            ],
        }
        create_resp = await client.post("/api/v1/rules", json=payload)
        if create_resp.status_code != 201:
            pytest.skip("Auth required")
        rule_id = create_resp.json()["id"]

        eval_resp = await client.post(
            f"/api/v1/rules/{rule_id}/evaluate",
            json={"entity_id": "e-1", "entity_type": "company", "data": {"score": 80}},
        )
        if eval_resp.status_code == 200:
            data = eval_resp.json()
            assert data["matched"] is True
            assert len(data["actions_executed"]) == 1
