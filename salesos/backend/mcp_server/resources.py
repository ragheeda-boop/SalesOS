"""MCP resources for SalesOS — readable URIs exposing knowledge."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server.salesos_client import SalesOSClient


def register_resources(mcp: FastMCP, api_key: str) -> None:
    """Register all resources with the given FastMCP instance."""

    client = SalesOSClient()

    @mcp.resource("salesos://pipeline/summary")
    async def pipeline_summary() -> str:
        """Current pipeline overview — velocity, conversion, health, forecast."""
        try:
            result = await client.get_pipeline_summary()
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.resource("salesos://metrics/kpi")
    async def kpi_metrics() -> str:
        """Current KPI metrics — revenue, pipeline, team, health."""
        try:
            result = await client.get_kpi_metrics()
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.resource("salesos://search/recent")
    async def recent_search() -> str:
        """Recent search activity and top searches."""
        try:
            from sqlalchemy import DateTime, Float, Integer, String, column, select, table

            from app.database import async_session as db_session

            # EAB-001-P1-DRIFT-01: ephemeral TableClause — no private metadata registry.
            # CI-19 Slice 6: allowlisted Core columns (no sqlalchemy.text).
            search_log = table(
                "search_log",
                column("query", String),
                column("strategy", String),
                column("total", Integer),
                column("took_ms", Float),
                column("created_at", DateTime),
                column("tenant_id", String),
            )
            async with db_session() as db:
                rows = await db.execute(
                    select(
                        search_log.c.query,
                        search_log.c.strategy,
                        search_log.c.total,
                        search_log.c.took_ms,
                        search_log.c.created_at,
                    )
                    .where(search_log.c.tenant_id == "default")
                    .order_by(search_log.c.created_at.desc())
                    .limit(10)
                )
                results = [
                    {
                        "query": r.query,
                        "strategy": r.strategy,
                        "total": r.total,
                        "took_ms": round(float(r.took_ms), 2) if r.took_ms else None,
                        "created_at": str(r.created_at) if r.created_at else None,
                    }
                    for r in rows.all()
                ]
                return str(results) if results else "No recent searches"
        except Exception as e:
            return f"Error: {e}"

    @mcp.resource("salesos://metrics/revenue")
    async def revenue_metrics() -> str:
        """Revenue metrics — booked, pipeline, forecast, growth."""
        try:
            result = await client.get_revenue_analytics()
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    @mcp.resource("salesos://workflows/active")
    async def active_workflows() -> str:
        """List of active automation workflows."""
        try:
            result = await client.list_workflows(status="active")
            return str(result) if result else "No active workflows"
        except Exception as e:
            return f"Error: {e}"
