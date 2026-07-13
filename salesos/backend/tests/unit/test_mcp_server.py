"""Tests for SalesOS MCP Server — validates tools, auth, and error handling."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from mcp_server.server import create_server
from mcp_server.tools import set_valid_api_keys, _auth


# ── Fixtures ──

@pytest.fixture(autouse=True)
def setup_api_keys():
    set_valid_api_keys(["test-api-key", "secondary-key"])
    yield
    set_valid_api_keys([])


@pytest.fixture
def mcp():
    return create_server(api_keys=["test-api-key"])


# ── Auth Tests ──

class TestAuth:
    def test_valid_api_key(self):
        client = _auth("test-api-key")
        assert client is not None

    def test_secondary_key(self):
        client = _auth("secondary-key")
        assert client is not None

    def test_invalid_key_raises(self):
        with pytest.raises(PermissionError, match="Invalid API key"):
            _auth("bad-key")

    def test_empty_key_raises(self):
        with pytest.raises(PermissionError):
            _auth("")


# ── Tool Registration Tests ──

class TestToolRegistration:
    def test_tools_are_registered(self, mcp):
        """All expected tools should be registered on the MCP server."""
        tool_names = {t.name for t in mcp._tool_manager._tools.values()}
        expected = {
            "search_companies",
            "get_company",
            "get_company_pipeline",
            "get_pipeline_summary",
            "get_opportunity",
            "evaluate_decision",
            "get_decision_history",
            "search",
            "search_employees",
            "get_revenue_analytics",
            "get_market_intelligence",
            "list_workflows",
            "execute_workflow",
        }
        missing = expected - tool_names
        assert not missing, f"Missing tools: {missing}"

    def test_tool_count(self, mcp):
        tool_names = {t.name for t in mcp._tool_manager._tools.values()}
        assert len(tool_names) >= 13

    def test_no_duplicate_warnings(self, mcp):
        """Creating a second server should not produce duplicate warnings."""
        import io
        import logging
        logger = logging.getLogger("mcp.server.fastmcp")
        level = logger.level
        logger.setLevel(logging.WARNING)
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        logger.addHandler(handler)
        try:
            mcp2 = create_server(api_keys=["test-api-key"])
            output = buf.getvalue()
            assert "already exists" not in output, f"Duplicates detected: {output}"
        finally:
            logger.removeHandler(handler)
            logger.setLevel(level)


# ── Server Initialization Tests ──

class TestServerInit:
    def test_create_with_keys(self):
        server = create_server(api_keys=["custom-key"])
        assert server is not None
        assert server.name == "salesos"

    def test_create_defaults_to_env(self):
        with patch.dict(os.environ, {"MCP_API_KEY": "env-key"}, clear=True):
            server = create_server()
            assert server is not None
            from mcp_server.tools import VALID_API_KEYS
            assert "env-key" in VALID_API_KEYS


# ── Tool Handler Tests ──

class TestToolHandlers:
    def test_search_companies_tool_exists(self, mcp):
        tool = mcp._tool_manager._tools.get("search_companies")
        assert tool is not None
        assert tool.name == "search_companies"

    def test_get_company_tool_exists(self, mcp):
        tool = mcp._tool_manager._tools.get("get_company")
        assert tool is not None

    def test_get_pipeline_summary_tool_exists(self, mcp):
        tool = mcp._tool_manager._tools.get("get_pipeline_summary")
        assert tool is not None

    def test_search_tool_exists(self, mcp):
        tool = mcp._tool_manager._tools.get("search")
        assert tool is not None

    def test_evaluate_decision_tool_exists(self, mcp):
        tool = mcp._tool_manager._tools.get("evaluate_decision")
        assert tool is not None

    def test_get_revenue_analytics_tool_exists(self, mcp):
        tool = mcp._tool_manager._tools.get("get_revenue_analytics")
        assert tool is not None

    def test_list_workflows_tool_exists(self, mcp):
        tool = mcp._tool_manager._tools.get("list_workflows")
        assert tool is not None

    def test_search_companies_has_required_params(self, mcp):
        tool = mcp._tool_manager._tools.get("search_companies")
        params = tool.parameters
        required = set(params.get("required", []))
        assert "api_key" in required
        assert "query" in required

    def test_get_company_has_required_params(self, mcp):
        tool = mcp._tool_manager._tools.get("get_company")
        params = tool.parameters
        required = set(params.get("required", []))
        assert "api_key" in required
        assert "company_id" in required

    def test_execute_workflow_has_required_params(self, mcp):
        tool = mcp._tool_manager._tools.get("execute_workflow")
        params = tool.parameters
        required = set(params.get("required", []))
        assert "api_key" in required
        assert "workflow_id" in required

    def test_tool_names_are_descriptive(self, mcp):
        for name, tool in mcp._tool_manager._tools.items():
            assert tool.description, f"Tool {name} has no description"
            assert len(tool.description) > 10, f"Tool {name} description too short"
