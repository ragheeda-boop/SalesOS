"""MCP tools for SalesOS — each decorated with @mcp.tool()."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server.salesos_client import SalesOSClient

VALID_API_KEYS: set[str] = set()


def set_valid_api_keys(keys: list[str]) -> None:
    VALID_API_KEYS.clear()
    VALID_API_KEYS.update(keys)


def _auth(api_key: str) -> SalesOSClient:
    if api_key not in VALID_API_KEYS:
        raise PermissionError(f"Invalid API key: {api_key[:8]}...")
    return SalesOSClient()


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the given FastMCP instance."""

    @mcp.tool()
    async def search_companies(api_key: str, query: str, limit: int = 10) -> str:
        """Search for companies by name, CR number, or industry.
        Returns a list of matching companies with key details.
        """
        client = _auth(api_key)
        try:
            results = await client.search_companies(query, limit)
            return str(results)
        except Exception as e:
            return f"Error searching companies: {e}"

    @mcp.tool()
    async def get_company(api_key: str, company_id: str) -> str:
        """Get detailed company information including contact details, status, and health.
        Use the company's unique ID returned from search_companies.
        """
        client = _auth(api_key)
        try:
            result = await client.get_company(company_id)
            if not result:
                return f"Company not found: {company_id}"
            return str(result)
        except Exception as e:
            return f"Error getting company: {e}"

    @mcp.tool()
    async def get_company_pipeline(api_key: str, company_id: str) -> str:
        """Get all pipeline opportunities for a specific company.
        Returns opportunities with stage, value, probability, and status.
        """
        client = _auth(api_key)
        try:
            result = await client.get_company_pipeline(company_id)
            return str(result)
        except Exception as e:
            return f"Error getting company pipeline: {e}"

    @mcp.tool()
    async def get_pipeline_summary(api_key: str) -> str:
        """Get an overview of the entire sales pipeline.
        Returns pipeline velocity, conversion rates, deal health map, and forecast.
        """
        client = _auth(api_key)
        try:
            result = await client.get_pipeline_summary()
            return str(result)
        except Exception as e:
            return f"Error getting pipeline summary: {e}"

    @mcp.tool()
    async def get_opportunity(api_key: str, opportunity_id: str) -> str:
        """Get detailed information about a specific opportunity/deal.
        Includes stage, value, probability, owner, and expected close date.
        """
        client = _auth(api_key)
        try:
            result = await client.get_opportunity(opportunity_id)
            if not result:
                return f"Opportunity not found: {opportunity_id}"
            return str(result)
        except Exception as e:
            return f"Error getting opportunity: {e}"

    @mcp.tool()
    async def evaluate_decision(api_key: str, company_id: str, context: str = "") -> str:
        """Evaluate the next-best-action (NBA) for a company or opportunity.
        Returns a recommendation with confidence score, reasoning, and alternatives.
        The context parameter describes the current situation for better recommendations.
        """
        client = _auth(api_key)
        try:
            result = await client.evaluate_decision(company_id, context)
            return str(result)
        except Exception as e:
            return f"Error evaluating decision: {e}"

    @mcp.tool()
    async def get_decision_history(api_key: str, company_id: str, limit: int = 10) -> str:
        """Get recent decisions and recommendations made for a company.
        Returns a history of NBA (Next-Best-Action) evaluations.
        """
        client = _auth(api_key)
        try:
            result = await client.get_decision_history(company_id, limit)
            return str(result)
        except Exception as e:
            return f"Error getting decision history: {e}"

    @mcp.tool()
    async def search(api_key: str, query: str, domain: str = "all") -> str:
        """Unified search across companies, contacts, and opportunities.
        Uses hybrid search (full-text + semantic) by default.
        Domain options: all, fulltext, semantic, graph, hybrid.
        """
        client = _auth(api_key)
        try:
            result = await client.search(query, domain)
            return str(result)
        except Exception as e:
            return f"Error searching: {e}"

    @mcp.tool()
    async def search_employees(api_key: str, query: str, company_id: str | None = None) -> str:
        """Search for employees by name, email, or role.
        Optionally filter by company_id to find employees at a specific company.
        """
        client = _auth(api_key)
        try:
            result = await client.search_employees(query, company_id)
            return str(result)
        except Exception as e:
            return f"Error searching employees: {e}"

    @mcp.tool()
    async def get_revenue_analytics(api_key: str, timeframe: str = "monthly") -> str:
        """Get revenue KPIs and analytics.
        Returns booked revenue, pipeline value, growth rates, team stats, and new business metrics.
        Timeframe options: monthly, quarterly, yearly.
        """
        client = _auth(api_key)
        try:
            result = await client.get_revenue_analytics(timeframe)
            return str(result)
        except Exception as e:
            return f"Error getting revenue analytics: {e}"

    @mcp.tool()
    async def get_market_intelligence(api_key: str, industry: str | None = None) -> str:
        """Get market trends and intelligence data.
        Optionally filter by industry segment. Returns company counts, pipeline values by industry.
        """
        client = _auth(api_key)
        try:
            result = await client.get_market_intelligence(industry)
            return str(result)
        except Exception as e:
            return f"Error getting market intelligence: {e}"

    @mcp.tool()
    async def list_workflows(api_key: str, status: str | None = None) -> str:
        """List automation workflows with optional status filter.
        Returns workflow name, trigger type, status, and step count.
        Status options: active, inactive, draft.
        """
        client = _auth(api_key)
        try:
            result = await client.list_workflows(status)
            return str(result)
        except Exception as e:
            return f"Error listing workflows: {e}"

    @mcp.tool()
    async def execute_workflow(api_key: str, workflow_id: str, context: dict | None = None) -> str:
        """Execute a workflow by its ID with optional context parameters.
        The workflow must be in 'active' status. Returns execution results for each step.
        """
        client = _auth(api_key)
        try:
            result = await client.execute_workflow(workflow_id, context or {})
            return str(result)
        except Exception as e:
            return f"Error executing workflow: {e}"
