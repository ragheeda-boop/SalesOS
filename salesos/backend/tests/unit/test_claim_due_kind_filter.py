"""IL-2B.2: claim_due kind filter must not emit dangling t2.kind.

Live dispatcher always passes kinds_include / kinds_exclude. The candidates
CTE selects FROM agent_tasks with no t2 alias, so t2.kind is invalid SQL.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects.postgresql import ARRAY

from runtime.agent_runtime.queue import _claim_kind_clause, claim_due

# Mirror dispatcher FAST_KINDS / research-lane exclude (do not import dispatcher).
KINDS_FAST = ["brand", "portrait", "simple_lookup"]
KINDS_RESEARCH = [
    "research_company",
    "assess_icp",
    "investigate_expansion",
    "executive_change",
    "verify_license",
    "stagnation_alert",
    "identify",
    "profile",
    "recheck",
    "meeting_prep",
    "company_profile",
    "workspace_profile",
]


def _sql(query) -> str:
    return str(query)


class TestClaimKindClause:
    def test_include_uses_agent_tasks_kind_not_t2(self):
        clause, params = _claim_kind_clause(KINDS_FAST, None)
        assert "t2.kind" not in clause
        assert "t2." not in clause
        assert "agent_tasks.kind = ANY(:kinds)" in clause
        assert params["kinds"] == KINDS_FAST

    def test_exclude_uses_agent_tasks_kind_not_t2(self):
        clause, params = _claim_kind_clause(None, KINDS_FAST)
        assert "t2.kind" not in clause
        assert "t2." not in clause
        assert "agent_tasks.kind != ALL(:kinds)" in clause
        assert params["kinds"] == KINDS_FAST

    def test_research_include_filters_research_kinds(self):
        clause, params = _claim_kind_clause(KINDS_RESEARCH, None)
        assert "agent_tasks.kind = ANY(:kinds)" in clause
        assert params["kinds"] == KINDS_RESEARCH
        assert "brand" not in params["kinds"]

    def test_no_kinds_is_true(self):
        clause, params = _claim_kind_clause(None, None)
        assert clause == "TRUE"
        assert params == {}


async def _capture_claim(**kwargs):
    captured: dict = {}
    session = AsyncMock()
    result = MagicMock()
    result.fetchall.return_value = []

    async def execute(query, params):
        captured["query"] = query
        captured["sql"] = _sql(query)
        captured["params"] = params
        return result

    session.execute = execute
    await claim_due(session, "tenant-1", **kwargs)
    return captured


class TestClaimDueKindSql:
    @pytest.mark.asyncio
    async def test_kinds_include_fast_does_not_emit_t2(self):
        captured = await _capture_claim(kinds_include=KINDS_FAST)
        sql = captured["sql"]
        assert "t2.kind" not in sql
        assert "t2." not in sql
        assert "agent_tasks.kind = ANY(:kinds)" in sql
        assert captured["params"]["kinds"] == KINDS_FAST

    @pytest.mark.asyncio
    async def test_kinds_exclude_fast_research_lane_does_not_emit_t2(self):
        captured = await _capture_claim(kinds_exclude=KINDS_FAST)
        sql = captured["sql"]
        assert "t2.kind" not in sql
        assert "t2." not in sql
        assert "agent_tasks.kind != ALL(:kinds)" in sql
        assert captured["params"]["kinds"] == KINDS_FAST

    @pytest.mark.asyncio
    async def test_kinds_include_research_does_not_emit_t2(self):
        captured = await _capture_claim(kinds_include=KINDS_RESEARCH)
        sql = captured["sql"]
        assert "t2.kind" not in sql
        assert "agent_tasks.kind = ANY(:kinds)" in sql
        assert captured["params"]["kinds"] == KINDS_RESEARCH

    @pytest.mark.asyncio
    async def test_kinds_bind_is_text_array(self):
        captured = await _capture_claim(kinds_include=KINDS_FAST)
        bind = captured["query"]._bindparams["kinds"]
        assert isinstance(bind.type, ARRAY)

    @pytest.mark.asyncio
    async def test_no_kinds_keeps_true_and_no_t2(self):
        captured = await _capture_claim()
        sql = captured["sql"]
        assert "t2.kind" not in sql
        assert "AND TRUE" in sql
        assert "kinds" not in captured["params"]
        assert "kinds" not in captured["query"]._bindparams
