"""AI Domain REST API — prompt registry, evaluation, and generation."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_tenant_id
from sdk.permissions import PermissionAction
from app.dependencies import require_permission_dep
from domains.ai import PromptRegistry, AIEvaluator, AIService, OpenAIProvider
from domains.ai.schemas import PromptCreate, EvaluateRequest, GenerateRequest, ActivateRequest

logger = logging.getLogger(__name__)

router = APIRouter()

_registry = PromptRegistry()
_evaluator = AIEvaluator(_registry)
_service = AIService(_registry, _evaluator)
_service.register_provider("openai", OpenAIProvider())


async def _get_registry() -> PromptRegistry:
    return _registry


async def _get_evaluator() -> AIEvaluator:
    return _evaluator


async def _get_service() -> AIService:
    return _service


@router.get("/ai/prompts")
async def list_prompts(
    domain: str | None = None,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.READ)),
):
    try:
        templates = _registry.list(domain=domain)
        return [
            {
                "id": t.id,
                "name": t.name,
                "version": t.version,
                "domain": t.domain,
                "active": t.active,
                "variables": t.variables,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
            }
            for t in templates
        ]
    except Exception as exc:
        logger.error("list_prompts failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/prompts", status_code=201)
async def create_prompt(
    body: PromptCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.CREATE)),
):
    try:
        from domains.ai.models import PromptTemplate
        template = PromptTemplate(
            id=body.id,
            name=body.name,
            version=body.version,
            template=body.template,
            variables=body.variables,
            output_schema=body.output_schema,
            domain=body.domain,
        )
        _registry.register(template)
        return {"id": template.id, "name": template.name, "version": template.version}
    except Exception as exc:
        logger.error("create_prompt failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/prompts/activate")
async def activate_prompt(
    body: ActivateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.UPDATE)),
):
    template = _registry.activate(body.id, body.version)
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return {"id": template.id, "name": template.name, "version": template.version, "active": True}


@router.post("/ai/evaluate")
async def evaluate(
    body: EvaluateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.CREATE)),
):
    try:
        result = _evaluator.evaluate(
            prompt_id=body.prompt_id,
            input=body.input,
            output=body.output,
            expected=body.expected,
            metrics=body.metrics,
        )
        return {
            "id": result.id,
            "prompt_id": result.prompt_id,
            "score": result.score,
            "metrics": [
                {"name": m.name, "value": m.value, "threshold": m.threshold, "passed": m.passed}
                for m in result.metrics
            ],
            "timestamp": result.timestamp.isoformat(),
        }
    except Exception as exc:
        logger.error("evaluate failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ai/metrics/{prompt_id}")
async def get_metrics(
    prompt_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.READ)),
):
    try:
        return _evaluator.get_metrics(prompt_id)
    except Exception as exc:
        logger.error("get_metrics failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ai/generate")
async def generate(
    body: GenerateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep("ai", PermissionAction.CREATE)),
):
    try:
        output = await _service.generate(
            prompt_template_id=body.prompt_template_id,
            variables=body.variables,
            provider=body.provider,
            model=body.model,
        )
        return {"prompt_template_id": body.prompt_template_id, "output": output}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("generate failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")
