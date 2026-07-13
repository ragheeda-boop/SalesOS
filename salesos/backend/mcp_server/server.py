"""SalesOS MCP Server — AI agent interface for CRM, Pipeline, NBA, Search, and Insights.

Supports stdio transport (primary for AI agents like Claude Desktop, Cursor)
and SSE transport (for web integration with FastAPI).
"""

from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

from mcp_server.tools import register_tools, set_valid_api_keys
from mcp_server.resources import register_resources

logger = logging.getLogger(__name__)


def create_server(api_keys: list[str] | None = None) -> FastMCP:
    """Create and configure a new FastMCP server instance.

    Each call creates a fresh server with tools and resources registered.
    """
    keys = api_keys or [os.environ.get("MCP_API_KEY", "mcp-dev-key")]
    set_valid_api_keys(keys)

    mcp = FastMCP(
        "salesos",
        instructions="SalesOS AI Ecosystem — CRM, Pipeline, NBA, Search, Insights",
    )
    register_tools(mcp)
    register_resources(mcp, keys[0] if keys else "")
    return mcp


def run_stdio() -> None:
    """Run the MCP server over stdio transport (for AI agents)."""
    mcp = create_server()
    logger.info("SalesOS MCP server starting (stdio transport)")
    mcp.run(transport="stdio")


def run_sse(host: str = "0.0.0.0", port: int = 8001) -> None:
    """Run the MCP server over SSE transport (for web integration)."""
    mcp = create_server()
    logger.info(f"SalesOS MCP server starting (SSE transport) on {host}:{port}")
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if transport == "sse":
        run_sse()
    else:
        run_stdio()
