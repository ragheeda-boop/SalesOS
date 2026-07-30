from __future__ import annotations

from typing import Any

from .service import AuditService


AI_ACTIONS = {
    "chat_completion": "ai:chat_completion",
    "embedding": "ai:embedding",
    "decision_evaluate": "ai:decision_evaluate",
    "decision_explain": "ai:decision_explain",
    "recommendation": "ai:recommendation",
    "scoring": "ai:scoring",
    "agent_call": "ai:agent_call",
    "tool_call": "ai:tool_call",
    "search": "ai:search",
}

AI_RESOURCE_TYPES = {
    "openai_chat": "ai:openai/chat",
    "openai_embedding": "ai:openai/embedding",
    "decision_engine": "ai:decision-engine",
    "copilot_agent": "ai:copilot/agent",
    "copilot_tool": "ai:copilot/tool",
    "recommendation_engine": "ai:recommendations",
    "scoring_engine": "ai:scoring",
}


class AIAuditService:
    def __init__(self, audit_service: AuditService):
        self._audit = audit_service

    async def log_ai_call(
        self,
        tenant_id: str,
        user_id: str | None,
        action: str,
        resource_type: str,
        model: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        cost: float | None = None,
        operation: str | None = None,
        entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> None:
        details: dict[str, Any] = {
            "ai_model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "operation": operation,
        }
        if metadata:
            details["metadata"] = metadata

        await self._audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_llm_call(
        self,
        tenant_id: str,
        user_id: str | None,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float,
        operation: str = "completion",
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> None:
        await self.log_ai_call(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AI_ACTIONS["chat_completion"],
            resource_type=AI_RESOURCE_TYPES["openai_chat"],
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            operation=operation,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_decision_call(
        self,
        tenant_id: str,
        user_id: str | None,
        action: str,
        entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        await self.log_ai_call(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=AI_RESOURCE_TYPES["decision_engine"],
            entity_id=entity_id,
            metadata=metadata,
            request_id=request_id,
        )

    async def log_agent_call(
        self,
        tenant_id: str,
        user_id: str | None,
        agent_name: str,
        tool_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        await self.log_ai_call(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AI_ACTIONS["agent_call"] if not tool_name else AI_ACTIONS["tool_call"],
            resource_type=AI_RESOURCE_TYPES["copilot_agent"] if not tool_name else AI_RESOURCE_TYPES["copilot_tool"],
            model=agent_name,
            operation=tool_name,
            metadata=metadata,
            request_id=request_id,
        )
