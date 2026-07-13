"""MCP SSE router — hosts the MCP server over Server-Sent Events transport."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

try:
    from mcp_server.server import create_server
    _mcp_available = True
except ImportError:
    _mcp_available = False
    create_server = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])

_mcp_server = None


def _get_mcp():
    if not _mcp_available:
        return None
    global _mcp_server
    if _mcp_server is None:
        keys = [os.environ.get("MCP_API_KEY", "mcp-dev-key")]
        _mcp_server = create_server(api_keys=keys)
    return _mcp_server


@router.get("/sse")
async def mcp_sse(request: Request):
    """SSE endpoint for MCP protocol — enables AI agents to connect via web."""
    mcp_server = _get_mcp()
    logger.info("MCP SSE connection established from %s", request.client.host if request.client else "unknown")

    async def event_stream():
        async with mcp_server.run_sse_async() as stream:
            async for event in stream:
                yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def mcp_health():
    """Health check for the MCP server."""
    return {"status": "ok", "server": "salesos-mcp"}
