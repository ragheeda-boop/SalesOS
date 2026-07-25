"""Copilot tools — callable tools the copilot agent can invoke.

Each tool wraps a domain service and returns structured results.
Tools are the bridge between the LLM agent and the SalesOS backend.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

TOOL_TIMEOUT_SECONDS = 1.0


@dataclass
class ToolResult:
    """Standardized tool execution result."""

    success: bool = True
    data: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    latency_ms: float = 0.0
    tool_name: str = ""
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseCopilotTool(ABC):
    """Abstract base for all copilot tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, params: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        ...

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._parameter_schema(),
        }

    @abstractmethod
    def _parameter_schema(self) -> dict[str, Any]:
        ...


class SearchCompaniesTool(BaseCopilotTool):
    """Search companies via the Search domain — returns structured results.

    Delegates to PostgresSearchRepository for full-text search with
    < 1s timeout. Returns company name, id, and relevance score.
    """

    def __init__(self, search_repo: Any | None = None):
        super().__init__(
            name="search_companies",
            description=(
                "Search for companies by name, industry, city, or keyword."
                " Returns matching companies with relevance scores."
            ),
        )
        self._search_repo = search_repo

    def _parameter_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text",
                },
                "city": {
                    "type": "string",
                    "description": "Filter by city",
                },
                "industry": {
                    "type": "string",
                    "description": "Filter by industry",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 10, max 20)",
                    "default": 10,
                },
            },
            "required": ["query"],
        }

    async def execute(self, params: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        t0 = time.monotonic()
        query_text = params.get("query", "")
        tenant_id = context.get("tenant_id", "")
        city = params.get("city")
        industry = params.get("industry")
        limit = min(params.get("limit", 10), 20)

        if not query_text:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="Query text is required",
                latency_ms=0,
            )

        if not self._search_repo:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="Search repository not configured",
                latency_ms=0,
            )

        try:
            from domains.search.contracts.models import SearchQuery

            filters: dict[str, str] = {}
            if city:
                filters["city"] = city
            if industry:
                filters["industry"] = industry

            search_query = SearchQuery(
                query=query_text,
                filters=filters,
                page_size=limit,
                tenant_id=tenant_id,
            )

            search_result = await asyncio.wait_for(
                self._search_repo.search(search_query),
                timeout=TOOL_TIMEOUT_SECONDS,
            )

            data = []
            for item in search_result.items:
                if isinstance(item, dict):
                    data.append({
                        "id": item.get("id", ""),
                        "name_ar": item.get("name_ar", ""),
                        "name_en": item.get("name_en", ""),
                        "cr_number": item.get("cr_number", ""),
                        "city": item.get("city", ""),
                        "industry": item.get("industry", ""),
                        "score": item.get("rank", 0.0),
                    })
                else:
                    data.append({
                        "id": str(getattr(item, "id", "")),
                        "name_ar": getattr(item, "name_ar", ""),
                        "name_en": getattr(item, "name_en", ""),
                        "cr_number": getattr(item, "cr_number", ""),
                        "city": getattr(item, "city", ""),
                        "industry": getattr(item, "industry", ""),
                        "score": getattr(item, "rank", 0.0),
                    })

            latency_ms = (time.monotonic() - t0) * 1000
            return ToolResult(
                success=True,
                data=data,
                total=search_result.total,
                latency_ms=latency_ms,
                tool_name=self.name,
                metadata={
                    "strategy": search_result.strategy,
                    "duration_ms": search_result.duration_ms,
                },
            )

        except TimeoutError:
            latency_ms = (time.monotonic() - t0) * 1000
            logger.warning("search_companies timeout after %.0fms", latency_ms)
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=f"Search timed out after {latency_ms:.0f}ms (target: <1000ms)",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.monotonic() - t0) * 1000
            logger.error("search_companies failed: %s", e)
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=str(e),
                latency_ms=latency_ms,
            )
